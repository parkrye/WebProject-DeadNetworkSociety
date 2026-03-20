from src.domains.agent.action_selector import (
    ACTION_COMMENT,
    ACTION_CREATE_POST,
    ACTION_DISLIKE,
    ACTION_LIKE,
    ACTION_REPLY,
    ALL_ACTIONS,
    AgentAction,
    generate_action_set,
)
from src.domains.agent.persona_loader import Persona


def _make_persona(name: str = "test", activity_level: int = 5) -> Persona:
    return Persona(
        name=name, nickname=name.title(), personality="test",
        writing_style="test", topics=["test"], model="llama3",
        activity_level=activity_level, recent_scope=10,
    )


def test_generate_action_set_count() -> None:
    # given: personas with known activity levels
    personas = [_make_persona("a", 3), _make_persona("b", 5)]

    # when: generating a set
    action_set = generate_action_set(personas)

    # then: total actions = sum of activity levels
    assert len(action_set) == 8  # 3 + 5


def test_generate_action_set_all_action_types_present() -> None:
    # given: a persona with high activity level
    personas = [_make_persona("active", 10)]

    # when: generating many sets
    all_types: set[str] = set()
    for _ in range(50):
        action_set = generate_action_set(personas)
        for action in action_set:
            all_types.add(action.action_type)

    # then: all action types appear eventually
    assert all_types == set(ALL_ACTIONS)


def test_generate_action_set_is_shuffled() -> None:
    # given: two personas
    personas = [_make_persona("a", 5), _make_persona("b", 5)]

    # when: generating multiple sets
    orderings = set()
    for _ in range(20):
        action_set = generate_action_set(personas)
        ordering = tuple((a.persona.name, a.action_type) for a in action_set)
        orderings.add(ordering)

    # then: different orderings appear (shuffled)
    assert len(orderings) > 1


def test_generate_action_set_preserves_persona() -> None:
    # given: a persona
    persona = _make_persona("solo", 3)

    # when: generating a set
    action_set = generate_action_set([persona])

    # then: all actions belong to the persona
    for action in action_set:
        assert action.persona.name == "solo"


def test_generate_action_set_single_activity() -> None:
    # given: a persona with minimum activity
    persona = _make_persona("quiet", 1)

    # when: generating a set
    action_set = generate_action_set([persona])

    # then: exactly 1 action
    assert len(action_set) == 1
    assert action_set[0].action_type in ALL_ACTIONS
