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

    # then: at least 4 personas exist and are valid
    assert len(personas) >= 4
    for persona in personas:
        assert persona.name
        assert persona.nickname
        assert persona.personality
        assert persona.writing_style
        assert len(persona.topics) > 0
