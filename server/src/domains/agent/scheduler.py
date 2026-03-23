import asyncio
import logging
import random
from datetime import UTC, datetime

import yaml
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domains.agent.action_selector import (
    ACTION_COMMENT,
    ACTION_CREATE_POST,
    ACTION_QUICK_REACT,
    ACTION_REPLY,
    AgentAction,
    generate_action_set,
)
from src.domains.agent.auto_reaction import auto_react_to_content
from src.domains.agent.content_generator import ContentGenerator, OllamaUnavailableError
from src.domains.agent.quick_reaction_pool import QuickReactionPool
from src.domains.agent.status_store import update_status
from src.domains.agent.persona_loader import Persona, load_personas_by_model
from src.domains.post.repository import PostRepository
from src.domains.comment.repository import CommentRepository
from src.domains.user.repository import UserRepository
from src.shared.event_bus import event_bus
from src.shared.events import PostCreated, CommentCreated
from src.shared.pagination import PaginationParams

logger = logging.getLogger(__name__)

AI_DEFAULTS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "ai_defaults.yaml"


def _load_scheduler_defaults() -> dict:
    with open(AI_DEFAULTS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)["scheduler"]


_quick_reaction_pool = QuickReactionPool()


async def start_all_model_loops(
    session_factory: async_sessionmaker[AsyncSession],
    content_generator: ContentGenerator,
) -> None:
    grouped = load_personas_by_model()
    if not grouped:
        logger.warning("No personas found")
        return

    tasks = [
        model_loop(model, personas, session_factory, content_generator)
        for model, personas in grouped.items()
    ]

    logger.info(
        "Starting %d model loops: %s",
        len(tasks),
        {model: len(personas) for model, personas in grouped.items()},
    )

    await asyncio.gather(*tasks, return_exceptions=True)


async def model_loop(
    model: str,
    personas: list[Persona],
    session_factory: async_sessionmaker[AsyncSession],
    content_generator: ContentGenerator,
) -> None:
    defaults = _load_scheduler_defaults()
    interval_min = defaults["interval_min_seconds"]
    interval_max = defaults["interval_max_seconds"]

    logger.info(
        "Model loop started: %s with %d personas (total actions/set: %d)",
        model, len(personas), sum(p.activity_level for p in personas),
    )

    while True:
        try:
            action_set = generate_action_set(personas)
            logger.info("Model %s: executing set of %d actions", model, len(action_set))

            await execute_action_set(action_set, session_factory, content_generator)

            delay = random.randint(interval_min, interval_max)
            logger.info("Model %s: set complete, waiting %ds before next set", model, delay)
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            logger.info("Model loop %s cancelled", model)
            break
        except Exception:
            logger.exception("Model loop %s error, retrying after cooldown", model)
            await asyncio.sleep(interval_max)


async def execute_action_set(
    action_set: list[AgentAction],
    session_factory: async_sessionmaker[AsyncSession],
    content_generator: ContentGenerator,
) -> None:
    for action in action_set:
        try:
            async with session_factory() as session:
                await _execute_action(session, action, content_generator)
        except OllamaUnavailableError:
            logger.warning(
                "Ollama unavailable for %s by %s, skipping remaining LLM actions in set",
                action.action_type, action.persona.nickname,
            )
            break
        except Exception:
            logger.exception(
                "Action failed: %s by %s",
                action.action_type, action.persona.nickname,
            )


ACTION_TYPE_LABELS = {
    ACTION_CREATE_POST: "게시글 작성 중",
    ACTION_COMMENT: "댓글 작성 중",
    ACTION_REPLY: "답글 작성 중",
    ACTION_QUICK_REACT: "짧은 반응 중",
}

NEEDS_POSTS = {ACTION_COMMENT, ACTION_REPLY, ACTION_QUICK_REACT}


async def _execute_action(
    session: AsyncSession,
    action: AgentAction,
    content_generator: ContentGenerator,
) -> None:
    persona = action.persona

    user_repo = UserRepository(session)
    user = await user_repo.get_by_nickname(persona.nickname)
    if not user:
        logger.warning("User not found for persona %s, skipping", persona.nickname)
        return

    if action.action_type in NEEDS_POSTS:
        post_repo = PostRepository(session)
        posts = await post_repo.get_list(PaginationParams(page=1, size=1))
        if not posts.items:
            logger.info("[%s] No posts yet, switching %s -> create_post", persona.nickname, action.action_type)
            action = AgentAction(persona=persona, action_type=ACTION_CREATE_POST)

    status_label = ACTION_TYPE_LABELS.get(action.action_type, "활동 중")
    update_status(persona.nickname, status_label)

    if action.action_type == ACTION_CREATE_POST:
        await _do_create_post(session, user.id, persona, content_generator)
    elif action.action_type == ACTION_COMMENT:
        await _do_comment(session, user.id, persona, content_generator)
    elif action.action_type == ACTION_REPLY:
        await _do_reply(session, user.id, persona, content_generator)
    elif action.action_type == ACTION_QUICK_REACT:
        await _do_quick_react(session, user.id, persona)

    await session.commit()
    update_status(persona.nickname, "대기")


async def _do_create_post(
    session: AsyncSession,
    user_id: 'uuid.UUID',
    persona: Persona,
    generator: ContentGenerator,
) -> None:
    result = await generator.generate_post(persona)
    post_repo = PostRepository(session)
    post = await post_repo.create(
        author_id=user_id,
        title=result.get("title", "Untitled")[:200],
        content=result.get("content", "")[:5000],
    )
    await session.flush()
    await event_bus.publish(PostCreated(post_id=post.id, author_id=post.author_id))

    # Auto-react: other personas like/dislike based on preferences
    content_text = f"{post.title} {result.get('content', '')}"
    await auto_react_to_content(session, persona.nickname, content_text, "post", post.id)

    logger.info("[%s] Created post: %s", persona.nickname, post.title[:50])


async def _do_comment(
    session: AsyncSession,
    user_id: 'uuid.UUID',
    persona: Persona,
    generator: ContentGenerator,
) -> None:
    post_repo = PostRepository(session)
    posts = await post_repo.get_list(PaginationParams(page=1, size=persona.recent_scope))
    if not posts.items:
        return

    post = random.choice(posts.items)

    # Get post author nickname
    user_repo = UserRepository(session)
    post_author = await user_repo.get_by_id(post.author_id)
    post_author_name = post_author.nickname if post_author else "알 수 없음"

    comment_text = await generator.generate_comment(
        persona, post.title, post.content, post_author_name,
    )

    comment_repo = CommentRepository(session)
    comment = await comment_repo.create(
        post_id=post.id,
        author_id=user_id,
        content=comment_text[:2000],
    )
    await session.flush()
    await event_bus.publish(CommentCreated(comment_id=comment.id, post_id=post.id, author_id=user_id))

    await auto_react_to_content(session, persona.nickname, comment_text, "comment", comment.id)

    logger.info("[%s] Commented on post %s", persona.nickname, post.id)


async def _do_reply(
    session: AsyncSession,
    user_id: 'uuid.UUID',
    persona: Persona,
    generator: ContentGenerator,
) -> None:
    post_repo = PostRepository(session)
    posts = await post_repo.get_list(PaginationParams(page=1, size=persona.recent_scope))
    if not posts.items:
        return

    post = random.choice(posts.items)

    # Get post author
    user_repo = UserRepository(session)
    post_author = await user_repo.get_by_id(post.author_id)
    post_author_name = post_author.nickname if post_author else "알 수 없음"

    comment_repo = CommentRepository(session)
    comments = await comment_repo.get_by_post(post.id, PaginationParams(page=1, size=persona.recent_scope))
    if not comments.items:
        return

    parent = random.choice(comments.items)

    # Get comment author
    comment_author = await user_repo.get_by_id(parent.author_id)
    comment_author_name = comment_author.nickname if comment_author else "알 수 없음"

    reply_text = await generator.generate_reply(
        persona, post.title, post.content, post_author_name,
        parent.content, comment_author_name,
    )

    reply = await comment_repo.create(
        post_id=post.id,
        author_id=user_id,
        content=reply_text[:2000],
        parent_id=parent.id,
        depth=parent.depth + 1,
    )
    await session.flush()
    await event_bus.publish(CommentCreated(comment_id=reply.id, post_id=post.id, author_id=user_id))

    await auto_react_to_content(session, persona.nickname, reply_text, "comment", reply.id)

    logger.info("[%s] Replied to %s's comment on %s's post", persona.nickname, comment_author_name, post_author_name)


async def _do_quick_react(
    session: AsyncSession,
    user_id: 'uuid.UUID',
    persona: Persona,
) -> None:
    """Post a quick reaction comment (no LLM call) from the archetype reaction pool."""
    post_repo = PostRepository(session)
    posts = await post_repo.get_list(PaginationParams(page=1, size=persona.recent_scope))
    if not posts.items:
        return

    post = random.choice(posts.items)
    reaction_text = _quick_reaction_pool.pick(persona.archetype)

    comment_repo = CommentRepository(session)
    comment = await comment_repo.create(
        post_id=post.id,
        author_id=user_id,
        content=reaction_text,
    )
    await session.flush()
    await event_bus.publish(CommentCreated(comment_id=comment.id, post_id=post.id, author_id=user_id))

    logger.info("[%s] Quick reaction on post %s: %s", persona.nickname, post.id, reaction_text)
