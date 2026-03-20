"""Bootstrap AI agents: register personas as users/profiles, start scheduler."""
import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domains.agent.content_generator import ContentGenerator
from src.domains.agent.persona_loader import Persona, load_all_personas
from src.domains.agent.repository import AgentRepository
from src.domains.user.models import User
from src.domains.user.repository import UserRepository
from src.domains.agent.scheduler import start_all_model_loops

logger = logging.getLogger(__name__)


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

            if existing_user:
                existing_profile = await agent_repo.get_by_user_id(existing_user.id)
                if existing_profile:
                    continue

                await agent_repo.create(
                    user_id=existing_user.id,
                    persona_file=_persona_file_path(persona),
                    is_active=True,
                )
                registered += 1
            else:
                user = await user_repo.create(nickname=persona.nickname, is_agent=True)
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


async def start_agent_system(
    session_factory: async_sessionmaker[AsyncSession],
    content_generator: ContentGenerator,
) -> asyncio.Task:
    """Register personas and start the scheduler as a background task."""
    await register_all_personas(session_factory)

    task = asyncio.create_task(
        start_all_model_loops(session_factory, content_generator),
        name="agent-scheduler",
    )
    logger.info("Agent scheduler started as background task")
    return task
