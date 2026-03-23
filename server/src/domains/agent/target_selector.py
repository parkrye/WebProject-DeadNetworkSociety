"""Selects posts/comments for agent interaction using topic affinity,
engagement score, and inter-agent affinity (relationship tracking).

Replaces random.choice with weighted probabilistic selection.
"""
import logging
import random
import uuid
from collections import defaultdict
from dataclasses import dataclass, field

from src.domains.agent.persona_loader import Persona

logger = logging.getLogger(__name__)

# Topic keyword mapping: English topic -> Korean keywords for text matching
TOPIC_KEYWORDS: dict[str, list[str]] = {
    "food": ["음식", "요리", "맛", "레시피", "밥", "먹", "식당", "배달"],
    "cooking": ["요리", "레시피", "식재료", "조리", "맛"],
    "street food": ["길거리", "음식", "포장마차", "떡볶이", "분식"],
    "traditional cooking": ["전통", "요리", "음식", "한식", "된장"],
    "gaming": ["게임", "플레이", "캐릭터", "스테이지", "공략", "겜"],
    "retro gaming": ["레트로", "게임", "오락실", "추억", "고전"],
    "music": ["음악", "노래", "앨범", "가수", "멜로디"],
    "movies": ["영화", "감독", "배우", "개봉", "관람"],
    "film": ["영화", "감독", "촬영", "씬"],
    "anime": ["애니", "만화", "캐릭터", "성우"],
    "technology": ["기술", "IT", "개발", "프로그래밍", "AI"],
    "programming": ["코딩", "개발", "프로그래밍", "버그", "코드"],
    "science": ["과학", "연구", "실험", "발견"],
    "travel": ["여행", "관광", "숙소", "비행", "해외"],
    "fitness": ["운동", "헬스", "근력", "다이어트", "체력"],
    "health": ["건강", "병원", "약", "치료", "영양"],
    "sports": ["스포츠", "축구", "야구", "농구", "경기", "선수"],
    "fashion": ["패션", "옷", "스타일", "브랜드", "코디"],
    "beauty": ["뷰티", "화장", "스킨케어", "메이크업"],
    "pets": ["반려", "강아지", "고양이", "동물", "펫"],
    "animals": ["동물", "고양이", "강아지", "반려"],
    "books": ["책", "독서", "작가", "소설", "도서"],
    "literature": ["문학", "소설", "시", "작가"],
    "philosophy": ["철학", "사유", "존재", "의미"],
    "art": ["예술", "그림", "미술", "작품", "전시"],
    "finance": ["투자", "주식", "금융", "경제", "재테크"],
    "crypto": ["코인", "비트코인", "블록체인", "암호화폐"],
    "career": ["직장", "회사", "커리어", "취업", "이직"],
    "education": ["교육", "학교", "공부", "시험", "수업"],
    "nature": ["자연", "산", "바다", "숲", "환경"],
    "humor": ["웃긴", "유머", "개그", "ㅋㅋ", "웃음"],
    "memes": ["밈", "짤", "유행", "ㅋㅋ"],
    "daily life": ["일상", "오늘", "하루", "생활"],
    "random thoughts": ["생각", "느낌", "갑자기", "문득"],
    "relationships": ["연애", "사랑", "이별", "썸"],
    "nostalgia for the old days": ["옛날", "추억", "그때", "시절"],
    "complaints about modern society": ["요즘", "세상", "사회", "불만"],
    "rising prices and economic complaints": ["물가", "비싸", "가격", "경제"],
    "grandchildren and family": ["손주", "가족", "아이", "엄마", "아빠"],
    "quest design": ["퀘스트", "미션", "보상", "경험치"],
    "daily life gamification": ["게이미피케이션", "레벨", "경험치", "도전"],
    "character builds": ["캐릭터", "빌드", "스펙", "스탯"],
    "minimal reactions to any topic": ["읽음", "봤음", "확인"],
    "horror": ["공포", "무서운", "귀신", "호러"],
    "mystery": ["미스터리", "추리", "범인", "사건"],
    "drama": ["드라마", "방영", "회차", "배우"],
    "K-pop": ["케이팝", "아이돌", "컴백", "앨범"],
    "coffee": ["커피", "카페", "원두", "라떼"],
    "cooking ASMR": ["ASMR", "소리", "요리", "먹방"],
    "camping": ["캠핑", "텐트", "야외", "불멍"],
    "webtoon": ["웹툰", "만화", "연재", "작가"],
    "ramen": ["라면", "라멘", "면", "국물"],
}

# Minimum score for a post to be considered "on-topic"
TOPIC_MATCH_THRESHOLD = 1

# Weight multipliers
TOPIC_WEIGHT = 3.0
ENGAGEMENT_WEIGHT = 1.5
AFFINITY_WEIGHT = 2.0
BASE_WEIGHT = 1.0


@dataclass
class PostCandidate:
    post: object  # Post model
    topic_score: float = 0.0
    engagement_score: float = 0.0
    affinity_score: float = 0.0

    @property
    def total_weight(self) -> float:
        return (
            BASE_WEIGHT
            + self.topic_score * TOPIC_WEIGHT
            + self.engagement_score * ENGAGEMENT_WEIGHT
            + self.affinity_score * AFFINITY_WEIGHT
        )


class AffinityTracker:
    """In-memory tracker for inter-agent interaction frequency.

    Tracks how often agent A interacts with agent B's content.
    Used to boost reply/comment probability toward frequent interaction partners.
    """

    def __init__(self) -> None:
        # {agent_nickname: {other_nickname: interaction_count}}
        self._interactions: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def record(self, actor: str, target_author: str) -> None:
        if actor != target_author:
            self._interactions[actor][target_author] += 1

    def get_affinity(self, actor: str, target_author: str) -> float:
        count = self._interactions.get(actor, {}).get(target_author, 0)
        if count == 0:
            return 0.0
        # Logarithmic scale to prevent runaway affinity
        import math
        return math.log1p(count)

    def get_top_partners(self, actor: str, limit: int = 5) -> list[tuple[str, int]]:
        partners = self._interactions.get(actor, {})
        return sorted(partners.items(), key=lambda x: x[1], reverse=True)[:limit]


# Module-level singleton
_affinity_tracker = AffinityTracker()


def get_affinity_tracker() -> AffinityTracker:
    return _affinity_tracker


def compute_topic_score(persona: Persona, title: str, content: str) -> float:
    """Score how well a post matches the persona's topics."""
    text = f"{title} {content}".lower()
    score = 0.0

    for topic in persona.topics:
        topic_lower = topic.lower()
        # Direct keyword match from mapping
        keywords = TOPIC_KEYWORDS.get(topic_lower, [])
        for kw in keywords:
            if kw in text:
                score += 1.0

        # Fallback: direct topic string match
        if topic_lower in text:
            score += 0.5

    return score


def compute_engagement_score(comment_count: int, like_count: int, dislike_count: int) -> float:
    """Score based on post engagement. More engagement = more attractive."""
    import math
    total_reactions = like_count + dislike_count
    # Log scale to prevent extremely popular posts from dominating
    return math.log1p(comment_count + total_reactions)


def select_post(
    persona: Persona,
    posts: list,
    author_nicknames: dict[uuid.UUID, str] | None = None,
    engagement_data: dict[uuid.UUID, tuple[int, int, int]] | None = None,
) -> object | None:
    """Select a post with weighted probability based on topic, engagement, and affinity.

    Args:
        persona: The acting persona.
        posts: List of Post objects.
        author_nicknames: {post.author_id: nickname} for affinity lookup.
        engagement_data: {post.id: (comment_count, like_count, dislike_count)}.

    Returns:
        Selected Post object, or None if no posts available.
    """
    if not posts:
        return None

    candidates: list[PostCandidate] = []
    tracker = get_affinity_tracker()

    for post in posts:
        candidate = PostCandidate(post=post)

        # Topic score
        candidate.topic_score = compute_topic_score(
            persona, getattr(post, "title", ""), getattr(post, "content", ""),
        )

        # Engagement score
        if engagement_data:
            post_id = getattr(post, "id", None)
            if post_id and post_id in engagement_data:
                c, l, d = engagement_data[post_id]
                candidate.engagement_score = compute_engagement_score(c, l, d)

        # Affinity score
        if author_nicknames:
            author_id = getattr(post, "author_id", None)
            if author_id and author_id in author_nicknames:
                author_nick = author_nicknames[author_id]
                candidate.affinity_score = tracker.get_affinity(persona.nickname, author_nick)

        candidates.append(candidate)

    # Weighted random selection
    weights = [c.total_weight for c in candidates]
    selected = random.choices(candidates, weights=weights, k=1)[0]
    return selected.post


def select_comment(
    persona: Persona,
    comments: list,
    author_nicknames: dict[uuid.UUID, str] | None = None,
) -> object | None:
    """Select a comment for reply with affinity-weighted probability."""
    if not comments:
        return None

    tracker = get_affinity_tracker()
    weights: list[float] = []

    for comment in comments:
        weight = BASE_WEIGHT
        if author_nicknames:
            author_id = getattr(comment, "author_id", None)
            if author_id and author_id in author_nicknames:
                author_nick = author_nicknames[author_id]
                weight += tracker.get_affinity(persona.nickname, author_nick) * AFFINITY_WEIGHT
        weights.append(weight)

    selected = random.choices(comments, weights=weights, k=1)[0]
    return selected
