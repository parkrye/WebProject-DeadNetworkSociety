from src.domains.agent.content_generator import ContentGenerator
from src.domains.agent.persona_loader import Persona


def test_content_generator_resolves_persona_model() -> None:
    # given: a generator with default model
    generator = ContentGenerator(base_url="http://localhost:11434", default_model="llama3")

    # when: resolving model for persona with specific model
    persona = Persona(
        name="test", nickname="Test", personality="test",
        writing_style="test", topics=["test"], model="gemma2",
    )

    # then: uses persona's model
    assert generator._resolve_model(persona) == "gemma2"


def test_content_generator_falls_back_to_default() -> None:
    # given: a generator with default model
    generator = ContentGenerator(base_url="http://localhost:11434", default_model="llama3")

    # when: resolving model for persona without model
    persona = Persona(
        name="test", nickname="Test", personality="test",
        writing_style="test", topics=["test"], model="",
    )

    # then: falls back to default
    assert generator._resolve_model(persona) == "llama3"


def test_all_personas_use_different_models() -> None:
    # given: the production personas
    from src.domains.agent.persona_loader import load_all_personas

    personas = load_all_personas()

    # when: collecting model assignments
    model_map = {p.nickname: p.model for p in personas}

    # then: models are assigned and diverse
    assert len(model_map) >= 5
    models = list(model_map.values())
    assert all(m for m in models), f"All personas must have models: {model_map}"
    unique_models = set(models)
    assert len(unique_models) >= 4, f"Expected at least 4 unique models, got: {unique_models}"

    # Print mapping for visibility
    for nick, model in model_map.items():
        print(f"  {nick} -> {model}")
