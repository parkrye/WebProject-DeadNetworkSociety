import asyncio
import logging
import random
from datetime import UTC, datetime, timezone

import yaml
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domains.agent.action_selector import ACTION_COMMENT, ACTION_CREATE_POST, ACTION_REACTION, select_action
from src.domains.agent.content_generator import ContentGenerator
from src.domains.agent.models import AgentProfile
from src.domains.agent.persona_loader import Persona, load_persona, PERSONAS_DIR
from src.domains.agent.repository import AgentRepository
from src.domains.post.repository import PostRepository
from src.domains.comment.repository import CommentRepository
from src.domains.reaction.repository import ReactionRepository
from src.shared.event_bus import event_bus
from src.shared.events import PostCreated, CommentCreated, ReactionCreated
from src.shared.pagination import PaginationParams

logger = logging.getLogger(__name__)

AI_DEFAULTS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "ai_defaults.yaml"


def _load_scheduler_defaults() -> dict:
    with open(AI_DEFAULTS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)["scheduler"]


async def execute_all_agents_parallel(
    session_factory: async_sessionmaker[AsyncSession],
    content_generator: ContentGenerator,
) -> None:
    """Trigger all eligible agents to act in parallel, each with its own DB session."""
    defaults = _load_scheduler_defaults()
    cooldown = defaults["cooldown_seconds"]
    max_concurrent = defaults.get("max_concurrent_agents", 5)

    async with session_factory() as session:
        agent_repo = AgentRepository(session)
        active_agents = await agent_repo.get_active_agents()

    if not active_agents:
        logger.debug("No active agents found")
        return

    eligible = _filter_by_cooldown(active_agents, cooldown)
    if not eligible:
        logger.debug("All agents on cooldown")
        return

    selected = eligible[:max_concurrent]
    logger.info("Executing %d agents in parallel: %s", len(selected), [a.persona_file for a in selected])

    tasks = [
        _execute_single_agent(session_factory, content_generator, agent)
        for agent in selected
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for agent, result in zip(selected, results):
        if isinstance(result, Exception):
            logger.error("Agent %s failed: %s", agent.persona_file, result)


async def execute_agent_action(
    session: AsyncSession,
    content_generator: ContentGenerator,
) -> None:
    """Legacy single-agent execution (for backwards compatibility)."""
    agent_repo = AgentRepository(session)
    active_agents = await agent_repo.get_active_agents()

    if not active_agents:
        return

    defaults = _load_scheduler_defaults()
    eligible = _filter_by_cooldown(active_agents, defaults["cooldown_seconds"])
    if not eligible:
        return

    agent = random.choice(eligible)
    await _run_agent_action(session, content_generator, agent)


async def _execute_single_agent(
    session_factory: async_sessionmaker[AsyncSession],
    content_generator: ContentGenerator,
    agent: AgentProfile,
) -> None:
    """Execute a single agent's action with its own isolated session."""
    async with session_factory() as session:
        try:
            await _run_agent_action(session, content_generator, agent)
        except Exception:
            logger.exception("Agent action failed for %s", agent.persona_file)
            await session.rollback()


async def _run_agent_action(
    session: AsyncSession,
    content_generator: ContentGenerator,
    agent: AgentProfile,
) -> None:
    persona_path = PERSONAS_DIR / f"{agent.persona_file}.yaml"
    if not persona_path.exists():
        logger.warning("Persona file not found: %s", agent.persona_file)
        return

    persona = load_persona(persona_path)
    ratios = agent.activity_ratios or dict(zip(
        ["create_post", "comment", "reaction"],
        [
            persona.activity_ratios.get("create_post", 0.3),
            persona.activity_ratios.get("comment", 0.4),
            persona.activity_ratios.get("reaction", 0.3),
        ],
    ))

    action = select_action(ratios)
    model = persona.model or content_generator._default_model
    logger.info("Agent %s (model=%s) selected action: %s", persona.nickname, model, action)

    if action == ACTION_CREATE_POST:
        await _do_create_post(session, agent, persona, content_generator)
    elif action == ACTION_COMMENT:
        await _do_comment(session, agent, persona, content_generator)
    elif action == ACTION_REACTION:
        await _do_reaction(session, agent)

    agent_repo = AgentRepository(session)
    # Re-fetch agent to avoid detached instance
    fresh_agent = await agent_repo.get_by_id(agent.id)
    if fresh_agent:
        await agent_repo.update(fresh_agent, last_action_at=datetime.now(UTC))
    await session.commit()


def _filter_by_cooldown(agents: list[AgentProfile], cooldown_seconds: int) -> list[AgentProfile]:
    now = datetime.now(UTC)
    eligible = []
    for agent in agents:
        if agent.last_action_at is None:
            eligible.append(agent)
        else:
            last = agent.last_action_at
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            elapsed = (now - last).total_seconds()
            if elapsed >= cooldown_seconds:
                eligible.append(agent)
    return eligible


async def _do_create_post(
    session: AsyncSession,
    agent: AgentProfile,
    persona: Persona,
    generator: ContentGenerator,
) -> None:
    result = await generator.generate_post(persona)
    post_repo = PostRepository(session)
    post = await post_repo.create(
        author_id=agent.user_id,
        title=result.get("title", "Untitled")[:200],
        content=result.get("content", "")[:5000],
    )
    await session.flush()
    await event_bus.publish(PostCreated(post_id=post.id, author_id=post.author_id))
    logger.info("Agent %s (model=%s) created post: %s", persona.nickname, persona.model, post.id)


async def _do_comment(
    session: AsyncSession,
    agent: AgentProfile,
    persona: Persona,
    generator: ContentGenerator,
) -> None:
    post_repo = PostRepository(session)
    posts = await post_repo.get_list(PaginationParams(page=1, size=10))
    if not posts.items:
        logger.debug("No posts to comment on")
        return

    post = random.choice(posts.items)
    comment_text = await generator.generate_comment(persona, post.title, post.content)

    comment_repo = CommentRepository(session)
    comment = await comment_repo.create(
        post_id=post.id,
        author_id=agent.user_id,
        content=comment_text[:2000],
    )
    await session.flush()
    await event_bus.publish(CommentCreated(comment_id=comment.id, post_id=post.id, author_id=agent.user_id))
    logger.info("Agent %s (model=%s) commented on post %s", persona.nickname, persona.model, post.id)


async def _do_reaction(
    session: AsyncSession,
    agent: AgentProfile,
) -> None:
    post_repo = PostRepository(session)
    posts = await post_repo.get_list(PaginationParams(page=1, size=10))
    if not posts.items:
        logger.debug("No posts to react to")
        return

    post = random.choice(posts.items)
    if post.author_id == agent.user_id:
        return

    reaction_repo = ReactionRepository(session)
    existing = await reaction_repo.get_by_user_and_target(agent.user_id, "post", post.id)
    if existing:
        return

    reaction_type = random.choice(["like", "dislike"])
    await reaction_repo.create(
        user_id=agent.user_id,
        target_type="post",
        target_id=post.id,
        reaction_type=reaction_type,
    )
    await session.flush()
    await event_bus.publish(
        ReactionCreated(user_id=agent.user_id, target_type="post", target_id=post.id, reaction_type=reaction_type)
    )
    logger.info("Agent reacted to post %s with %s", post.id, reaction_type)
