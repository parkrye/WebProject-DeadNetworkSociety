from src.domains.agent.content_generator import ContentGenerator
from src.domains.agent.persona_loader import Persona, PersonaExamples, load_personas_by_model
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
        archetype_detail="요리 전문가. 식재료의 과학에 정통하다.",
    )

    system_prompt = generator._build_system_prompt(persona)

    assert "test personality" in system_prompt
    assert "test style" in system_prompt
    assert "Behavioral archetype:" in system_prompt
    assert "Archetype specification:" in system_prompt
    assert "요리 전문가" in system_prompt


def test_no_archetype_no_injection() -> None:
    generator = ContentGenerator(base_url="http://localhost:11434", default_model="llama3")
    persona = Persona(
        name="test", nickname="Test", personality="test",
        writing_style="test", topics=["test"], model="llama3",
    )

    system_prompt = generator._build_system_prompt(persona)

    assert "Behavioral archetype:" not in system_prompt


def test_persona_example_injected_for_post() -> None:
    generator = ContentGenerator(base_url="http://localhost:11434", default_model="llama3")
    persona = Persona(
        name="test", nickname="Test", personality="test",
        writing_style="test", topics=["test"], model="llama3",
        examples=PersonaExamples(
            post_title="테스트 제목",
            post_content="테스트 본문입니다.",
            comment="테스트 댓글",
        ),
    )

    example_section = generator._build_persona_example(persona, "post")

    assert "YOUR writing style" in example_section
    assert "테스트 제목" in example_section
    assert "테스트 본문입니다." in example_section


def test_persona_example_injected_for_comment() -> None:
    generator = ContentGenerator(base_url="http://localhost:11434", default_model="llama3")
    persona = Persona(
        name="test", nickname="Test", personality="test",
        writing_style="test", topics=["test"], model="llama3",
        examples=PersonaExamples(
            post_title="제목", post_content="본문",
            comment="이건 댓글 예시입니다",
        ),
    )

    example_section = generator._build_persona_example(persona, "comment")

    assert "YOUR comment style" in example_section
    assert "이건 댓글 예시입니다" in example_section


def test_no_examples_no_injection() -> None:
    generator = ContentGenerator(base_url="http://localhost:11434", default_model="llama3")
    persona = Persona(
        name="test", nickname="Test", personality="test",
        writing_style="test", topics=["test"], model="llama3",
    )

    assert generator._build_persona_example(persona, "post") == ""
    assert generator._build_persona_example(persona, "comment") == ""
