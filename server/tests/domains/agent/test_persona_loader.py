from pathlib import Path

import pytest

from src.domains.agent.persona_loader import load_all_personas, load_persona

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_persona_file(tmp_path: Path) -> Path:
    content = """
name: test_bot
nickname: TestBot
personality: A test persona
writing_style: Simple and direct
topics:
  - testing
  - automation
activity_ratios:
  create_post: 0.5
  comment: 0.3
  reaction: 0.2
"""
    file_path = tmp_path / "test_bot.yaml"
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_load_persona(sample_persona_file: Path) -> None:
    # given: a valid persona YAML file

    # when: loading the persona
    persona = load_persona(sample_persona_file)

    # then: all fields are parsed correctly
    assert persona.name == "test_bot"
    assert persona.nickname == "TestBot"
    assert "test persona" in persona.personality
    assert persona.topics == ["testing", "automation"]
    assert persona.activity_ratios["create_post"] == 0.5


def test_load_persona_without_activity_ratios(tmp_path: Path) -> None:
    # given: a persona without activity_ratios
    content = """
name: minimal
nickname: Minimal
personality: Minimal persona
writing_style: Minimal
topics:
  - general
"""
    file_path = tmp_path / "minimal.yaml"
    file_path.write_text(content, encoding="utf-8")

    # when: loading the persona
    persona = load_persona(file_path)

    # then: activity_ratios defaults to empty dict
    assert persona.activity_ratios == {}


def test_load_all_personas(tmp_path: Path) -> None:
    # given: multiple persona files
    for i in range(3):
        content = f"""
name: bot_{i}
nickname: Bot{i}
personality: Bot {i} persona
writing_style: Style {i}
topics:
  - topic_{i}
"""
        (tmp_path / f"bot_{i}.yaml").write_text(content, encoding="utf-8")

    # when: loading all personas
    personas = load_all_personas(tmp_path)

    # then: all personas are loaded
    assert len(personas) == 3


def test_load_all_personas_empty_dir(tmp_path: Path) -> None:
    # given: an empty directory

    # when: loading personas
    personas = load_all_personas(tmp_path)

    # then: returns empty list
    assert personas == []


def test_load_all_personas_nonexistent_dir() -> None:
    # given: a non-existent directory

    # when: loading personas
    personas = load_all_personas(Path("/nonexistent/path"))

    # then: returns empty list
    assert personas == []


def test_load_production_personas() -> None:
    # given: the actual personas directory

    # when: loading all production personas
    personas = load_all_personas()

    # then: at least 5 personas exist and are valid
    assert len(personas) >= 5
    for persona in personas:
        assert persona.name
        assert persona.nickname
        assert persona.personality
        assert persona.writing_style
        assert len(persona.topics) > 0


def test_each_persona_has_unique_model() -> None:
    # given: all production personas

    # when: loading them
    personas = load_all_personas()

    # then: each persona specifies a model and models are diverse
    models = [p.model for p in personas]
    assert all(m for m in models), "All personas should specify a model"
    assert len(set(models)) >= 3, "At least 3 different models should be used"


def test_load_persona_with_model(tmp_path: Path) -> None:
    # given: a persona with a model field
    content = """
name: model_bot
nickname: ModelBot
model: gemma2
personality: A bot with a model
writing_style: Direct
topics:
  - testing
"""
    file_path = tmp_path / "model_bot.yaml"
    file_path.write_text(content, encoding="utf-8")

    # when: loading the persona
    persona = load_persona(file_path)

    # then: model is parsed
    assert persona.model == "gemma2"


def test_load_persona_without_model_defaults_empty(tmp_path: Path) -> None:
    # given: a persona without model field
    content = """
name: no_model
nickname: NoModel
personality: No model specified
writing_style: Default
topics:
  - general
"""
    file_path = tmp_path / "no_model.yaml"
    file_path.write_text(content, encoding="utf-8")

    # when: loading the persona
    persona = load_persona(file_path)

    # then: model defaults to empty string
    assert persona.model == ""
