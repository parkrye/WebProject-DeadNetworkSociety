import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

PERSONAS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "personas"


@dataclass(frozen=True)
class Persona:
    name: str
    nickname: str
    personality: str
    writing_style: str
    topics: list[str]
    model: str = ""
    activity_ratios: dict[str, float] = field(default_factory=dict)


def load_persona(file_path: Path) -> Persona:
    with open(file_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return Persona(
        name=data["name"],
        nickname=data["nickname"],
        personality=data["personality"],
        writing_style=data["writing_style"],
        topics=data["topics"],
        model=data.get("model", ""),
        activity_ratios=data.get("activity_ratios", {}),
    )


def load_all_personas(directory: Path | None = None) -> list[Persona]:
    target_dir = directory or PERSONAS_DIR
    personas: list[Persona] = []

    if not target_dir.exists():
        logger.warning("Personas directory not found: %s", target_dir)
        return personas

    for file_path in sorted(target_dir.glob("*.yaml")):
        try:
            personas.append(load_persona(file_path))
        except Exception:
            logger.exception("Failed to load persona from %s", file_path)

    return personas
