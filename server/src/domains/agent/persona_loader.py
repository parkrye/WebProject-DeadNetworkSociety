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
DEFAULT_IMPERFECTION_LEVEL = 3
DEFAULT_LENGTH_RANGE_MIN = 2
DEFAULT_LENGTH_RANGE_MAX = 4

VALID_ARCHETYPES = frozenset({
    "expert", "concepter", "provocateur", "storyteller",
    "critic", "cheerleader", "observer", "wildcard",
})


@dataclass(frozen=True)
class PersonaExamples:
    post_title: str = ""
    post_content: str = ""
    comment: str = ""


@dataclass(frozen=True)
class PersonaPreferences:
    likes: list[str] = field(default_factory=list)
    dislikes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Persona:
    name: str
    nickname: str
    writing_style: str
    topics: list[str]
    personality: str = ""
    archetype: str = ""
    archetype_detail: str = ""
    model: str = ""
    activity_level: int = DEFAULT_ACTIVITY_LEVEL
    recent_scope: int = DEFAULT_RECENT_SCOPE
    imperfection_level: int = DEFAULT_IMPERFECTION_LEVEL
    length_range: tuple[int, int] = (DEFAULT_LENGTH_RANGE_MIN, DEFAULT_LENGTH_RANGE_MAX)
    examples: PersonaExamples = field(default_factory=PersonaExamples)
    preferences: PersonaPreferences = field(default_factory=PersonaPreferences)


def load_persona(file_path: Path) -> Persona:
    with open(file_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    activity_level = data.get("activity_level", DEFAULT_ACTIVITY_LEVEL)
    activity_level = max(MIN_ACTIVITY_LEVEL, min(MAX_ACTIVITY_LEVEL, activity_level))

    archetype = data.get("archetype", "")
    if archetype and archetype not in VALID_ARCHETYPES:
        logger.warning("Unknown archetype '%s' in %s", archetype, file_path)

    examples_data = data.get("examples", {})
    examples = PersonaExamples(
        post_title=examples_data.get("post_title", ""),
        post_content=examples_data.get("post_content", ""),
        comment=examples_data.get("comment", ""),
    )

    prefs_data = data.get("preferences", {})
    preferences = PersonaPreferences(
        likes=prefs_data.get("likes", []),
        dislikes=prefs_data.get("dislikes", []),
    )

    imperfection_level = data.get("imperfection_level", DEFAULT_IMPERFECTION_LEVEL)
    imperfection_level = max(0, min(10, imperfection_level))

    length_raw = data.get("length_range", [DEFAULT_LENGTH_RANGE_MIN, DEFAULT_LENGTH_RANGE_MAX])
    length_range = (
        max(1, int(length_raw[0])) if len(length_raw) > 0 else DEFAULT_LENGTH_RANGE_MIN,
        max(1, int(length_raw[1])) if len(length_raw) > 1 else DEFAULT_LENGTH_RANGE_MAX,
    )

    return Persona(
        name=data["name"],
        nickname=data["nickname"],
        personality=data.get("personality", ""),
        writing_style=data["writing_style"],
        topics=data["topics"],
        archetype=archetype,
        archetype_detail=data.get("archetype_detail", ""),
        model=data.get("model", ""),
        activity_level=activity_level,
        recent_scope=data.get("recent_scope", DEFAULT_RECENT_SCOPE),
        imperfection_level=imperfection_level,
        length_range=length_range,
        examples=examples,
        preferences=preferences,
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
