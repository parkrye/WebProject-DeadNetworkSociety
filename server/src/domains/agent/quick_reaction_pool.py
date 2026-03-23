"""Loads and serves quick reactions by archetype. No LLM call needed."""
import logging
import random
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

REACTIONS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "quick_reactions.yaml"

SENTIMENT_POSITIVE = "positive"
SENTIMENT_NEGATIVE = "negative"
SENTIMENT_NEUTRAL = "neutral"
ALL_SENTIMENTS = [SENTIMENT_POSITIVE, SENTIMENT_NEGATIVE, SENTIMENT_NEUTRAL]
SENTIMENT_WEIGHTS = [40, 20, 40]


class QuickReactionPool:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or REACTIONS_PATH
        self._data: dict[str, dict[str, list[str]]] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        try:
            with open(self._path, encoding="utf-8") as f:
                self._data = yaml.safe_load(f) or {}
            logger.info("Loaded quick reactions for %d archetypes", len(self._data))
        except Exception:
            logger.exception("Failed to load quick reactions")
        self._loaded = True

    def pick(self, archetype: str) -> str:
        """Pick a random reaction for the given archetype."""
        self._ensure_loaded()
        pool = self._data.get(archetype, self._data.get("wildcard", {}))
        if not pool:
            return "ㅇㅇ"

        sentiment = random.choices(ALL_SENTIMENTS, weights=SENTIMENT_WEIGHTS, k=1)[0]
        reactions = pool.get(sentiment, [])
        if not reactions:
            # Fallback to any available sentiment
            for s in ALL_SENTIMENTS:
                reactions = pool.get(s, [])
                if reactions:
                    break

        return random.choice(reactions) if reactions else "ㅇㅇ"
