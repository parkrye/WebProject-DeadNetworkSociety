"""Auto-react: after content creation, other personas like/dislike based on preferences."""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.agent.persona_loader import Persona, load_all_personas
from src.domains.reaction.repository import ReactionRepository
from src.domains.user.repository import UserRepository
from src.shared.event_bus import event_bus
from src.shared.events import ReactionCreated

logger = logging.getLogger(__name__)

_all_personas: list[Persona] | None = None


def _get_all_personas() -> list[Persona]:
    global _all_personas
    if _all_personas is None:
        _all_personas = load_all_personas()
    return _all_personas


def _match_keywords(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


async def auto_react_to_content(
    session: AsyncSession,
    author_nickname: str,
    content_text: str,
    target_type: str,
    target_id: 'uuid.UUID',
) -> None:
    """Check all personas' preferences and auto-react to new content."""
    import uuid

    personas = _get_all_personas()
    user_repo = UserRepository(session)
    reaction_repo = ReactionRepository(session)

    reacted = 0
    for persona in personas:
        if persona.nickname == author_nickname:
            continue

        if not persona.preferences.likes and not persona.preferences.dislikes:
            continue

        # Check likes
        if persona.preferences.likes and _match_keywords(content_text, persona.preferences.likes):
            reaction_type = "like"
        elif persona.preferences.dislikes and _match_keywords(content_text, persona.preferences.dislikes):
            reaction_type = "dislike"
        else:
            continue

        user = await user_repo.get_by_nickname(persona.nickname)
        if not user:
            continue

        existing = await reaction_repo.get_by_user_and_target(user.id, target_type, target_id)
        if existing:
            continue

        await reaction_repo.create(
            user_id=user.id,
            target_type=target_type,
            target_id=target_id,
            reaction_type=reaction_type,
        )
        reacted += 1

    if reacted > 0:
        await session.flush()
        logger.info("Auto-reacted to %s %s: %d reactions", target_type, target_id, reacted)
