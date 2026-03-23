"""Social dynamics engine: interest contagion, mood decay, random perturbation."""
import json
import logging
import random
import uuid

import yaml
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.agent.models import PersonaState
from src.domains.agent.persona_state_repo import PersonaStateRepository
from src.domains.follow.models import Follow
from src.domains.follow.repository import FollowRepository
from src.domains.post.models import Post

logger = logging.getLogger(__name__)

_AI_DEFAULTS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "ai_defaults.yaml"


def _load_social_config() -> dict:
    with open(_AI_DEFAULTS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f).get("social_dynamics", {})


async def run_social_dynamics_cycle(
    session: AsyncSession,
    user_id: uuid.UUID,
    persona_nickname: str,
    original_topics: list[str],
) -> None:
    """Run one cycle of social dynamics for a persona: contagion + mood decay + random follow."""
    config = _load_social_config()
    state_repo = PersonaStateRepository(session)
    follow_repo = FollowRepository(session)

    state = await state_repo.get_or_create(user_id, default_interests=original_topics)
    interests = state_repo.get_interests(state)
    if not interests:
        interests = list(original_topics)

    max_interests = config.get("max_active_interests", 10)

    # 1. Interest contagion: absorb a topic from someone you follow
    absorb_chance = config.get("contagion_absorb_chance", 0.10)
    if random.random() < absorb_chance:
        new_topic = await _pick_following_topic(session, user_id)
        if new_topic and new_topic not in interests:
            interests.append(new_topic)
            if len(interests) > max_interests:
                interests = interests[-max_interests:]
            logger.info("[%s] Absorbed interest: %s", persona_nickname, new_topic)

    # 2. Interest decay: forget the oldest interest
    forget_chance = config.get("contagion_forget_chance", 0.05)
    if random.random() < forget_chance and len(interests) > 3:
        # Don't forget original core topics (keep at least 3)
        forgotten = interests.pop(0)
        logger.info("[%s] Forgot interest: %s", persona_nickname, forgotten)

    await state_repo.set_interests(state, interests)

    # 3. Mood decay toward neutral
    mood_decay = config.get("mood_decay_rate", 0.1)
    await state_repo.decay_mood(user_id, mood_decay)

    # 4. Random follow/unfollow perturbation
    random_follow_chance = config.get("random_follow_change_chance", 0.01)
    if random.random() < random_follow_chance:
        await _random_follow_perturbation(session, user_id, persona_nickname)

    await session.flush()


async def _pick_following_topic(session: AsyncSession, user_id: uuid.UUID) -> str | None:
    """Pick a random topic from a random person this user follows, based on their recent posts."""
    follow_repo = FollowRepository(session)
    following_ids = await follow_repo.get_following_ids(user_id)
    if not following_ids:
        return None

    target_id = random.choice(list(following_ids))

    # Get a recent post from this followed user
    stmt = (
        select(Post.title, Post.content)
        .where(Post.author_id == target_id)
        .order_by(Post.created_at.desc())
        .limit(3)
    )
    result = await session.execute(stmt)
    posts = result.all()
    if not posts:
        return None

    post = random.choice(posts)
    # Extract a "topic" from the post — use first significant word from title
    words = post.title.split()
    if words:
        return random.choice(words)
    return None


async def _random_follow_perturbation(
    session: AsyncSession, user_id: uuid.UUID, nickname: str,
) -> None:
    """Randomly follow or unfollow someone to break stable patterns."""
    from src.domains.user.models import User

    follow_repo = FollowRepository(session)

    if random.random() < 0.5:
        # Random follow: pick a random non-followed user
        following_ids = await follow_repo.get_following_ids(user_id)
        stmt = (
            select(User.id, User.nickname)
            .where(User.id != user_id, User.is_agent == True)
            .limit(50)
        )
        result = await session.execute(stmt)
        candidates = [(r.id, r.nickname) for r in result.all() if r.id not in following_ids]
        if candidates:
            target_id, target_nick = random.choice(candidates)
            await follow_repo.create(user_id, target_id)
            logger.info("[%s] Random-followed [%s]", nickname, target_nick)
    else:
        # Random unfollow: unfollow someone with low sentiment
        following_ids = await follow_repo.get_following_ids(user_id)
        if following_ids:
            target_id = random.choice(list(following_ids))
            await follow_repo.delete_by_pair(user_id, target_id)
            logger.info("[%s] Random-unfollowed user %s", nickname, target_id)


def get_active_interests(state: PersonaState | None, original_topics: list[str]) -> list[str]:
    """Get effective interests: dynamic state if available, else original topics."""
    if state is None:
        return list(original_topics)
    try:
        interests = json.loads(state.active_interests)
        return interests if interests else list(original_topics)
    except (json.JSONDecodeError, TypeError):
        return list(original_topics)
