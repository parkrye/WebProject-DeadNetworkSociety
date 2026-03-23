from src.domains.agent.action_selector import (
    ACTION_COMMENT,
    ACTION_CREATE_POST,
    ACTION_QUICK_REACT,
    ACTION_REPLY,
    ALL_ACTIONS,
    AgentAction,
    generate_action_set,
)
from src.domains.agent.persona_loader import Persona


def _make_persona(name: str = "test", activity_level: int = 5) -> Persona:
    return Persona(
        name=name, nickname=name.title(),
        writing_style="test", topics=["test"], model="llama3",
        activity_level=activity_level, recent_scope=10,
    )


def test_generate_action_set_count() -> None:
    personas = [_make_persona("a", 3), _make_persona("b", 5)]
    action_set = generate_action_set(personas)
    assert len(action_set) == 8


def test_generate_action_set_only_content_actions() -> None:
    personas = [_make_persona("active", 10)]
    all_types: set[str] = set()
    for _ in range(50):
        for action in generate_action_set(personas):
            all_types.add(action.action_type)

    assert all_types == {ACTION_COMMENT, ACTION_REPLY, ACTION_CREATE_POST, ACTION_QUICK_REACT}
    assert "like" not in all_types
    assert "dislike" not in all_types


def test_generate_action_set_is_shuffled() -> None:
    personas = [_make_persona("a", 5), _make_persona("b", 5)]
    orderings = set()
    for _ in range(20):
        action_set = generate_action_set(personas)
        ordering = tuple((a.persona.name, a.action_type) for a in action_set)
        orderings.add(ordering)
    assert len(orderings) > 1


def test_generate_action_set_preserves_persona() -> None:
    persona = _make_persona("solo", 3)
    action_set = generate_action_set([persona])
    for action in action_set:
        assert action.persona.name == "solo"


def test_generate_action_set_single_activity() -> None:
    persona = _make_persona("quiet", 1)
    action_set = generate_action_set([persona])
    assert len(action_set) == 1
    assert action_set[0].action_type in ALL_ACTIONS
