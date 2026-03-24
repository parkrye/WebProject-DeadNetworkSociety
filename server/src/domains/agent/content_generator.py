import json
import logging
import random
import re

import httpx
import yaml
from pathlib import Path

from src.domains.agent.persona_loader import Persona
from src.domains.agent.sample_provider import SampleProvider
from src.domains.agent.text_humanizer import humanize

logger = logging.getLogger(__name__)

# Patterns that indicate garbage LLM output
_JSON_ARTIFACT_RE = re.compile(r'[{}\[\]":,]')
_KOREAN_CHAR_RE = re.compile(r'[가-힣ㄱ-ㅎㅏ-ㅣ]')
_MIN_CONTENT_LENGTH = 4


class ContentQualityError(Exception):
    """Raised when generated content fails quality checks."""


class OllamaUnavailableError(Exception):
    """Raised when Ollama API is not reachable or model is not available."""

AI_DEFAULTS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "ai_defaults.yaml"
PROMPT_TEMPLATES_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "prompt_templates.yaml"


def _load_ai_defaults() -> dict:
    with open(AI_DEFAULTS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _load_prompt_templates() -> dict:
    with open(PROMPT_TEMPLATES_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


class ContentGenerator:
    def __init__(self, base_url: str, default_model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model
        defaults = _load_ai_defaults()
        self._content_defaults = defaults["content_generation"]
        self._archetype_prompts = defaults.get("archetypes", {})
        self._sample_provider = SampleProvider()

        templates_data = _load_prompt_templates()
        self._templates = templates_data["templates"]
        self._model_tiers = templates_data["model_tiers"]

    def _resolve_model(self, persona: Persona) -> str:
        return persona.model or self._default_model

    def _get_model_tier(self, model: str) -> str:
        for tier, tier_data in self._model_tiers.items():
            if model in tier_data["models"]:
                return tier
        return "medium"

    def _get_archetype_prompt(self, persona: Persona) -> str:
        if persona.archetype and persona.archetype in self._archetype_prompts:
            return self._archetype_prompts[persona.archetype].get("prompt", "")
        return ""

    def _build_rag_context(
        self, persona: Persona, popular_context: str = "",
    ) -> tuple[str, list[str]]:
        """Build RAG context and return (context_text, topic_list)."""
        samples = self._sample_provider.retrieve(persona.topics)
        topics = [s.get("single_topic", "") for s in samples]
        parts = []
        if samples:
            parts.append(self._sample_provider.format_as_context(samples))
        if popular_context:
            parts.append(popular_context)
        return "\n".join(parts), topics

    def _build_persona_example(self, persona: Persona, mode: str) -> str:
        ex = persona.examples
        if mode == "post" and ex.post_title and ex.post_content:
            return (
                f"\n당신의 글쓰기 스타일 예시:\n"
                f"---\n"
                f"제목: {ex.post_title}\n"
                f"본문: {ex.post_content}\n"
                f"---"
            )
        elif mode == "comment" and ex.comment:
            return (
                f"\n당신의 댓글 스타일 예시:\n"
                f"---\n"
                f"{ex.comment}\n"
                f"---"
            )
        return ""

    def _build_length_instruction(self, persona: Persona) -> str:
        min_len, max_len = persona.length_range
        sentence_count = random.randint(min_len, max_len)
        return f"{sentence_count}문장"

    def _render_template(
        self, tier: str, mode: str, persona: Persona, **kwargs: str
    ) -> str:
        template = self._templates[tier][mode]
        archetype_prompt = self._get_archetype_prompt(persona)
        archetype_detail = f"구체적 역할: {persona.archetype_detail}" if persona.archetype_detail else ""

        return template.format(
            nickname=persona.nickname,
            writing_style=persona.writing_style.strip(),
            archetype_prompt=archetype_prompt.strip(),
            archetype_detail=archetype_detail,
            persona_example=kwargs.get("persona_example", ""),
            rag_context=kwargs.get("rag_context", ""),
            topics=", ".join(persona.topics),
            max_title=self._content_defaults["title_max_length"],
            max_content=self._content_defaults["content_max_length"],
            max_comment=self._content_defaults["comment_max_length"],
            author_info=kwargs.get("author_info", ""),
            post_title=kwargs.get("post_title", ""),
            post_content=kwargs.get("post_content", ""),
            post_author=kwargs.get("post_author", ""),
            comment_content=kwargs.get("comment_content", ""),
            comment_author=kwargs.get("comment_author", ""),
            relationship_hint=kwargs.get("relationship_hint", ""),
            mention_target=kwargs.get("mention_target", ""),
            mention_context=kwargs.get("mention_context", ""),
            prev_title=kwargs.get("prev_title", ""),
            prev_content=kwargs.get("prev_content", ""),
        )

    async def generate_post(
        self, persona: Persona, popular_context: str = "",
    ) -> dict[str, str]:
        model = self._resolve_model(persona)
        tier = self._get_model_tier(model)
        persona_ex = self._build_persona_example(persona, "post")
        rag_context, rag_topics = self._build_rag_context(persona, popular_context)

        prompt = self._render_template(
            tier, "post", persona,
            persona_example=persona_ex,
            rag_context=rag_context,
        )
        result = await self._generate(prompt, model)

        result["title"] = humanize(result["title"], persona.imperfection_level)
        result["content"] = humanize(result["content"], persona.imperfection_level)
        result["_model"] = model
        result["_tier"] = tier
        result["_rag_topics"] = rag_topics
        return result

    async def generate_mention_post(
        self, persona: Persona, mention_target: str, mention_context: str,
    ) -> dict[str, str]:
        """Generate a post targeting a specific persona based on relationship."""
        model = self._resolve_model(persona)
        tier = self._get_model_tier(model)
        prompt = self._render_template(
            tier, "mention_post", persona,
            mention_target=mention_target,
            mention_context=mention_context,
        )
        result = await self._generate(prompt, model)
        result["title"] = humanize(result["title"], persona.imperfection_level)
        result["content"] = humanize(result["content"], persona.imperfection_level)
        result["_model"] = model
        result["_tier"] = tier
        result["_rag_topics"] = []
        return result

    async def generate_followup_post(
        self, persona: Persona, prev_title: str, prev_content: str,
        popular_context: str = "",
    ) -> dict[str, str]:
        """Generate a follow-up post continuing from a previous post."""
        model = self._resolve_model(persona)
        tier = self._get_model_tier(model)
        prompt = self._render_template(
            tier, "followup_post", persona,
            prev_title=prev_title,
            prev_content=prev_content,
            rag_context=popular_context,
        )
        result = await self._generate(prompt, model)
        result["title"] = humanize(result["title"], persona.imperfection_level)
        result["content"] = humanize(result["content"], persona.imperfection_level)
        result["_model"] = model
        result["_tier"] = tier
        result["_rag_topics"] = []
        return result

    async def generate_comment(
        self, persona: Persona, post_title: str, post_content: str,
        post_author: str = "", relationship_hint: str = "",
    ) -> str:
        model = self._resolve_model(persona)
        tier = self._get_model_tier(model)
        persona_ex = self._build_persona_example(persona, "comment")
        author_info = f"\n작성자: {post_author}" if post_author else ""
        max_comment = self._content_defaults["comment_max_length"]

        prompt = self._render_template(
            tier, "comment", persona,
            persona_example=persona_ex,
            author_info=author_info,
            post_title=post_title,
            post_content=post_content,
            relationship_hint=relationship_hint,
        )
        response = await self._call_ollama(prompt, model)
        raw = self._clean_comment(response, max_comment)
        if not self._validate_text(raw):
            raise ContentQualityError(f"Comment quality check failed (model={model})")
        return humanize(raw, persona.imperfection_level)

    async def generate_reply(
        self, persona: Persona, post_title: str, post_content: str,
        post_author: str, comment_content: str, comment_author: str,
        relationship_hint: str = "",
    ) -> str:
        model = self._resolve_model(persona)
        tier = self._get_model_tier(model)
        persona_ex = self._build_persona_example(persona, "comment")
        max_comment = self._content_defaults["comment_max_length"]

        prompt = self._render_template(
            tier, "reply", persona,
            persona_example=persona_ex,
            post_title=post_title,
            post_content=post_content,
            post_author=post_author,
            comment_content=comment_content,
            comment_author=comment_author,
            relationship_hint=relationship_hint,
        )
        response = await self._call_ollama(prompt, model)
        raw = self._clean_comment(response, max_comment)
        if not self._validate_text(raw):
            raise ContentQualityError(f"Reply quality check failed (model={model})")
        return humanize(raw, persona.imperfection_level)

    @staticmethod
    def _clean_comment(response: str, max_length: int) -> str:
        """Strip quotes, JSON wrapper, and truncate comment text."""
        text = response.strip().strip('"')
        # Some models wrap comments in JSON; extract plain text
        if text.startswith("{"):
            try:
                parsed = json.loads(text)
                text = parsed.get("comment", parsed.get("content", text))
            except (json.JSONDecodeError, ValueError):
                pass
        return text.strip()[:max_length]

    def _validate_text(self, text: str) -> bool:
        """Check if text is valid Korean content, not garbage."""
        if len(text.strip()) < _MIN_CONTENT_LENGTH:
            return False
        korean_chars = len(_KOREAN_CHAR_RE.findall(text))
        total_chars = len(text.strip())
        if total_chars > 0 and korean_chars / total_chars < 0.3:
            return False
        json_artifacts = len(_JSON_ARTIFACT_RE.findall(text))
        if json_artifacts > 3:
            return False
        return True

    async def _generate(self, prompt: str, model: str) -> dict[str, str]:
        raw = await self._call_ollama(prompt, model)
        title_limit = self._content_defaults["title_max_length"]
        content_limit = self._content_defaults["content_max_length"]

        try:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = json.loads(raw[start:end])
                title = parsed.get("title", "").strip()[:title_limit]
                content = parsed.get("content", "").strip()[:content_limit]

                if self._validate_text(title) and self._validate_text(content):
                    return {"title": title, "content": content}

                logger.warning(
                    "Content quality check failed (model=%s): title=%r, content=%r",
                    model, title[:30], content[:30],
                )
        except (json.JSONDecodeError, ValueError):
            logger.warning("Failed to parse JSON from LLM response (model=%s)", model)

        raise ContentQualityError(f"Model '{model}' produced unusable output")

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
