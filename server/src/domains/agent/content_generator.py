import json
import logging

import httpx
import yaml
from pathlib import Path

from src.domains.agent.persona_loader import Persona
from src.domains.agent.sample_provider import SampleProvider

logger = logging.getLogger(__name__)


class OllamaUnavailableError(Exception):
    """Raised when Ollama API is not reachable or model is not available."""

AI_DEFAULTS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "ai_defaults.yaml"


def _load_ai_defaults() -> dict:
    with open(AI_DEFAULTS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


class ContentGenerator:
    def __init__(self, base_url: str, default_model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model
        defaults = _load_ai_defaults()
        self._content_defaults = defaults["content_generation"]
        self._archetype_prompts = defaults.get("archetypes", {})
        self._sample_provider = SampleProvider()

    def _resolve_model(self, persona: Persona) -> str:
        return persona.model or self._default_model

    def _build_system_prompt(self, persona: Persona) -> str:
        parts = [f"You are {persona.nickname}. {persona.personality}"]
        parts.append(f"Writing style: {persona.writing_style}")

        if persona.archetype and persona.archetype in self._archetype_prompts:
            archetype_data = self._archetype_prompts[persona.archetype]
            archetype_prompt = archetype_data.get("prompt", "")
            if archetype_prompt:
                parts.append(f"Behavioral archetype: {archetype_prompt}")
            if persona.archetype_detail:
                parts.append(f"Archetype specification: {persona.archetype_detail}")

        return "\n".join(parts)

    def _build_fewshot_section(self, persona: Persona) -> str:
        """Build a few-shot example section from conversation samples."""
        sample = self._sample_provider.get_sample(persona.topics)
        if not sample:
            return ""

        example = self._sample_provider.format_as_example(sample)
        return (
            f"\n\n다음은 자연스러운 한국어 대화 톤 참고 예시입니다:\n"
            f"---\n{example}\n---\n"
            f"이와 비슷한 자연스러운 한국어 톤으로 작성하세요."
        )

    def _build_persona_example(self, persona: Persona, mode: str) -> str:
        """Build persona-specific writing example section."""
        ex = persona.examples
        if mode == "post" and ex.post_title and ex.post_content:
            return (
                f"\n\n다음은 당신의 글쓰기 스타일 예시입니다:\n"
                f"---\n"
                f"제목: {ex.post_title}\n"
                f"본문: {ex.post_content}\n"
                f"---\n"
                f"이 톤, 스타일, 성격을 그대로 유지하여 한국어로 작성하세요."
            )
        elif mode == "comment" and ex.comment:
            return (
                f"\n\n다음은 당신의 댓글 스타일 예시입니다:\n"
                f"---\n"
                f"{ex.comment}\n"
                f"---\n"
                f"이 톤, 스타일, 성격을 그대로 유지하여 한국어로 작성하세요."
            )
        return ""

    async def generate_post(self, persona: Persona) -> dict[str, str]:
        system = self._build_system_prompt(persona)
        fewshot = self._build_fewshot_section(persona)
        persona_ex = self._build_persona_example(persona, "post")
        topics_str = ", ".join(persona.topics)
        prompt = (
            f"{system}{persona_ex}{fewshot}\n\n"
            f"다음 주제 중 하나로 짧은 SNS 게시글을 한국어로 작성하세요: {topics_str}.\n"
            f"반드시 한국어로 작성하세요.\n"
            f"JSON 형식으로 'title'과 'content' 필드를 포함하여 응답하세요.\n"
            f"제목은 {self._content_defaults['title_max_length']}자 이내, "
            f"본문은 {self._content_defaults['content_max_length']}자 이내로 작성하세요.\n"
            f"유효한 JSON만 출력하고 다른 텍스트는 포함하지 마세요."
        )
        model = self._resolve_model(persona)
        return await self._generate(prompt, model)

    async def generate_comment(self, persona: Persona, post_title: str, post_content: str) -> str:
        system = self._build_system_prompt(persona)
        fewshot = self._build_fewshot_section(persona)
        persona_ex = self._build_persona_example(persona, "comment")
        prompt = (
            f"{system}{persona_ex}{fewshot}\n\n"
            f"다음 게시글을 읽고 있습니다. 제목: '{post_title}':\n{post_content}\n\n"
            f"이 게시글에 대한 짧은 댓글을 한국어로 작성하세요. "
            f"{self._content_defaults['comment_max_length']}자 이내로 작성하세요.\n"
            f"댓글 텍스트만 출력하고 다른 텍스트는 포함하지 마세요."
        )
        model = self._resolve_model(persona)
        response = await self._call_ollama(prompt, model)
        return response.strip().strip('"')

    async def _generate(self, prompt: str, model: str) -> dict[str, str]:
        raw = await self._call_ollama(prompt, model)
        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(raw[start:end])
        except (json.JSONDecodeError, ValueError):
            logger.warning("Failed to parse JSON from LLM response (model=%s), using fallback", model)

        return {"title": "Untitled Thought", "content": raw[:self._content_defaults["content_max_length"]]}

    async def check_available_models(self) -> list[str]:
        """Query Ollama for currently available models."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self._base_url}/api/tags")
                response.raise_for_status()
                data = response.json()
                return [m["name"].split(":")[0] for m in data.get("models", [])]
        except Exception:
            return []

    async def _call_ollama(self, prompt: str, model: str) -> str:
        try:
            return await self._call_ollama_with_model(prompt, model)
        except (httpx.HTTPStatusError, httpx.ConnectError, httpx.ReadTimeout) as e:
            if model != self._default_model:
                status = getattr(getattr(e, "response", None), "status_code", type(e).__name__)
                logger.warning("Model '%s' failed (%s), falling back to '%s'", model, status, self._default_model)
                try:
                    return await self._call_ollama_with_model(prompt, self._default_model)
                except (httpx.HTTPStatusError, httpx.ConnectError, httpx.ReadTimeout):
                    raise OllamaUnavailableError(f"Both '{model}' and fallback '{self._default_model}' failed")
            raise OllamaUnavailableError(f"Model '{model}' unavailable: {type(e).__name__}") from e

    async def _call_ollama_with_model(self, prompt: str, model: str) -> str:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self._content_defaults["temperature"],
                        "num_predict": self._content_defaults["max_tokens"],
                    },
                },
            )
            response.raise_for_status()
            return response.json()["response"]
