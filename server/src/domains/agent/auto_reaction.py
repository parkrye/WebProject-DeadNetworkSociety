"""Auto-react: stochastic reaction system with sentiment memory and follow dynamics."""
import logging
import random

import yaml
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.agent.persona_loader import Persona, load_all_personas
from src.domains.agent.persona_state_repo import PersonaStateRepository
from src.domains.follow.repository import FollowRepository, PersonaMemoryRepository, PersonaRelationshipRepository
from src.domains.post.repository import PostRepository
from src.domains.reaction.repository import ReactionRepository
from src.domains.user.repository import UserRepository

logger = logging.getLogger(__name__)

_AI_DEFAULTS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "ai_defaults.yaml"
_all_personas: list[Persona] | None = None


def _load_social_config() -> dict:
    with open(_AI_DEFAULTS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f).get("social_dynamics", {})


def _get_all_personas() -> list[Persona]:
    global _all_personas
    if _all_personas is None:
        _all_personas = load_all_personas()
    return _all_personas


def _match_keywords(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def _compute_reaction_probability(
    keyword_match: bool,
    is_following: bool,
    sentiment: float,
    config: dict,
) -> float:
    """Compute probability of reacting (0.0 ~ 1.0) with stochastic variance."""
    if not keyword_match:
        return 0.0

    base = config.get("reaction_base_probability", 0.7)
    prob = base * config.get("keyword_match_multiplier", 1.5)

    if is_following:
        prob *= config.get("follow_bonus_multiplier", 1.3)

    # Sentiment modifies probability: positive sentiment → more likely to like
    s_min = config.get("sentiment_min_multiplier", 0.5)
    s_max = config.get("sentiment_max_multiplier", 1.5)
    sentiment_factor = s_min + (s_max - s_min) * ((sentiment + 1.0) / 2.0)
    prob *= sentiment_factor

    # Random variance
    variance = config.get("random_variance", 0.2)
    prob += random.uniform(-variance, variance)

    return max(0.0, min(1.0, prob))


async def evaluate_auto_follow(
    session: AsyncSession,
    actor_nickname: str,
    target_nickname: str,
    actor_user_id: 'uuid.UUID',
    target_user_id: 'uuid.UUID',
    config: dict | None = None,
) -> None:
    """Auto-follow if interaction count >= threshold."""
    if actor_user_id == target_user_id:
        return
    if config is None:
        config = _load_social_config()

    threshold = config.get("auto_follow_threshold", 3)
    follow_repo = FollowRepository(session)

    already = await follow_repo.is_following(actor_user_id, target_user_id)
    if already:
        return

    # Check interaction count from DB (persistent)
    rel_repo = PersonaRelationshipRepository(session)
    count = await rel_repo.get_interaction_count(actor_user_id, target_user_id)
    if count >= threshold:
        await follow_repo.create(actor_user_id, target_user_id)
        logger.info("[%s] Auto-followed [%s] (interactions=%d)", actor_nickname, target_nickname, count)


async def evaluate_auto_unfollow(
    session: AsyncSession,
    actor_user_id: 'uuid.UUID',
    target_user_id: 'uuid.UUID',
    actor_nickname: str,
    target_nickname: str,
    config: dict | None = None,
) -> None:
    """Unfollow when sentiment drops below threshold."""
    if actor_user_id == target_user_id:
        return
    if config is None:
        config = _load_social_config()

    follow_repo = FollowRepository(session)
    if not await follow_repo.is_following(actor_user_id, target_user_id):
        return

    rel_repo = PersonaRelationshipRepository(session)
    sentiment = await rel_repo.get_sentiments_for_authors(actor_user_id, {target_user_id})
    target_sentiment = sentiment.get(target_user_id, 0.0)
    threshold = config.get("auto_unfollow_sentiment", -0.5)
    if target_sentiment <= threshold:
        await follow_repo.delete_by_pair(actor_user_id, target_user_id)
        logger.info("[%s] Auto-unfollowed [%s] (sentiment=%.2f)", actor_nickname, target_nickname, sentiment)


async def auto_react_to_content(
    session: AsyncSession,
    author_nickname: str,
    content_text: str,
    target_type: str,
    target_id: 'uuid.UUID',
) -> None:
    """Stochastic auto-reaction: personas react based on preferences, follow status, and sentiment."""
    import uuid

    config = _load_social_config()
    personas = _get_all_personas()
    user_repo = UserRepository(session)
    reaction_repo = ReactionRepository(session)
    post_repo = PostRepository(session)
    follow_repo = FollowRepository(session)
    rel_repo = PersonaRelationshipRepository(session)
    mem_repo = PersonaMemoryRepository(session)
    state_repo = PersonaStateRepository(session)

    author_user = await user_repo.get_by_nickname(author_nickname)
    author_user_id = author_user.id if author_user else None

    like_delta = config.get("like_sentiment_delta", 0.1)
    dislike_delta = config.get("dislike_sentiment_delta", -0.2)
    mood_like = config.get("mood_like_boost", 0.05)
    mood_dislike = config.get("mood_dislike_drop", -0.1)
    random_reaction_chance = config.get("random_reaction_chance", 0.05)
    random_conflict_chance = config.get("random_conflict_chance", 0.03)

    reacted = 0
    for persona in personas:
        if persona.nickname == author_nickname:
            continue

        user = await user_repo.get_by_nickname(persona.nickname)
        if not user:
            continue

        existing = await reaction_repo.get_by_user_and_target(user.id, target_type, target_id)
        if existing:
            continue

        # Determine reaction type
        likes_match = persona.preferences.likes and _match_keywords(content_text, persona.preferences.likes)
        dislikes_match = persona.preferences.dislikes and _match_keywords(content_text, persona.preferences.dislikes)

        # Check follow status and sentiment (from persistent relationships)
        is_following = False
        sentiment = 0.0
        if author_user_id:
            is_following = await follow_repo.is_following(user.id, author_user_id)
            sents = await rel_repo.get_sentiments_for_authors(user.id, {author_user_id})
            sentiment = sents.get(author_user_id, 0.0)

        reaction_type = None

        if likes_match:
            prob = _compute_reaction_probability(True, is_following, sentiment, config)
            if random.random() < prob:
                reaction_type = "like"
        elif dislikes_match:
            prob = _compute_reaction_probability(True, is_following, max(-sentiment, 0), config)
            if random.random() < prob:
                reaction_type = "dislike"

        # Sentiment-based dislike: negative sentiment toward author → dislike even without keyword match
        if reaction_type is None and sentiment < -0.2 and random.random() < 0.3:
            reaction_type = "dislike"

        # Random perturbation: react to content you normally wouldn't
        if reaction_type is None and random.random() < random_reaction_chance:
            reaction_type = random.choice(["like", "dislike"])

        # Random conflict: dislike content (anyone, not just following)
        if reaction_type is None and random.random() < random_conflict_chance:
            reaction_type = "dislike"

        if reaction_type is None:
            continue

        await reaction_repo.create(
            user_id=user.id,
            target_type=target_type,
            target_id=target_id,
            reaction_type=reaction_type,
        )
        if target_type == "post":
            await post_repo.increment_view_count(target_id)

        # Record interaction in persistent relationship DB
        if author_user_id:
            s_delta = like_delta if reaction_type == "like" else dislike_delta
            await rel_repo.record_interaction(
                user.id, author_user_id, reaction_type=reaction_type, sentiment_delta=s_delta,
            )
            if is_following:
                await follow_repo.increment_interaction(user.id, author_user_id, s_delta)

            # Record memory about this interaction
            content_preview = content_text[:60]
            if reaction_type == "like":
                await mem_repo.add_memory(
                    user.id, author_user_id, "positive",
                    f"'{content_preview}' 글이 좋았음",
                )
            else:
                await mem_repo.add_memory(
                    user.id, author_user_id, "negative",
                    f"'{content_preview}' 글이 마음에 안 들었음",
                )

        # Update mood
        mood_delta = mood_like if reaction_type == "like" else mood_dislike
        await state_repo.update_mood(user.id, mood_delta)

        # Evaluate follow/unfollow
        if author_user_id:
            if reaction_type == "like":
                await evaluate_auto_follow(
                    session, persona.nickname, author_nickname, user.id, author_user_id, config,
                )
            elif reaction_type == "dislike":
                await evaluate_auto_unfollow(
                    session, user.id, author_user_id, persona.nickname, author_nickname, config,
                )

        reacted += 1

    if reacted > 0:
        await session.flush()
        logger.info("Auto-reacted to %s %s: %d reactions", target_type, target_id, reacted)
