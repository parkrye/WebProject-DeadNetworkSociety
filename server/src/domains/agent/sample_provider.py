"""Provides few-shot conversation samples for content generation prompts."""
import json
import logging
import random
from pathlib import Path

logger = logging.getLogger(__name__)

SAMPLES_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "conversation_samples.json"

# Map persona topics to conversation sample topics
TOPIC_TO_SAMPLE_KEY: dict[str, list[str]] = {
    # Daily life
    "일상": ["daily", "general"],
    "daily life": ["daily", "general"],
    "random thoughts": ["daily", "general"],
    "digital culture": ["daily", "general"],
    "internet culture": ["daily", "general"],
    "human behavior": ["daily", "general"],
    # Relationships
    "relationships": ["relationships"],
    "연애": ["relationships"],
    "결혼": ["relationships"],
    "social media trends": ["relationships", "daily"],
    # Food
    "food": ["food"],
    "cooking": ["food"],
    "street food": ["food"],
    "음식": ["food"],
    # Health & Fitness
    "fitness": ["fitness", "health"],
    "health": ["health"],
    "운동": ["fitness"],
    "건강": ["health"],
    "yoga": ["fitness"],
    "meditation": ["fitness"],
    # Entertainment
    "gaming": ["gaming"],
    "retro gaming": ["gaming"],
    "게임": ["gaming"],
    "music": ["music"],
    "음악": ["music"],
    "movies": ["media", "culture"],
    "film": ["media", "culture"],
    "cinema": ["media", "culture"],
    "anime": ["media", "culture"],
    "manga": ["media", "culture"],
    # Culture
    "books": ["books"],
    "독서": ["books"],
    "literature": ["books"],
    "art": ["culture"],
    "fashion": ["culture", "beauty"],
    "beauty": ["beauty"],
    "뷰티": ["beauty"],
    # Travel & Nature
    "travel": ["travel"],
    "여행": ["travel"],
    "nature": ["nature"],
    "자연": ["nature"],
    # Sports
    "sports": ["sports"],
    "스포츠": ["sports"],
    # Tech & Science
    "technology": ["tech"],
    "programming": ["tech"],
    "software": ["tech"],
    "science": ["tech"],
    "data analysis": ["tech"],
    "crypto": ["finance", "tech"],
    "web3": ["finance", "tech"],
    # Work & Education
    "career": ["work", "self_improvement"],
    "직업": ["work"],
    "education": ["school", "self_improvement"],
    "학교": ["school"],
    # Finance
    "finance": ["finance"],
    "투자": ["finance"],
    "shopping": ["shopping"],
    "쇼핑": ["shopping"],
    # Pets
    "pets": ["pets"],
    "동물": ["pets"],
    "animals": ["pets"],
    "cats": ["pets"],
    # Misc
    "philosophy": ["daily", "general"],
    "existentialism": ["daily", "general"],
    "minimalism": ["daily", "general"],
    "humor": ["daily", "general"],
    "memes": ["daily", "general"],
    "paradoxes": ["daily", "general"],
    "chaos theory": ["daily", "general"],
}


class SampleProvider:
    def __init__(self, samples_path: Path | None = None) -> None:
        self._samples: dict[str, list[dict]] = {}
        self._loaded = False
        self._path = samples_path or SAMPLES_PATH

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        if not self._path.exists():
            logger.warning("Conversation samples not found: %s", self._path)
            self._loaded = True
            return
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                self._samples = json.load(f)
            total = sum(len(v) for v in self._samples.values())
            logger.info("Loaded %d conversation samples across %d topics", total, len(self._samples))
        except Exception:
            logger.exception("Failed to load conversation samples")
        self._loaded = True

    def get_sample(self, persona_topics: list[str]) -> dict | None:
        """Get a relevant conversation sample based on persona topics."""
        self._ensure_loaded()
        if not self._samples:
            return None

        # Find matching sample keys from persona topics
        candidate_keys: list[str] = []
        for topic in persona_topics:
            topic_lower = topic.lower()
            if topic_lower in TOPIC_TO_SAMPLE_KEY:
                candidate_keys.extend(TOPIC_TO_SAMPLE_KEY[topic_lower])

        # Deduplicate and filter to available keys
        available_keys = [k for k in set(candidate_keys) if k in self._samples]

        # Fallback to any available topic
        if not available_keys:
            available_keys = list(self._samples.keys())

        if not available_keys:
            return None

        key = random.choice(available_keys)
        samples = self._samples[key]
        return random.choice(samples) if samples else None

    def format_as_example(self, sample: dict) -> str:
        """Format a conversation sample as a prompt example."""
        lines = []
        topic = sample.get("single_topic", "")
        if topic:
            lines.append(f"[대화 주제: {topic}]")

        for utt in sample.get("utterances", [])[:8]:
            speaker = utt.get("speaker", "?")
            text = utt.get("text", "")
            lines.append(f"{speaker}: {text}")

        return "\n".join(lines)
