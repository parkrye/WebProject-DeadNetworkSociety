from pathlib import Path

from src.domains.agent.persona_loader import VALID_ARCHETYPES, load_all_personas, load_persona, load_personas_by_model


def test_load_persona_with_all_fields(tmp_path: Path) -> None:
    content = """
name: test_bot
nickname: TestBot
model: llama3
archetype: expert
activity_level: 7
recent_scope: 15
personality: A test persona
writing_style: Simple and direct
topics:
  - testing
  - automation
examples:
  post_title: "테스트 제목"
  post_content: "테스트 본문입니다."
  comment: "테스트 댓글입니다."
"""
    file_path = tmp_path / "test_bot.yaml"
    file_path.write_text(content, encoding="utf-8")

    persona = load_persona(file_path)

    assert persona.name == "test_bot"
    assert persona.nickname == "TestBot"
    assert persona.model == "llama3"
    assert persona.archetype == "expert"
    assert persona.activity_level == 7
    assert persona.recent_scope == 15
    assert persona.topics == ["testing", "automation"]
    assert persona.examples.post_title == "테스트 제목"
    assert persona.examples.post_content == "테스트 본문입니다."
    assert persona.examples.comment == "테스트 댓글입니다."


def test_load_persona_defaults(tmp_path: Path) -> None:
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

    persona = load_persona(file_path)

    assert persona.model == ""
    assert persona.activity_level == 5
    assert persona.recent_scope == 10


def test_load_persona_clamps_activity_level(tmp_path: Path) -> None:
    content = """
name: extreme
nickname: Extreme
model: llama3
activity_level: 99
personality: Over the top
writing_style: Loud
topics:
  - chaos
"""
    file_path = tmp_path / "extreme.yaml"
    file_path.write_text(content, encoding="utf-8")

    persona = load_persona(file_path)

    assert persona.activity_level == 10


def test_load_all_personas_recursive(tmp_path: Path) -> None:
    (tmp_path / "model_a").mkdir()
    (tmp_path / "model_b").mkdir()
    for i in range(3):
        content = f"""
name: bot_{i}
nickname: Bot{i}
model: model_a
personality: Bot {i}
writing_style: Style {i}
topics:
  - topic_{i}
"""
        (tmp_path / "model_a" / f"bot_{i}.yaml").write_text(content, encoding="utf-8")

    content = """
name: other
nickname: Other
model: model_b
personality: Other bot
writing_style: Other style
topics:
  - other
"""
    (tmp_path / "model_b" / "other.yaml").write_text(content, encoding="utf-8")

    personas = load_all_personas(tmp_path)

    assert len(personas) == 4


def test_load_personas_by_model(tmp_path: Path) -> None:
    for model in ["llama3", "gemma2"]:
        (tmp_path / model).mkdir()
        for i in range(2):
            content = f"""
name: {model}_bot_{i}
nickname: {model.title()}Bot{i}
model: {model}
personality: A {model} bot
writing_style: Standard
topics:
  - test
"""
            (tmp_path / model / f"bot_{i}.yaml").write_text(content, encoding="utf-8")

    grouped = load_personas_by_model(tmp_path)

    assert len(grouped) == 2
    assert len(grouped["llama3"]) == 2
    assert len(grouped["gemma2"]) == 2


def test_load_production_personas() -> None:
    personas = load_all_personas()

    assert len(personas) >= 240

    grouped = load_personas_by_model()
    assert len(grouped) >= 8
    for model, model_personas in grouped.items():
        assert len(model_personas) == 30, f"Model {model} should have 30 personas, got {len(model_personas)}"


def test_all_personas_have_valid_fields() -> None:
    personas = load_all_personas()

    for p in personas:
        assert p.name, f"Missing name: {p}"
        assert p.nickname, f"Missing nickname: {p}"
        assert p.model, f"Missing model: {p}"
        assert p.personality, f"Missing personality: {p}"
        assert p.writing_style, f"Missing writing_style: {p}"
        assert len(p.topics) > 0, f"No topics: {p}"
        assert 1 <= p.activity_level <= 10, f"Invalid activity_level: {p}"
        assert p.recent_scope >= 1, f"Invalid recent_scope: {p}"
        assert p.archetype in VALID_ARCHETYPES, f"Invalid archetype '{p.archetype}': {p.nickname}"
        assert p.archetype_detail, f"{p.nickname} missing archetype_detail"


def test_all_archetypes_represented() -> None:
    personas = load_all_personas()

    used_archetypes = {p.archetype for p in personas}

    for archetype in VALID_ARCHETYPES:
        assert archetype in used_archetypes, f"Archetype '{archetype}' has no personas"


def test_archetype_distribution() -> None:
    personas = load_all_personas()

    counts: dict[str, int] = {}
    for p in personas:
        counts[p.archetype] = counts.get(p.archetype, 0) + 1

    for archetype, count in counts.items():
        assert count >= 4, f"Archetype '{archetype}' only has {count} personas, expected at least 4"


def test_all_personas_have_examples() -> None:
    personas = load_all_personas()

    for p in personas:
        assert p.examples.post_title, f"{p.nickname} missing post_title example"
        assert p.examples.post_content, f"{p.nickname} missing post_content example"
        assert p.examples.comment, f"{p.nickname} missing comment example"
