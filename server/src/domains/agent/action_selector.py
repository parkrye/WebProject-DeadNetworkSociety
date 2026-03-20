import random

import yaml
from pathlib import Path

AI_DEFAULTS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "ai_defaults.yaml"

ACTION_CREATE_POST = "create_post"
ACTION_COMMENT = "comment"
ACTION_REACTION = "reaction"

ALL_ACTIONS = [ACTION_CREATE_POST, ACTION_COMMENT, ACTION_REACTION]


def _load_default_ratios() -> dict[str, float]:
    with open(AI_DEFAULTS_PATH, encoding="utf-8") as f:
        defaults = yaml.safe_load(f)
    return defaults["activity_ratios"]


def select_action(activity_ratios: dict[str, float] | None = None) -> str:
    ratios = activity_ratios or _load_default_ratios()

    actions = []
    weights = []
    for action in ALL_ACTIONS:
        if action in ratios and ratios[action] > 0:
            actions.append(action)
            weights.append(ratios[action])

    if not actions:
        return ACTION_CREATE_POST

    return random.choices(actions, weights=weights, k=1)[0]
