from src.domains.agent.content_generator import ContentGenerator
from src.domains.agent.persona_loader import Persona, load_personas_by_model
from src.domains.agent.action_selector import generate_action_set, ALL_ACTIONS


def test_content_generator_resolves_persona_model() -> None:
    generator = ContentGenerator(base_url="http://localhost:11434", default_model="llama3")
    persona = Persona(
        name="test", nickname="Test", personality="test",
        writing_style="test", topics=["test"], model="gemma2",
    )

    assert generator._resolve_model(persona) == "gemma2"


def test_content_generator_falls_back_to_default() -> None:
    generator = ContentGenerator(base_url="http://localhost:11434", default_model="llama3")
    persona = Persona(
        name="test", nickname="Test", personality="test",
        writing_style="test", topics=["test"], model="",
    )

    assert generator._resolve_model(persona) == "llama3"


def test_five_models_with_ten_personas_each() -> None:
    grouped = load_personas_by_model()

    assert len(grouped) >= 5
    for model, personas in grouped.items():
        assert len(personas) == 10, f"{model} has {len(personas)} personas, expected 10"


def test_set_generation_respects_activity_levels() -> None:
    grouped = load_personas_by_model()

    for model, personas in grouped.items():
        action_set = generate_action_set(personas)

        expected = sum(p.activity_level for p in personas)
        assert len(action_set) == expected, f"{model}: expected {expected} actions, got {len(action_set)}"

        for action in action_set:
            assert action.action_type in ALL_ACTIONS


def test_activity_level_distribution() -> None:
    grouped = load_personas_by_model()

    all_levels = []
    for personas in grouped.values():
        levels = [p.activity_level for p in personas]
        all_levels.extend(levels)

    assert min(all_levels) <= 3, "Should have quiet personas"
    assert max(all_levels) >= 8, "Should have active personas"


def test_archetype_prompt_injected_in_system_prompt() -> None:
    generator = ContentGenerator(base_url="http://localhost:11434", default_model="llama3")
    persona = Persona(
        name="test", nickname="Test", personality="test personality",
        writing_style="test style", topics=["test"],
        model="llama3", archetype="expert",
    )

    system_prompt = generator._build_system_prompt(persona)

    assert "test personality" in system_prompt
    assert "test style" in system_prompt
    assert "Behavioral archetype:" in system_prompt
    assert "expert" in system_prompt.lower()


def test_no_archetype_no_injection() -> None:
    generator = ContentGenerator(base_url="http://localhost:11434", default_model="llama3")
    persona = Persona(
        name="test", nickname="Test", personality="test",
        writing_style="test", topics=["test"], model="llama3",
    )

    system_prompt = generator._build_system_prompt(persona)

    assert "Behavioral archetype:" not in system_prompt
