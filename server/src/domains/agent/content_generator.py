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
        parts = [f"당신은 '{persona.nickname}'입니다. {persona.personality}"]
        parts.append(f"글쓰기 스타일: {persona.writing_style}")

        if persona.archetype and persona.archetype in self._archetype_prompts:
            archetype_data = self._archetype_prompts[persona.archetype]
            archetype_prompt = archetype_data.get("prompt", "")
            if archetype_prompt:
                parts.append(f"행동 원형: {archetype_prompt}")
            if persona.archetype_detail:
                parts.append(f"구체적 역할: {persona.archetype_detail}")

        return "\n".join(parts)

    def _build_rag_context(self, persona: Persona) -> str:
        """RAG: retrieve relevant samples and format as source material."""
        samples = self._sample_provider.retrieve(persona.topics)
        if not samples:
            return ""
        return self._sample_provider.format_as_context(samples)

    def _build_persona_example(self, persona: Persona, mode: str) -> str:
        """Build persona-specific writing example section."""
        ex = persona.examples
        if mode == "post" and ex.post_title and ex.post_content:
            return (
                f"\n\n당신의 글쓰기 스타일 예시:\n"
                f"---\n"
                f"제목: {ex.post_title}\n"
                f"본문: {ex.post_content}\n"
                f"---"
            )
        elif mode == "comment" and ex.comment:
            return (
                f"\n\n당신의 댓글 스타일 예시:\n"
                f"---\n"
                f"{ex.comment}\n"
                f"---"
            )
        return ""

    async def generate_post(self, persona: Persona) -> dict[str, str]:
        system = self._build_system_prompt(persona)
        persona_ex = self._build_persona_example(persona, "post")
        rag_context = self._build_rag_context(persona)
        topics_str = ", ".join(persona.topics)
        max_title = self._content_defaults["title_max_length"]
        max_content = self._content_defaults["content_max_length"]
        prompt = (
            f"{system}{persona_ex}{rag_context}\n\n"
            f"[지시사항]\n"
            f"위 참고 자료를 바탕으로, 다음 주제 중 하나에 대해 당신만의 관점으로 짧은 SNS 게시글을 작성하세요: {topics_str}\n"
            f"- 반드시 한국어로 작성\n"
            f"- 제목 {max_title}자 이내, 본문 {max_content}자 이내\n"
            f"- 2~4문장으로 간결하게\n"
            f"- JSON 형식: {{\"title\": \"제목\", \"content\": \"본문\"}}\n"
            f"- JSON만 출력"
        )
        model = self._resolve_model(persona)
        return await self._generate(prompt, model)

    async def generate_comment(self, persona: Persona, post_title: str, post_content: str) -> str:
        system = self._build_system_prompt(persona)
        persona_ex = self._build_persona_example(persona, "comment")
        max_comment = self._content_defaults["comment_max_length"]
        prompt = (
            f"{system}{persona_ex}\n\n"
            f"[게시글]\n제목: {post_title}\n내용: {post_content}\n\n"
            f"[지시사항]\n"
            f"위 게시글에 대해 당신의 관점으로 짧은 댓글을 한국어로 작성하세요.\n"
            f"- 1~2문장, {max_comment}자 이내\n"
            f"- 댓글 텍스트만 출력"
        )
        model = self._resolve_model(persona)
        response = await self._call_ollama(prompt, model)
        return response.strip().strip('"')[:max_comment]

    async def _generate(self, prompt: str, model: str) -> dict[str, str]:
        raw = await self._call_ollama(prompt, model)
        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = json.loads(raw[start:end])
                # Enforce length limits
                parsed["title"] = parsed.get("title", "")[:self._content_defaults["title_max_length"]]
                parsed["content"] = parsed.get("content", "")[:self._content_defaults["content_max_length"]]
                return parsed
        except (json.JSONDecodeError, ValueError):
            logger.warning("Failed to parse JSON from LLM response (model=%s), using fallback", model)

        return {"title": "생각 한 조각", "content": raw[:self._content_defaults["content_max_length"]]}

    async def check_available_models(self) -> list[str]:
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

    def _get_token_limit(self, model: str) -> int:
        """Get model-specific token limit. Smaller models get fewer tokens."""
        limits = self._content_defaults.get("model_token_limits", {})
        return limits.get(model, self._content_defaults["max_tokens"])

    async def _call_ollama_with_model(self, prompt: str, model: str) -> str:
        token_limit = self._get_token_limit(model)
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{self._base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self._content_defaults["temperature"],
                        "num_predict": token_limit,
                    },
                },
            )
            response.raise_for_status()
            return response.json()["response"]
