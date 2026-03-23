"""Post-processing module that injects human-like imperfections into AI-generated text.

Applies typos, abbreviations, emoji, and community slang based on a persona's
imperfection_level (0-10). Level 0 = no changes, level 10 = maximum messiness.
"""
import random
import re

# Korean community abbreviations: formal -> casual
ABBREVIATIONS: list[tuple[str, str]] = [
    ("ㅋㅋ", "ㅋㅋㅋㅋ"),
    ("정말", "진짜"),
    ("진짜로", "ㄹㅇ"),
    ("사실", "솔직히"),
    ("그렇지만", "근데"),
    ("하지만", "근데"),
    ("그런데", "근데"),
    ("너무", "넘"),
    ("아니요", "아뇨"),
    ("맞아요", "ㅇㅇ"),
    ("그래서", "그래갖고"),
    ("무엇", "뭐"),
    ("것 같아요", "듯"),
    ("것 같다", "듯"),
    ("입니다", "임"),
    ("합니다", "함"),
    ("됩니다", "됨"),
    ("있습니다", "있음"),
    ("없습니다", "없음"),
    ("습니다", "음"),
    ("세요", "셈"),
    ("예요", "임"),
    ("이에요", "임"),
]

# Trailing particles and fillers real users append
TRAILING_FILLERS: list[str] = [
    "ㅋㅋ", "ㅋㅋㅋ", "ㅎㅎ", "ㅎ", "...", "..", "ㅠㅠ", "ㅠ",
    "ㄷㄷ", ";;", "~", "ㅇㅇ", "ㄹㅇ", "ㅎㅇ",
]

# Emoji pool for casual injection
EMOJI_POOL: list[str] = [
    "😂", "🤣", "😭", "🔥", "💀", "👍", "😎", "🤔",
    "😱", "🙏", "❤️", "👀", "😤", "🥲", "✨", "💯",
]

# Common Korean typo patterns (correct -> typo)
TYPO_PATTERNS: list[tuple[str, str]] = [
    ("되", "돼"),
    ("돼", "되"),
    ("않", "안"),
    ("맞", "맛"),
    ("웃기", "웃긴"),
    ("같아", "갈아"),
    ("에요", "예요"),
]

# Spacing removal patterns (real users often omit spaces)
SPACE_REMOVAL_TARGETS: list[str] = [
    "그리고 ", "하지만 ", "그런데 ", "그래서 ", "왜냐하면 ",
    "진짜 ", "너무 ", "정말 ", "아주 ",
]


def humanize(text: str, imperfection_level: int) -> str:
    """Apply human-like imperfections to text.

    Args:
        text: The AI-generated text.
        imperfection_level: 0 (pristine) to 10 (maximum messiness).

    Returns:
        Text with imperfections injected.
    """
    if imperfection_level <= 0 or not text:
        return text

    level = min(imperfection_level, 10)
    probability = level / 10.0  # 0.1 ~ 1.0

    result = text

    if level >= 3:
        result = _apply_abbreviations(result, probability)

    if level >= 2:
        result = _apply_typos(result, probability * 0.3)

    if level >= 4:
        result = _remove_some_spaces(result, probability * 0.2)

    if level >= 5:
        result = _remove_punctuation_formality(result, probability)

    if level >= 2:
        result = _append_trailing_filler(result, probability * 0.4)

    if level >= 6:
        result = _inject_emoji(result, probability * 0.3)

    return result


def _apply_abbreviations(text: str, probability: float) -> str:
    result = text
    for formal, casual in ABBREVIATIONS:
        if formal in result and random.random() < probability:
            result = result.replace(formal, casual, 1)
    return result


def _apply_typos(text: str, probability: float) -> str:
    result = text
    for correct, typo in TYPO_PATTERNS:
        if correct in result and random.random() < probability:
            result = result.replace(correct, typo, 1)
    return result


def _remove_some_spaces(text: str, probability: float) -> str:
    result = text
    for target in SPACE_REMOVAL_TARGETS:
        if target in result and random.random() < probability:
            result = result.replace(target, target.strip(), 1)
    return result


def _remove_punctuation_formality(text: str, probability: float) -> str:
    """Remove trailing periods (formal) -> more casual tone."""
    if random.random() > probability:
        return text
    # Remove trailing period if text ends with Korean + period
    result = re.sub(r'([가-힣])\.\s*$', r'\1', text)
    # Remove mid-sentence formal periods
    result = re.sub(r'([가-힣])\. ([가-힣])', r'\1 \2', result, count=1)
    return result


def _append_trailing_filler(text: str, probability: float) -> str:
    if random.random() > probability:
        return text
    filler = random.choice(TRAILING_FILLERS)
    # Don't double up if text already ends with similar
    if text.rstrip().endswith(filler[:2]):
        return text
    separator = " " if not text.endswith(" ") else ""
    return text.rstrip() + separator + filler


def _inject_emoji(text: str, probability: float) -> str:
    if random.random() > probability:
        return text
    emoji = random.choice(EMOJI_POOL)
    # Append at end
    return text.rstrip() + emoji
