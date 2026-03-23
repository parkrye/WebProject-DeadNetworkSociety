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
from src.domains.agent.auto_reaction import auto_react_to_content, evaluate_auto_follow
from src.domains.agent.social_dynamics import run_social_dynamics_cycle
from src.domains.follow.repository import FollowRepository
from src.domains.agent.content_generator import ContentGenerator, ContentQualityError, OllamaUnavailableError
from src.domains.agent.quick_reaction_pool import QuickReactionPool
from src.domains.agent.status_store import update_status
from src.domains.agent.persona_loader import Persona, load_personas_by_model
from src.domains.agent.target_selector import get_affinity_tracker, select_post, select_comment
from src.domains.post.models import Post
from src.domains.post.repository import PopularPostRepository, PostMetadataRepository, PostRepository
from src.domains.comment.models import Comment
from src.domains.comment.repository import CommentRepository
from src.domains.reaction.models import Reaction
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
        except ContentQualityError:
            logger.warning(
                "Content quality check failed for %s by %s, skipping this action",
                action.action_type, action.persona.nickname,
            )
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

    # Refresh popular posts queue after each action set
    try:
        async with session_factory() as session:
            popular_repo = PopularPostRepository(session)
            await popular_repo.refresh()
            await session.commit()
    except Exception:
        logger.exception("Failed to refresh popular posts")


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

    # Run social dynamics cycle (interest contagion, mood decay, random perturbation)
    await run_social_dynamics_cycle(session, user.id, persona.nickname, persona.topics)

    await session.commit()
    update_status(persona.nickname, "대기")


async def _find_self_post_comment(
    post_repo: PostRepository,
    comment_repo: CommentRepository,
    user_id: 'uuid.UUID',
    persona: Persona,
) -> tuple:
    """Find an unanswered comment on the persona's own post. Returns (post, comment) or (None, None)."""
    import uuid as _uuid

    own_posts = await post_repo.get_recent_by_author(user_id, limit=5)
    if not own_posts:
        return None, None

    for post in own_posts:
        comments = await comment_repo.get_by_post(post.id, PaginationParams(page=1, size=20))
        if not comments.items:
            continue

        # Find comments by others that the persona hasn't replied to
        other_comments = [c for c in comments.items if c.author_id != user_id and c.depth == 0]
        replied_parent_ids = {c.parent_id for c in comments.items if c.author_id == user_id and c.parent_id}

        unanswered = [c for c in other_comments if c.id not in replied_parent_ids]
        if unanswered:
            return post, random.choice(unanswered)

    return None, None


async def _collect_engagement(session: AsyncSession, posts: list[Post]) -> dict:
    """Collect comment and reaction counts for posts."""
    from sqlalchemy import func, select
    import uuid as _uuid

    post_ids = [p.id for p in posts]
    if not post_ids:
        return {}

    # Comment counts
    comment_stmt = (
        select(Comment.post_id, func.count().label("cnt"))
        .where(Comment.post_id.in_(post_ids))
        .group_by(Comment.post_id)
    )
    comment_result = await session.execute(comment_stmt)
    comment_counts = {row[0]: row[1] for row in comment_result.all()}

    # Reaction counts (likes and dislikes)
    like_stmt = (
        select(Reaction.target_id, func.count().label("cnt"))
        .where(Reaction.target_type == "post", Reaction.target_id.in_(post_ids), Reaction.reaction_type == "like")
        .group_by(Reaction.target_id)
    )
    dislike_stmt = (
        select(Reaction.target_id, func.count().label("cnt"))
        .where(Reaction.target_type == "post", Reaction.target_id.in_(post_ids), Reaction.reaction_type == "dislike")
        .group_by(Reaction.target_id)
    )
    like_result = await session.execute(like_stmt)
    like_counts = {row[0]: row[1] for row in like_result.all()}
    dislike_result = await session.execute(dislike_stmt)
    dislike_counts = {row[0]: row[1] for row in dislike_result.all()}

    return {
        pid: (comment_counts.get(pid, 0), like_counts.get(pid, 0), dislike_counts.get(pid, 0))
        for pid in post_ids
    }


async def _get_following_ids(session: AsyncSession, user_id: 'uuid.UUID') -> set:
    follow_repo = FollowRepository(session)
    return await follow_repo.get_following_ids(user_id)


async def _get_sentiments(session: AsyncSession, user_id: 'uuid.UUID', author_ids: set) -> dict:
    follow_repo = FollowRepository(session)
    return await follow_repo.get_sentiments_for_authors(user_id, author_ids)


async def _collect_author_nicknames(session: AsyncSession, author_ids: set) -> dict:
    """Map author UUIDs to nicknames."""
    user_repo = UserRepository(session)
    result = {}
    for aid in author_ids:
        user = await user_repo.get_by_id(aid)
        if user:
            result[aid] = user.nickname
    return result


async def _fetch_popular_context(session: AsyncSession, persona: Persona) -> str:
    """Fetch popular posts from the popular_posts queue as RAG context."""
    from sqlalchemy import select as sa_select
    from src.domains.post.models import PopularPost as PP

    stmt = (
        sa_select(Post.title, Post.content)
        .join(PP, Post.id == PP.post_id)
        .order_by(PP.popularity_score.desc())
        .limit(3)
    )
    result = await session.execute(stmt)
    rows = result.all()
    if not rows:
        return ""

    blocks = [f"- {r.title}: {r.content}" for r in rows]
    return (
        "\n\n[참고: 커뮤니티 인기글]\n"
        + "\n".join(blocks)
        + "\n위 인기글을 참고하되, 당신만의 관점으로 재해석하세요."
    )


async def _do_create_post(
    session: AsyncSession,
    user_id: 'uuid.UUID',
    persona: Persona,
    generator: ContentGenerator,
) -> None:
    popular_context = await _fetch_popular_context(session, persona)
    result = await generator.generate_post(persona, popular_context=popular_context)
    post_repo = PostRepository(session)
    post = await post_repo.create(
        author_id=user_id,
        title=result["title"][:30],
        content=result["content"][:140],
    )
    await session.flush()

    # Save generation metadata
    import json as _json
    meta_repo = PostMetadataRepository(session)
    await meta_repo.create(
        post_id=post.id,
        persona_nickname=persona.nickname,
        model_used=result.get("_model", ""),
        template_tier=result.get("_tier", ""),
        rag_context_summary=_json.dumps(result.get("_rag_topics", []), ensure_ascii=False),
    )

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

    author_ids = {p.author_id for p in posts.items}
    author_nicknames = await _collect_author_nicknames(session, author_ids)
    engagement_data = await _collect_engagement(session, posts.items)

    following_ids = await _get_following_ids(session, user_id)
    sentiments = await _get_sentiments(session, user_id, author_ids)
    post = select_post(persona, posts.items, author_nicknames, engagement_data, following_ids, sentiments)
    if not post:
        return

    await post_repo.increment_view_count(post.id)

    post_author_name = author_nicknames.get(post.author_id, "알 수 없음")

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

    # Track affinity + evaluate follow
    get_affinity_tracker().record(persona.nickname, post_author_name)
    await evaluate_auto_follow(session, persona.nickname, post_author_name, user_id, post.author_id)

    await auto_react_to_content(session, persona.nickname, comment_text, "comment", comment.id)

    logger.info("[%s] Commented on post %s (topic-weighted)", persona.nickname, post.id)


async def _do_reply(
    session: AsyncSession,
    user_id: 'uuid.UUID',
    persona: Persona,
    generator: ContentGenerator,
) -> None:
    post_repo = PostRepository(session)
    comment_repo = CommentRepository(session)

    # Priority: reply to comments on own posts first
    post, parent = await _find_self_post_comment(post_repo, comment_repo, user_id, persona)

    if not post:
        # Fallback: normal weighted selection
        posts = await post_repo.get_list(PaginationParams(page=1, size=persona.recent_scope))
        if not posts.items:
            return

        author_ids = {p.author_id for p in posts.items}
        author_nicknames = await _collect_author_nicknames(session, author_ids)
        engagement_data = await _collect_engagement(session, posts.items)

        following_ids = await _get_following_ids(session, user_id)
        post = select_post(persona, posts.items, author_nicknames, engagement_data, following_ids)
        if not post:
            return

        comments = await comment_repo.get_by_post(post.id, PaginationParams(page=1, size=persona.recent_scope))
        if not comments.items:
            return

        comment_author_ids = {c.author_id for c in comments.items}
        comment_author_nicks = await _collect_author_nicknames(session, comment_author_ids)
        parent = select_comment(persona, comments.items, comment_author_nicks)
        if not parent:
            return

    await post_repo.increment_view_count(post.id)

    user_repo = UserRepository(session)
    post_author = await user_repo.get_by_id(post.author_id)
    post_author_name = post_author.nickname if post_author else "알 수 없음"
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

    # Track affinity for both post author and comment author
    tracker = get_affinity_tracker()
    tracker.record(persona.nickname, post_author_name)
    tracker.record(persona.nickname, comment_author_name)
    await evaluate_auto_follow(session, persona.nickname, post_author_name, user_id, post.author_id)
    if parent.author_id != post.author_id:
        _user_repo = UserRepository(session)
        comment_author_user = await _user_repo.get_by_nickname(comment_author_name)
        if comment_author_user:
            await evaluate_auto_follow(session, persona.nickname, comment_author_name, user_id, comment_author_user.id)

    await auto_react_to_content(session, persona.nickname, reply_text, "comment", reply.id)

    logger.info("[%s] Replied to %s's comment on %s's post (affinity-weighted)", persona.nickname, comment_author_name, post_author_name)


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

    author_ids = {p.author_id for p in posts.items}
    author_nicknames = await _collect_author_nicknames(session, author_ids)
    engagement_data = await _collect_engagement(session, posts.items)

    following_ids = await _get_following_ids(session, user_id)
    sentiments = await _get_sentiments(session, user_id, author_ids)
    post = select_post(persona, posts.items, author_nicknames, engagement_data, following_ids, sentiments)
    if not post:
        return

    await post_repo.increment_view_count(post.id)

    reaction_text = _quick_reaction_pool.pick(persona.archetype)

    comment_repo = CommentRepository(session)
    comment = await comment_repo.create(
        post_id=post.id,
        author_id=user_id,
        content=reaction_text,
    )
    await session.flush()
    await event_bus.publish(CommentCreated(comment_id=comment.id, post_id=post.id, author_id=user_id))

    # Track affinity
    post_author_name = author_nicknames.get(post.author_id, "")
    if post_author_name:
        get_affinity_tracker().record(persona.nickname, post_author_name)

    logger.info("[%s] Quick reaction on post %s: %s", persona.nickname, post.id, reaction_text)
