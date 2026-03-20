from src.domains.agent.action_selector import (
    ACTION_COMMENT,
    ACTION_CREATE_POST,
    ACTION_REACTION,
    select_action,
)


def test_select_action_with_custom_ratios() -> None:
    # given: ratios that heavily favor create_post
    ratios = {"create_post": 1.0, "comment": 0.0, "reaction": 0.0}

    # when: selecting an action many times
    actions = [select_action(ratios) for _ in range(100)]

    # then: always returns create_post
    assert all(a == ACTION_CREATE_POST for a in actions)


def test_select_action_with_default_ratios() -> None:
    # given: no custom ratios (uses defaults)

    # when: selecting an action
    action = select_action()

    # then: returns a valid action
    assert action in [ACTION_CREATE_POST, ACTION_COMMENT, ACTION_REACTION]


def test_select_action_distribution() -> None:
    # given: equal ratios
    ratios = {"create_post": 1.0, "comment": 1.0, "reaction": 1.0}

    # when: selecting many actions
    actions = [select_action(ratios) for _ in range(300)]

    # then: all action types appear (statistically near-certain with 300 samples)
    assert ACTION_CREATE_POST in actions
    assert ACTION_COMMENT in actions
    assert ACTION_REACTION in actions


def test_select_action_empty_ratios_uses_defaults() -> None:
    # given: empty ratios (falsy, so defaults are loaded)
    ratios: dict[str, float] = {}

    # when: selecting an action
    action = select_action(ratios)

    # then: returns a valid action from defaults
    assert action in [ACTION_CREATE_POST, ACTION_COMMENT, ACTION_REACTION]
