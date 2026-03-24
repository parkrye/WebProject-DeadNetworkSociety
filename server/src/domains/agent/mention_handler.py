"""Mention handler: when @nickname appears in content, force that persona to react."""
import logging
import random
import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.post.repository import PostRepository
from src.domains.reaction.repository import ReactionRepository
from src.domains.user.repository import UserRepository

logger = logging.getLogger(__name__)

_MENTION_RE = re.compile(r'@(\S+)')


def extract_mentions(text: str) -> list[str]:
    """Extract @nickname mentions from text."""
    return _MENTION_RE.findall(text)


async def handle_mentions(
    session: AsyncSession,
    content_text: str,
    target_type: str,
    target_id: uuid.UUID,
    author_user_id: uuid.UUID,
) -> int:
    """Process @mentions: mentioned personas will react and/or comment.
    Returns number of mentions processed."""
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

        # Check if already reacted
        existing = await reaction_repo.get_by_user_and_target(user.id, target_type, target_id)
        if existing:
            continue

        # Force reaction: 70% like, 30% dislike (mentioned = attention = mostly positive)
        reaction_type = "like" if random.random() < 0.7 else "dislike"
        await reaction_repo.create(
            user_id=user.id,
            target_type=target_type,
            target_id=target_id,
            reaction_type=reaction_type,
        )
        if target_type == "post":
            await post_repo.increment_view_count(target_id)

        processed += 1
        logger.info("[@mention] %s reacted '%s' to %s %s", nickname, reaction_type, target_type, target_id)

    if processed > 0:
        await session.flush()

    return processed
