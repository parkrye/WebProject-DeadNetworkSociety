import logging
from dataclasses import dataclass, field
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

PERSONAS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data" / "personas"

MIN_ACTIVITY_LEVEL = 1
MAX_ACTIVITY_LEVEL = 10
DEFAULT_ACTIVITY_LEVEL = 5
DEFAULT_RECENT_SCOPE = 10

VALID_ARCHETYPES = frozenset({
    "expert", "concepter", "provocateur", "storyteller",
    "critic", "cheerleader", "observer", "wildcard",
})


@dataclass(frozen=True)
class Persona:
    name: str
    nickname: str
    personality: str
    writing_style: str
    topics: list[str]
    archetype: str = ""
    model: str = ""
    activity_level: int = DEFAULT_ACTIVITY_LEVEL
    recent_scope: int = DEFAULT_RECENT_SCOPE


def load_persona(file_path: Path) -> Persona:
    with open(file_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    activity_level = data.get("activity_level", DEFAULT_ACTIVITY_LEVEL)
    activity_level = max(MIN_ACTIVITY_LEVEL, min(MAX_ACTIVITY_LEVEL, activity_level))

    archetype = data.get("archetype", "")
    if archetype and archetype not in VALID_ARCHETYPES:
        logger.warning("Unknown archetype '%s' in %s", archetype, file_path)

    return Persona(
        name=data["name"],
        nickname=data["nickname"],
        personality=data["personality"],
        writing_style=data["writing_style"],
        topics=data["topics"],
        archetype=archetype,
        model=data.get("model", ""),
        activity_level=activity_level,
        recent_scope=data.get("recent_scope", DEFAULT_RECENT_SCOPE),
    )


def load_all_personas(directory: Path | None = None) -> list[Persona]:
    target_dir = directory or PERSONAS_DIR
    personas: list[Persona] = []

    if not target_dir.exists():
        logger.warning("Personas directory not found: %s", target_dir)
        return personas

    for file_path in sorted(target_dir.rglob("*.yaml")):
        try:
            personas.append(load_persona(file_path))
        except Exception:
            logger.exception("Failed to load persona from %s", file_path)

    return personas


def load_personas_by_model(directory: Path | None = None) -> dict[str, list[Persona]]:
    personas = load_all_personas(directory)
    grouped: dict[str, list[Persona]] = {}
    for persona in personas:
        model = persona.model
        if model not in grouped:
            grouped[model] = []
        grouped[model].append(persona)
    return grouped
