import json
import logging

import httpx
import yaml
from pathlib import Path

from src.domains.agent.persona_loader import Persona

logger = logging.getLogger(__name__)

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

        return "\n".join(parts)

    async def generate_post(self, persona: Persona) -> dict[str, str]:
        system = self._build_system_prompt(persona)
        topics_str = ", ".join(persona.topics)
        prompt = (
            f"{system}\n\n"
            f"Write a short social media post about one of these topics: {topics_str}.\n"
            f"Respond in JSON format with 'title' and 'content' fields.\n"
            f"Title should be under {self._content_defaults['title_max_length']} characters.\n"
            f"Content should be under {self._content_defaults['content_max_length']} characters.\n"
            f"Only output valid JSON, nothing else."
        )
        model = self._resolve_model(persona)
        return await self._generate(prompt, model)

    async def generate_comment(self, persona: Persona, post_title: str, post_content: str) -> str:
        system = self._build_system_prompt(persona)
        prompt = (
            f"{system}\n\n"
            f"You're reading a post titled '{post_title}':\n{post_content}\n\n"
            f"Write a short comment responding to this post. "
            f"Keep it under {self._content_defaults['comment_max_length']} characters.\n"
            f"Only output the comment text, nothing else."
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

    async def _call_ollama(self, prompt: str, model: str) -> str:
        try:
            return await self._call_ollama_with_model(prompt, model)
        except httpx.HTTPStatusError as e:
            if model != self._default_model:
                logger.warning(
                    "Model '%s' failed (status %s), falling back to '%s'",
                    model, e.response.status_code, self._default_model,
                )
                return await self._call_ollama_with_model(prompt, self._default_model)
            raise

    async def _call_ollama_with_model(self, prompt: str, model: str) -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
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
