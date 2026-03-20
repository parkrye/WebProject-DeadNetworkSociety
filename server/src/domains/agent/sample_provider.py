"""RAG-style provider: retrieves relevant conversation samples for content generation."""
import json
import logging
import random
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
SAMPLES_PATH = DATA_DIR / "conversation_samples.json"
COMMUNITY_PATH = DATA_DIR / "community_content.json"

RAG_RETRIEVE_COUNT = 3

# Map persona topics to conversation sample topics
TOPIC_TO_SAMPLE_KEY: dict[str, list[str]] = {
    "일상": ["daily", "general"],
    "daily life": ["daily", "general"],
    "random thoughts": ["daily", "general"],
    "digital culture": ["daily", "general"],
    "internet culture": ["daily", "general"],
    "human behavior": ["daily", "general"],
    "relationships": ["relationships"],
    "연애": ["relationships"],
    "결혼": ["relationships"],
    "social media trends": ["relationships", "daily"],
    "food": ["food"],
    "cooking": ["food"],
    "street food": ["food"],
    "음식": ["food"],
    "fitness": ["fitness", "health"],
    "health": ["health"],
    "운동": ["fitness"],
    "건강": ["health"],
    "yoga": ["fitness"],
    "meditation": ["fitness"],
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
    "books": ["books"],
    "독서": ["books"],
    "literature": ["books"],
    "art": ["culture"],
    "fashion": ["culture", "beauty"],
    "beauty": ["beauty"],
    "뷰티": ["beauty"],
    "travel": ["travel"],
    "여행": ["travel"],
    "nature": ["nature"],
    "자연": ["nature"],
    "sports": ["sports"],
    "스포츠": ["sports"],
    "technology": ["tech"],
    "programming": ["tech"],
    "software": ["tech"],
    "science": ["tech"],
    "data analysis": ["tech"],
    "crypto": ["finance", "tech"],
    "web3": ["finance", "tech"],
    "career": ["work", "self_improvement"],
    "직업": ["work"],
    "education": ["school", "self_improvement"],
    "학교": ["school"],
    "finance": ["finance"],
    "투자": ["finance"],
    "shopping": ["shopping"],
    "쇼핑": ["shopping"],
    "pets": ["pets"],
    "동물": ["pets"],
    "animals": ["pets"],
    "cats": ["pets"],
    "philosophy": ["daily", "general"],
    "existentialism": ["daily", "general"],
    "minimalism": ["daily", "general"],
    "humor": ["daily", "general"],
    "memes": ["daily", "general"],
    "paradoxes": ["daily", "general"],
    "chaos theory": ["daily", "general"],
}


class SampleProvider:
    def __init__(self, samples_path: Path | None = None, community_path: Path | None = None) -> None:
        self._samples: dict[str, list[dict]] = {}
        self._community: dict[str, list[dict]] = {}
        self._loaded = False
        self._path = samples_path or SAMPLES_PATH
        self._community_path = community_path or COMMUNITY_PATH

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return

        # Load conversation samples
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    self._samples = json.load(f)
                total = sum(len(v) for v in self._samples.values())
                logger.info("Loaded %d conversation samples across %d topics", total, len(self._samples))
            except Exception:
                logger.exception("Failed to load conversation samples")

        # Load community content
        if self._community_path.exists():
            try:
                with open(self._community_path, "r", encoding="utf-8") as f:
                    self._community = json.load(f)
                total = sum(len(v) for v in self._community.values())
                logger.info("Loaded %d community posts across %d topics", total, len(self._community))
            except Exception:
                logger.exception("Failed to load community content")

        self._loaded = True

    def retrieve(self, persona_topics: list[str], count: int = RAG_RETRIEVE_COUNT) -> list[dict]:
        """RAG retrieval: get relevant samples from conversations + community content."""
        self._ensure_loaded()

        candidate_keys: list[str] = []
        for topic in persona_topics:
            topic_lower = topic.lower()
            if topic_lower in TOPIC_TO_SAMPLE_KEY:
                candidate_keys.extend(TOPIC_TO_SAMPLE_KEY[topic_lower])
            # Also use Korean topic names directly for community content
            candidate_keys.append(topic_lower)

        # Collect from conversation samples
        conv_keys = [k for k in set(candidate_keys) if k in self._samples]
        if not conv_keys and self._samples:
            conv_keys = list(self._samples.keys())

        candidates: list[dict] = []
        for key in conv_keys:
            candidates.extend(self._samples.get(key, []))

        # Collect from community content (Korean topic keys)
        korean_topic_map = {
            "일상": ["일상", "인기"],
            "유머": ["유머"],
            "게임": ["게임"],
            "음악": ["음악"],
            "영화": ["영화"],
            "여행": ["여행"],
            "요리": ["요리"],
            "스포츠": ["스포츠"],
            "동물": ["동물"],
            "쇼핑": ["쇼핑"],
            "뉴스": ["뉴스"],
            "한국": ["한국"],
            "드라마": ["드라마"],
            "언어": ["언어"],
        }
        community_keys: set[str] = set()
        for topic in persona_topics:
            topic_lower = topic.lower()
            for kr_key, kr_topics in korean_topic_map.items():
                if kr_key in topic_lower or topic_lower in kr_key:
                    community_keys.update(kr_topics)
        if not community_keys and self._community:
            community_keys = set(self._community.keys())

        for key in community_keys:
            for item in self._community.get(key, []):
                candidates.append({
                    "single_topic": key,
                    "utterances": [{"text": item.get("title", "")}, {"text": item.get("content", "")}],
                    "_source": item.get("source", "community"),
                })

        if not candidates:
            return []

        return random.sample(candidates, min(count, len(candidates)))

    def get_sample(self, persona_topics: list[str]) -> dict | None:
        """Get a single relevant sample (backwards compat)."""
        results = self.retrieve(persona_topics, count=1)
        return results[0] if results else None

    def format_as_context(self, samples: list[dict]) -> str:
        """Format multiple samples as RAG context for the prompt."""
        if not samples:
            return ""

        blocks = []
        for i, sample in enumerate(samples, 1):
            lines = []
            topic = sample.get("single_topic", "")
            if topic:
                lines.append(f"[주제: {topic}]")
            for utt in sample.get("utterances", [])[:6]:
                text = utt.get("text", "")
                lines.append(text)
            blocks.append("\n".join(lines))

        context = "\n---\n".join(blocks)
        return (
            f"\n\n다음은 참고할 실제 한국어 대화/콘텐츠입니다:\n"
            f"===\n{context}\n===\n"
            f"위 내용에서 영감을 받아, 당신만의 관점과 스타일로 재해석하여 작성하세요. "
            f"원문을 그대로 복사하지 마세요."
        )

    def format_as_example(self, sample: dict) -> str:
        """Format a single sample (backwards compat)."""
        lines = []
        topic = sample.get("single_topic", "")
        if topic:
            lines.append(f"[대화 주제: {topic}]")
        for utt in sample.get("utterances", [])[:8]:
            speaker = utt.get("speaker", "?")
            text = utt.get("text", "")
            lines.append(f"{speaker}: {text}")
        return "\n".join(lines)
