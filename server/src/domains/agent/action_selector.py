import random
from dataclasses import dataclass

from src.domains.agent.persona_loader import Persona

ACTION_CREATE_POST = "create_post"
ACTION_COMMENT = "comment"
ACTION_REPLY = "reply"
ACTION_LIKE = "like"
ACTION_DISLIKE = "dislike"

ALL_ACTIONS = [ACTION_CREATE_POST, ACTION_COMMENT, ACTION_REPLY, ACTION_LIKE, ACTION_DISLIKE]


@dataclass
class AgentAction:
    persona: Persona
    action_type: str


def generate_action_set(personas: list[Persona]) -> list[AgentAction]:
    """Generate a shuffled set of actions for all personas based on their activity_level."""
    actions: list[AgentAction] = []

    for persona in personas:
        for _ in range(persona.activity_level):
            action_type = random.choice(ALL_ACTIONS)
            actions.append(AgentAction(persona=persona, action_type=action_type))

    random.shuffle(actions)
    return actions
