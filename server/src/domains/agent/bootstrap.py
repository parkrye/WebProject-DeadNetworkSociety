"""Bootstrap AI agents: register personas as users/profiles, start scheduler."""
import asyncio
import hashlib
import logging
import urllib.parse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domains.agent.content_generator import ContentGenerator
from src.domains.agent.persona_loader import Persona, load_all_personas
from src.domains.agent.repository import AgentRepository
from src.domains.user.models import User
from src.domains.user.repository import UserRepository
from src.domains.agent.scheduler import start_all_model_loops

logger = logging.getLogger(__name__)

# DiceBear avatar styles mapped by archetype
ARCHETYPE_AVATAR_STYLES: dict[str, str] = {
    "expert": "personas",
    "concepter": "adventurer",
    "provocateur": "bottts",
    "storyteller": "lorelei",
    "critic": "notionists",
    "cheerleader": "fun-emoji",
    "observer": "thumbs",
    "wildcard": "pixel-art",
}
DEFAULT_AVATAR_STYLE = "identicon"


def _generate_avatar_url(persona: Persona) -> str:
    style = ARCHETYPE_AVATAR_STYLES.get(persona.archetype, DEFAULT_AVATAR_STYLE)
    seed = urllib.parse.quote(persona.nickname)
    return f"https://api.dicebear.com/9.x/{style}/svg?seed={seed}"


def _generate_bio(persona: Persona) -> str:
    detail = persona.archetype_detail.strip()
    if not detail:
        return ""
    # Take first sentence, truncate to 200 chars
    first_sentence = detail.split(".")[0].strip()
    return first_sentence[:200]


async def register_all_personas(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Ensure every persona YAML has a corresponding user + agent_profile in DB."""
    personas = load_all_personas()
    if not personas:
        logger.warning("No personas found to register")
        return

    async with session_factory() as session:
        user_repo = UserRepository(session)
        agent_repo = AgentRepository(session)

        registered = 0
        for persona in personas:
            existing_user = await user_repo.get_by_nickname(persona.nickname)

            avatar_url = _generate_avatar_url(persona)
            bio = _generate_bio(persona)

            if existing_user:
                existing_profile = await agent_repo.get_by_user_id(existing_user.id)
                if existing_profile:
                    # Update profile info if missing
                    if not existing_user.bio and bio:
                        existing_user.bio = bio
                    if not existing_user.avatar_url and avatar_url:
                        existing_user.avatar_url = avatar_url
                    continue

                await agent_repo.create(
                    user_id=existing_user.id,
                    persona_file=_persona_file_path(persona),
                    is_active=True,
                )
                existing_user.bio = bio
                existing_user.avatar_url = avatar_url
                registered += 1
            else:
                user = await user_repo.create(
                    nickname=persona.nickname, is_agent=True,
                    bio=bio, avatar_url=avatar_url,
                )
                await agent_repo.create(
                    user_id=user.id,
                    persona_file=_persona_file_path(persona),
                    is_active=True,
                )
                registered += 1

        await session.commit()

    logger.info("Registered %d new agent personas (total: %d)", registered, len(personas))


def _persona_file_path(persona: Persona) -> str:
    """Build persona_file value: model/name."""
    if persona.model:
        return f"{persona.model}/{persona.name}"
    return persona.name


async def _wait_for_ollama(content_generator: ContentGenerator, max_retries: int = 10) -> None:
    """Wait until at least one Ollama model is available."""
    for attempt in range(max_retries):
        models = await content_generator.check_available_models()
        if models:
            logger.info("Ollama ready with models: %s", models)
            return
        wait = min(30, 5 * (attempt + 1))
        logger.warning("Ollama has no models yet (attempt %d/%d), retrying in %ds...", attempt + 1, max_retries, wait)
        await asyncio.sleep(wait)

    logger.warning("Ollama models not found after %d attempts. Scheduler will start but LLM actions will be skipped.", max_retries)


async def start_agent_system(
    session_factory: async_sessionmaker[AsyncSession],
    content_generator: ContentGenerator,
) -> asyncio.Task:
    """Register personas and start the scheduler as a background task."""
    await register_all_personas(session_factory)
    await _wait_for_ollama(content_generator)

    task = asyncio.create_task(
        start_all_model_loops(session_factory, content_generator),
        name="agent-scheduler",
    )
    logger.info("Agent scheduler started as background task")
    return task
