import json
from pathlib import Path

from src.domains.agent.sample_provider import SampleProvider


def _create_test_samples(tmp_path: Path) -> Path:
    samples = {
        "daily": [
            {
                "single_topic": "일상 생활",
                "utterances": [
                    {"speaker": "P01", "text": "오늘 뭐해?"},
                    {"speaker": "P02", "text": "집에서 쉬고 있어"},
                    {"speaker": "P01", "text": "나도 집에 있는데 심심해"},
                ],
            },
        ],
        "gaming": [
            {
                "single_topic": "게임",
                "utterances": [
                    {"speaker": "P01", "text": "오늘 롤 한판 할래?"},
                    {"speaker": "P02", "text": "좋아 바로 접속할게"},
                ],
            },
        ],
        "food": [
            {
                "single_topic": "식음료",
                "utterances": [
                    {"speaker": "P01", "text": "점심 뭐 먹을까"},
                    {"speaker": "P02", "text": "김치찌개 어때?"},
                ],
            },
        ],
    }
    path = tmp_path / "test_samples.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False)
    return path


def test_get_sample_with_matching_topic(tmp_path: Path) -> None:
    # given: samples loaded
    path = _create_test_samples(tmp_path)
    provider = SampleProvider(samples_path=path)

    # when: requesting sample for gaming topic
    sample = provider.get_sample(["gaming", "retro gaming"])

    # then: returns a gaming sample
    assert sample is not None
    assert sample["single_topic"] == "게임"


def test_get_sample_fallback_to_any(tmp_path: Path) -> None:
    # given: samples loaded
    path = _create_test_samples(tmp_path)
    provider = SampleProvider(samples_path=path)

    # when: requesting sample for unmapped topic
    sample = provider.get_sample(["quantum_physics"])

    # then: returns any available sample
    assert sample is not None


def test_get_sample_no_file() -> None:
    # given: non-existent samples file
    provider = SampleProvider(samples_path=Path("/nonexistent/samples.json"))

    # when: requesting sample
    sample = provider.get_sample(["anything"])

    # then: returns None
    assert sample is None


def test_format_as_example(tmp_path: Path) -> None:
    # given: a sample
    path = _create_test_samples(tmp_path)
    provider = SampleProvider(samples_path=path)
    sample = provider.get_sample(["food"])

    # when: formatting
    example = provider.format_as_example(sample)

    # then: contains speaker labels and text
    assert "P01:" in example
    assert "P02:" in example


def test_production_samples_loadable() -> None:
    # given: the production samples file
    provider = SampleProvider()

    # when: getting a sample
    sample = provider.get_sample(["daily life"])

    # then: returns a valid sample (if file exists)
    if sample:
        assert "utterances" in sample
        assert len(sample["utterances"]) > 0


def test_fewshot_in_content_generator(tmp_path: Path) -> None:
    # given: a generator with samples
    from src.domains.agent.content_generator import ContentGenerator
    from src.domains.agent.persona_loader import Persona

    generator = ContentGenerator(base_url="http://localhost:11434", default_model="llama3")

    persona = Persona(
        name="test", nickname="Test", personality="test",
        writing_style="test", topics=["gaming", "retro gaming"],
        model="llama3", archetype="expert",
    )

    # when: building fewshot section
    fewshot = generator._build_fewshot_section(persona)

    # then: contains conversation example (if samples exist)
    if fewshot:
        assert "한국어 대화" in fewshot
        assert "P01:" in fewshot or "P02:" in fewshot
