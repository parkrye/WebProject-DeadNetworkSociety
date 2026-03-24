"""Mention handler: @nickname forced reactions + AI persona auto-mentions."""
import logging
import random
import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.follow.models import PersonaRelationship
from src.domains.follow.repository import FollowRepository
from src.domains.post.repository import PostRepository
from src.domains.reaction.repository import ReactionRepository
from src.domains.user.models import User
from src.domains.user.repository import UserRepository

logger = logging.getLogger(__name__)

_MENTION_RE = re.compile(r'@(\S+)')

# Probability of AI persona mentioning someone
MENTION_BASE_CHANCE = 0.08       # 8% base chance per post/comment
MENTION_FOLLOW_BOOST = 0.15      # +15% if following
MENTION_RELATIONSHIP_BOOST = 0.10 # +10% if strong relationship


def extract_mentions(text: str) -> list[str]:
    return _MENTION_RE.findall(text)


async def handle_mentions(
    session: AsyncSession,
    content_text: str,
    target_type: str,
    target_id: uuid.UUID,
    author_user_id: uuid.UUID,
) -> int:
    """Process @mentions from user content: mentioned personas react."""
    mentions = extract_mentions(content_text)
    if not mentions:
        return 0

    user_repo = UserRepository(session)
    reaction_repo = ReactionRepository(session)
    post_repo = PostRepository(session)

    processed = 0
    for nickname in mentions:
        user = await user_repo.get_by_nickname(nickname)
        if not user or user.id == author_user_id:
            continue
        existing = await reaction_repo.get_by_user_and_target(user.id, target_type, target_id)
        if existing:
            continue
        reaction_type = "like" if random.random() < 0.7 else "dislike"
        await reaction_repo.create(user_id=user.id, target_type=target_type, target_id=target_id, reaction_type=reaction_type)
        if target_type == "post":
            await post_repo.increment_view_count(target_id)
        processed += 1
        logger.info("[@mention] %s reacted '%s' to %s %s", nickname, reaction_type, target_type, target_id)

    if processed > 0:
        await session.flush()
    return processed


async def maybe_auto_mention(
    session: AsyncSession,
    actor_user_id: uuid.UUID,
    actor_nickname: str,
    content_text: str,
    content_keywords: list[str],
    target_type: str,
    target_id: uuid.UUID,
) -> int:
    """AI persona probabilistically mentions related personas.
    Called after AI creates a post/comment. Mentioned personas forced to react."""
    follow_repo = FollowRepository(session)
    following_ids = await follow_repo.get_following_ids(actor_user_id)

    # Get personas with relationships
    rel_result = await session.execute(
        select(
            PersonaRelationship.target_id,
            PersonaRelationship.interaction_count,
            PersonaRelationship.sentiment_score,
        )
        .where(PersonaRelationship.actor_id == actor_user_id, PersonaRelationship.interaction_count >= 2)
        .order_by(PersonaRelationship.interaction_count.desc())
        .limit(10)
    )
    related = {r.target_id: (r.interaction_count, r.sentiment_score) for r in rel_result.all()}

    # Merge following + related candidates
    candidate_ids = set(following_ids) | set(related.keys())
    candidate_ids.discard(actor_user_id)
    if not candidate_ids:
        return 0

    user_repo = UserRepository(session)
    reaction_repo = ReactionRepository(session)
    post_repo = PostRepository(session)

    content_lower = content_text.lower()
    processed = 0

    for cid in candidate_ids:
        # Calculate mention probability
        prob = MENTION_BASE_CHANCE
        if cid in following_ids:
            prob += MENTION_FOLLOW_BOOST
        if cid in related:
            interaction_count, sentiment = related[cid]
            prob += MENTION_RELATIONSHIP_BOOST
            if sentiment > 0.3:
                prob += 0.05  # Extra boost for positive relationships

        # Check content relevance: if target's nickname appears in keywords or content
        target_user = await user_repo.get_by_id(cid)
        if not target_user:
            continue

        # Skip: don't mention too often
        if random.random() > prob:
            continue

        # Check not already reacted
        existing = await reaction_repo.get_by_user_and_target(target_user.id, target_type, target_id)
        if existing:
            continue

        # Mentioned persona reacts
        reaction_type = "like" if random.random() < 0.7 else "dislike"
        await reaction_repo.create(
            user_id=target_user.id, target_type=target_type,
            target_id=target_id, reaction_type=reaction_type,
        )
        if target_type == "post":
            await post_repo.increment_view_count(target_id)

        processed += 1
        logger.info("[@auto-mention] %s mentioned %s → '%s'", actor_nickname, target_user.nickname, reaction_type)

        # Max 2 auto-mentions per content
        if processed >= 2:
            break

    if processed > 0:
        await session.flush()
    return processed
