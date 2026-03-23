import math
import uuid
from dataclasses import dataclass

from src.domains.agent.persona_loader import Persona
from src.domains.agent.target_selector import (
    compute_engagement_score,
    compute_topic_score,
    select_comment,
    select_post,
)


@dataclass
class FakePost:
    id: uuid.UUID
    author_id: uuid.UUID
    title: str
    content: str


@dataclass
class FakeComment:
    id: uuid.UUID
    author_id: uuid.UUID
    content: str


def _make_persona(topics: list[str], nickname: str = "test_bot") -> Persona:
    return Persona(
        name="test", nickname=nickname,
        writing_style="test", topics=topics, model="llama3",
    )


def _make_post(title: str, content: str) -> FakePost:
    return FakePost(
        id=uuid.uuid4(), author_id=uuid.uuid4(),
        title=title, content=content,
    )


# --- Topic scoring ---

def test_topic_score_matching_keywords() -> None:
    persona = _make_persona(["gaming", "music"])
    score = compute_topic_score(persona, "오늘의 게임 추천", "이 게임 진짜 재밌음")
    assert score > 0


def test_topic_score_no_match() -> None:
    persona = _make_persona(["gaming"])
    score = compute_topic_score(persona, "오늘 날씨가 좋다", "산책 다녀왔어요")
    assert score == 0


def test_topic_score_multiple_topics() -> None:
    persona = _make_persona(["food", "cooking"])
    score_food = compute_topic_score(persona, "맛있는 요리 레시피", "식재료를 준비하세요")
    score_unrelated = compute_topic_score(persona, "주식 투자 전략", "오늘 시장 분석")
    assert score_food > score_unrelated


# --- Engagement scoring ---

def test_engagement_score_increases_with_activity() -> None:
    low = compute_engagement_score(1, 0, 0)
    high = compute_engagement_score(10, 5, 3)
    assert high > low


def test_engagement_score_zero_for_no_activity() -> None:
    score = compute_engagement_score(0, 0, 0)
    assert score == 0.0


# --- Post selection ---

def test_select_post_prefers_on_topic() -> None:
    persona = _make_persona(["gaming"])
    on_topic = _make_post("게임 리뷰", "이 게임은 정말 재밌다")
    off_topic = _make_post("오늘의 날씨", "맑음")

    selections = {"on": 0, "off": 0}
    for _ in range(200):
        result = select_post(persona, [on_topic, off_topic])
        if result.id == on_topic.id:
            selections["on"] += 1
        else:
            selections["off"] += 1

    assert selections["on"] > selections["off"]


def test_select_post_with_engagement_boost() -> None:
    persona = _make_persona(["daily life"])
    popular = _make_post("일상 이야기", "오늘 하루")
    quiet = _make_post("일상 이야기2", "어제 하루")

    engagement = {
        popular.id: (20, 10, 2),
        quiet.id: (0, 0, 0),
    }

    selections = {"popular": 0, "quiet": 0}
    for _ in range(200):
        result = select_post(persona, [popular, quiet], engagement_data=engagement)
        if result.id == popular.id:
            selections["popular"] += 1
        else:
            selections["quiet"] += 1

    assert selections["popular"] > selections["quiet"]


def test_select_post_returns_none_for_empty() -> None:
    persona = _make_persona(["gaming"])
    assert select_post(persona, []) is None


def test_select_post_single_item() -> None:
    persona = _make_persona(["gaming"])
    post = _make_post("게임", "게임 이야기")
    result = select_post(persona, [post])
    assert result.id == post.id


# --- Affinity-based selection (DB affinities dict) ---

def test_select_post_with_affinity() -> None:
    persona = _make_persona(["daily life"], nickname="botA")

    friend_id = uuid.uuid4()
    stranger_id = uuid.uuid4()
    friend_post = FakePost(id=uuid.uuid4(), author_id=friend_id, title="daily", content="today")
    stranger_post = FakePost(id=uuid.uuid4(), author_id=stranger_id, title="daily", content="today")

    # Simulate DB affinity: 20 interactions with friend, 0 with stranger
    affinities = {friend_id: math.log1p(20)}

    selections = {"friend": 0, "stranger": 0}
    for _ in range(200):
        result = select_post(persona, [friend_post, stranger_post], affinities=affinities)
        if result.id == friend_post.id:
            selections["friend"] += 1
        else:
            selections["stranger"] += 1

    assert selections["friend"] > selections["stranger"]


# --- Comment selection with affinity ---

def test_select_comment_with_affinity() -> None:
    persona = _make_persona(["daily life"], nickname="botX")

    friend_id = uuid.uuid4()
    stranger_id = uuid.uuid4()
    friend_comment = FakeComment(id=uuid.uuid4(), author_id=friend_id, content="good post")
    stranger_comment = FakeComment(id=uuid.uuid4(), author_id=stranger_id, content="good post")

    affinities = {friend_id: math.log1p(20)}

    selections = {"friend": 0, "stranger": 0}
    for _ in range(200):
        result = select_comment(persona, [friend_comment, stranger_comment], affinities=affinities)
        if result.id == friend_comment.id:
            selections["friend"] += 1
        else:
            selections["stranger"] += 1

    assert selections["friend"] > selections["stranger"]


def test_select_comment_returns_none_for_empty() -> None:
    persona = _make_persona(["gaming"])
    assert select_comment(persona, []) is None
