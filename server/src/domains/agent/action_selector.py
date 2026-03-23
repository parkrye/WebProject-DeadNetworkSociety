import random
from dataclasses import dataclass

from src.domains.agent.persona_loader import Persona

ACTION_CREATE_POST = "create_post"
ACTION_COMMENT = "comment"
ACTION_REPLY = "reply"
ACTION_QUICK_REACT = "quick_react"

ALL_ACTIONS = [ACTION_COMMENT, ACTION_REPLY, ACTION_CREATE_POST, ACTION_QUICK_REACT]
DEFAULT_ACTION_WEIGHTS = [35, 20, 15, 30]

# Archetype-specific default weights: [comment, reply, create_post, quick_react]
ARCHETYPE_DEFAULT_WEIGHTS: dict[str, list[int]] = {
    "expert":       [30, 15, 35, 20],
    "concepter":    [20, 15, 45, 20],
    "provocateur":  [35, 25, 15, 25],
    "storyteller":  [20, 10, 50, 20],
    "critic":       [40, 20, 20, 20],
    "cheerleader":  [25, 20, 10, 45],
    "observer":     [15, 5,  5,  75],
    "wildcard":     [30, 20, 20, 30],
}


@dataclass
class AgentAction:
    persona: Persona
    action_type: str


def _get_weights(persona: Persona) -> list[int]:
    """Resolve action weights for a persona: YAML override > archetype default > global default."""
    if persona.action_weights:
        return [
            persona.action_weights.get("comment", 35),
            persona.action_weights.get("reply", 20),
            persona.action_weights.get("create_post", 15),
            persona.action_weights.get("quick_react", 30),
        ]
    if persona.archetype in ARCHETYPE_DEFAULT_WEIGHTS:
        return ARCHETYPE_DEFAULT_WEIGHTS[persona.archetype]
    return DEFAULT_ACTION_WEIGHTS


def generate_action_set(personas: list[Persona]) -> list[AgentAction]:
    """Generate a shuffled set of actions for all personas based on their activity_level."""
    actions: list[AgentAction] = []

    for persona in personas:
        weights = _get_weights(persona)
        for _ in range(persona.activity_level):
            action_type = random.choices(ALL_ACTIONS, weights=weights, k=1)[0]
            actions.append(AgentAction(persona=persona, action_type=action_type))

    random.shuffle(actions)
    return actions
