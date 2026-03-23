import random

from src.domains.agent.text_humanizer import (
    humanize,
    _apply_abbreviations,
    _apply_typos,
    _append_trailing_filler,
    _inject_emoji,
    _remove_punctuation_formality,
    TRAILING_FILLERS,
    EMOJI_POOL,
)


def test_level_zero_returns_unchanged() -> None:
    text = "안녕하세요. 정말 좋은 날씨입니다."
    assert humanize(text, 0) == text


def test_empty_text_returns_empty() -> None:
    assert humanize("", 5) == ""


def test_level_ten_modifies_text() -> None:
    random.seed(42)
    text = "정말로 하지만 맞아요. 그래서 합니다."
    result = humanize(text, 10)
    assert result != text


def test_abbreviations_applied() -> None:
    random.seed(1)
    text = "정말 좋은 날씨입니다"
    result = _apply_abbreviations(text, 1.0)
    assert "진짜" in result or "정말" in result


def test_abbreviations_not_applied_at_zero_probability() -> None:
    text = "정말 좋은 날씨입니다"
    result = _apply_abbreviations(text, 0.0)
    assert result == text


def test_typos_applied() -> None:
    random.seed(0)
    text = "이것은 되는 것이고 맞는 말입니다"
    result = _apply_typos(text, 1.0)
    assert result != text


def test_trailing_filler_appended() -> None:
    random.seed(0)
    text = "좋은 글이네요"
    result = _append_trailing_filler(text, 1.0)
    has_filler = any(result.endswith(f) or f in result for f in TRAILING_FILLERS)
    assert has_filler


def test_trailing_filler_not_doubled() -> None:
    text = "좋아요ㅋㅋ"
    result = _append_trailing_filler(text, 1.0)
    assert result.count("ㅋㅋ") <= 2


def test_emoji_injected() -> None:
    random.seed(0)
    text = "재미있는 글이네요"
    result = _inject_emoji(text, 1.0)
    has_emoji = any(e in result for e in EMOJI_POOL)
    assert has_emoji


def test_punctuation_formality_removed() -> None:
    random.seed(0)
    text = "좋은 날입니다."
    result = _remove_punctuation_formality(text, 1.0)
    assert not result.endswith(".")


def test_level_gradation() -> None:
    """Higher levels should generally produce more changes."""
    random.seed(42)
    text = "정말로 하지만 맞아요. 그래서 합니다. 좋은 날입니다."

    low_changes = 0
    high_changes = 0
    for _ in range(100):
        low_result = humanize(text, 2)
        high_result = humanize(text, 9)
        if low_result != text:
            low_changes += 1
        if high_result != text:
            high_changes += 1

    assert high_changes >= low_changes


def test_humanize_preserves_korean() -> None:
    text = "한글 테스트 문장입니다"
    result = humanize(text, 5)
    assert any('\uac00' <= c <= '\ud7a3' for c in result)
