import asyncio
import logging
import random
from datetime import UTC, datetime

import yaml
from pathlib import Path

from sqlalchemy import select
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
from src.domains.agent.content_generator import ContentGenerator, ContentQualityError, OllamaUnavailableError
from src.domains.agent.quick_reaction_pool import QuickReactionPool
from src.domains.agent.status_store import update_status
from src.domains.agent.persona_loader import Persona, load_personas_by_model
from src.domains.agent.target_selector import select_post, select_comment
from src.domains.follow.models import PersonaRelationship
from src.domains.follow.repository import FollowRepository, PersonaMemoryRepository, PersonaRelationshipRepository
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

    # Refresh popular posts + trending keywords after each action set
    try:
        async with session_factory() as session:
            popular_repo = PopularPostRepository(session)
            await popular_repo.refresh()
            from src.domains.post.repository import TrendingKeywordRepository
            keyword_repo = TrendingKeywordRepository(session)
            await keyword_repo.refresh()
            await session.commit()
    except Exception:
        logger.exception("Failed to refresh popular posts/keywords")


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
    rel_repo = PersonaRelationshipRepository(session)
    return await rel_repo.get_sentiments_for_authors(user_id, author_ids)


async def _get_affinities(session: AsyncSession, user_id: 'uuid.UUID', author_ids: set) -> dict:
    rel_repo = PersonaRelationshipRepository(session)
    return await rel_repo.get_affinities_for_authors(user_id, author_ids)


async def _build_relationship_hint(
    session: AsyncSession, actor_id: 'uuid.UUID', target_id: 'uuid.UUID', target_nickname: str,
) -> str:
    """Build a rich relationship context for the LLM prompt."""
    if actor_id == target_id:
        return ""
    follow_repo = FollowRepository(session)
    rel_repo = PersonaRelationshipRepository(session)
    mem_repo = PersonaMemoryRepository(session)

    is_following = await follow_repo.is_following(actor_id, target_id)
    is_followed_by = await follow_repo.is_following(target_id, actor_id)

    rel_stmt = select(PersonaRelationship).where(
        PersonaRelationship.actor_id == actor_id,
        PersonaRelationship.target_id == target_id,
    )
    rel_result = await session.execute(rel_stmt)
    rel = rel_result.scalar_one_or_none()

    parts = []

    # Follow status
    if is_following and is_followed_by:
        parts.append(f"당신과 {target_nickname}은(는) 서로 팔로우하는 사이입니다.")
    elif is_following:
        parts.append(f"당신은 {target_nickname}을(를) 팔로우하고 있습니다.")
    elif is_followed_by:
        parts.append(f"{target_nickname}이(가) 당신을 팔로우하고 있습니다.")

    # Interaction stats
    if rel:
        if rel.like_count > 0 or rel.dislike_count > 0:
            parts.append(f"그동안 {target_nickname}의 글에 좋아요 {rel.like_count}회, 싫어요 {rel.dislike_count}회를 남겼습니다.")
        if rel.sentiment_score > 0.3:
            parts.append("호감을 느끼고 있으니 친근하게 반응하세요.")
        elif rel.sentiment_score < -0.3:
            parts.append("불만을 느끼고 있으니 비판적으로 반응하세요.")

    # Memories
    memory_text = await mem_repo.format_memories_for_prompt(actor_id, target_id, target_nickname)
    if memory_text:
        parts.append(memory_text)

    if not parts:
        return ""
    return "\n".join(parts)


async def _collect_author_nicknames(session: AsyncSession, author_ids: set) -> dict:
    """Map author UUIDs to nicknames."""
    user_repo = UserRepository(session)
    result = {}
    for aid in author_ids:
        user = await user_repo.get_by_id(aid)
        if user:
            result[aid] = user.nickname
    return result


async def _fetch_live_search_context(persona: Persona) -> str:
    """Search the web for persona's topics and return formatted context."""
    from src.domains.agent.live_search import get_live_search
    try:
        searcher = get_live_search()
        keywords = random.sample(persona.topics, min(2, len(persona.topics)))
        results = await searcher.search(keywords, max_total=3)
        return searcher.format_as_context(results)
    except Exception:
        logger.debug("Live search failed for %s", persona.nickname)
        return ""


async def _fetch_popular_context(
    session: AsyncSession, persona: Persona, user_id: 'uuid.UUID | None' = None,
) -> tuple[str, list[str]]:
    """Fetch popular posts + trending keywords + live search + knowledge graph. Returns (context, keywords)."""
    from src.domains.agent.knowledge_graph import KnowledgeGraphRepository
    from src.domains.agent.live_search import get_live_search
    from src.domains.post.models import PopularPost as PP, TrendingKeyword
    import re

    parts = []
    collected_keywords: list[str] = []

    # Persona topics as base keywords
    collected_keywords.extend(persona.topics[:2])

    # Knowledge graph: inject persona's known connections
    if user_id:
        kg = KnowledgeGraphRepository(session)
        kg_context = await kg.format_for_prompt(user_id, persona.topics[:3])
        if kg_context:
            parts.append(kg_context)

    # Trending keywords
    kw_result = await session.execute(
        select(TrendingKeyword.keyword, TrendingKeyword.count)
        .order_by(TrendingKeyword.count.desc())
        .limit(10)
    )
    keywords = kw_result.all()
    if keywords:
        kw_list = ", ".join(f"{r.keyword}({r.count})" for r in keywords)
        parts.append(f"[현재 인기 키워드] {kw_list}")
        # Pick top 2 trending as keywords
        for r in keywords[:2]:
            if r.keyword not in collected_keywords:
                collected_keywords.append(r.keyword)

    # Live web search
    live_context = await _fetch_live_search_context(persona)
    if live_context:
        parts.append(live_context)
        # Extract keywords from search results (first noun-like words)
        korean_words = re.findall(r'[가-힣]{2,}', live_context)
        for w in korean_words[:3]:
            if w not in collected_keywords and len(w) >= 2:
                collected_keywords.append(w)
                break

    # Popular posts
    stmt = (
        select(Post.title, Post.content, Post.keywords)
        .join(PP, Post.id == PP.post_id)
        .order_by(PP.popularity_score.desc())
        .limit(3)
    )
    result = await session.execute(stmt)
    rows = result.all()
    if rows:
        blocks = [f"- {r.title}: {r.content}" for r in rows]
        parts.append("[커뮤니티 인기글]\n" + "\n".join(blocks))
        # Extract keywords from popular post keywords
        import json
        for r in rows:
            try:
                post_kws = json.loads(r.keywords) if r.keywords else []
                for kw in post_kws[:1]:
                    if kw not in collected_keywords:
                        collected_keywords.append(kw)
            except (json.JSONDecodeError, TypeError):
                pass

    context = ""
    if parts:
        context = "\n\n" + "\n".join(parts) + "\n위 트렌드/최신정보/인기글을 참고하되, 당신만의 관점으로 재해석하세요."

    return context, collected_keywords[:8]


async def _create_mention_post(
    session: AsyncSession, user_id: 'uuid.UUID', persona: Persona, generator: ContentGenerator,
) -> dict[str, str]:
    """Create a post mentioning/targeting a specific persona based on relationship."""
    rel_result = await session.execute(
        select(PersonaRelationship.target_id, PersonaRelationship.sentiment_score)
        .where(PersonaRelationship.actor_id == user_id, PersonaRelationship.interaction_count >= 2)
        .order_by(PersonaRelationship.interaction_count.desc())
        .limit(5)
    )
    candidates = rel_result.all()
    if not candidates:
        return await generator.generate_post(persona)

    target_row = random.choice(candidates)
    target_id = target_row.target_id

    user_repo = UserRepository(session)
    target_user = await user_repo.get_by_id(target_id)
    if not target_user:
        return await generator.generate_post(persona)

    mem_repo = PersonaMemoryRepository(session)
    memory_text = await mem_repo.format_memories_for_prompt(user_id, target_id, target_user.nickname)
    rel_hint = await _build_relationship_hint(session, user_id, target_id, target_user.nickname)
    live_context = await _fetch_live_search_context(persona)
    mention_context = "\n".join(filter(None, [rel_hint, memory_text, live_context]))

    return await generator.generate_mention_post(persona, target_user.nickname, mention_context)


async def _create_followup_post(
    session: AsyncSession, user_id: 'uuid.UUID', persona: Persona, generator: ContentGenerator,
) -> dict[str, str]:
    """Create a follow-up post based on a previous post (own or popular)."""
    post_repo = PostRepository(session)

    live_context = await _fetch_live_search_context(persona)

    # 50% chance: follow up own post, 50%: follow up a popular/recent post
    if random.random() < 0.5:
        own_posts = await post_repo.get_recent_by_author(user_id, limit=5)
        if own_posts:
            prev = random.choice(own_posts)
            return await generator.generate_followup_post(persona, prev.title, prev.content, popular_context=live_context)

    recent = await post_repo.get_list(PaginationParams(page=1, size=10))
    if recent.items:
        prev = random.choice(recent.items)
        return await generator.generate_followup_post(persona, prev.title, prev.content, popular_context=live_context)

    return await generator.generate_post(persona)


async def _pick_post_type(session: AsyncSession, user_id: 'uuid.UUID', persona: Persona) -> str:
    """Randomly select post type: topic (60%), mention (20%), followup (20%)."""
    roll = random.random()
    if roll < 0.6:
        return "topic"

    if roll < 0.8:
        # mention: only if we have relationship data with someone
        rel_result = await session.execute(
            select(PersonaRelationship.target_id)
            .where(PersonaRelationship.actor_id == user_id, PersonaRelationship.interaction_count >= 2)
            .limit(5)
        )
        if rel_result.all():
            return "mention"
        return "topic"

    # followup: only if we have previous posts
    post_repo = PostRepository(session)
    own_posts = await post_repo.get_recent_by_author(user_id, limit=1)
    if own_posts:
        return "followup"
    return "topic"


async def _do_create_post(
    session: AsyncSession,
    user_id: 'uuid.UUID',
    persona: Persona,
    generator: ContentGenerator,
) -> None:
    import json as _json

    post_type = await _pick_post_type(session, user_id, persona)
    context_keywords: list[str] = []

    if post_type == "mention":
        result = await _create_mention_post(session, user_id, persona, generator)
        context_keywords = list(persona.topics[:2])
    elif post_type == "followup":
        result = await _create_followup_post(session, user_id, persona, generator)
        context_keywords = list(persona.topics[:2])
    else:
        popular_context, context_keywords = await _fetch_popular_context(session, persona, user_id)
        result = await generator.generate_post(persona, popular_context=popular_context)

    keywords_json = _json.dumps(context_keywords, ensure_ascii=False)
    post_repo = PostRepository(session)
    post = await post_repo.create(
        author_id=user_id,
        title=result["title"][:30],
        content=result["content"][:140],
        keywords=keywords_json,
    )
    await session.flush()

    # Save generation metadata
    meta_repo = PostMetadataRepository(session)
    await meta_repo.create(
        post_id=post.id,
        persona_nickname=persona.nickname,
        model_used=result.get("_model", ""),
        template_tier=result.get("_tier", ""),
        rag_context_summary=_json.dumps(result.get("_rag_topics", []), ensure_ascii=False),
    )

    await event_bus.publish(PostCreated(post_id=post.id, author_id=post.author_id))

    # Strengthen knowledge graph with post keywords
    from src.domains.agent.knowledge_graph import KnowledgeGraphRepository, WEIGHT_POST_AUTHOR
    kg = KnowledgeGraphRepository(session)
    await kg.strengthen_edges(user_id, context_keywords, weight_delta=WEIGHT_POST_AUTHOR)

    # Auto-react: other personas like/dislike based on preferences
    content_text = f"{post.title} {result.get('content', '')}"
    await auto_react_to_content(session, persona.nickname, content_text, "post", post.id, target_keywords=context_keywords)

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
    affinities = await _get_affinities(session, user_id, author_ids)
    post = select_post(persona, posts.items, author_nicknames, engagement_data, following_ids, sentiments, affinities)
    if not post:
        return

    await post_repo.increment_view_count(post.id)

    post_author_name = author_nicknames.get(post.author_id, "알 수 없음")
    rel_hint = await _build_relationship_hint(session, user_id, post.author_id, post_author_name)

    comment_text = await generator.generate_comment(
        persona, post.title, post.content, post_author_name,
        relationship_hint=rel_hint,
    )

    import json as _json2, re as _re2
    comment_kws = list(persona.topics[:1])
    post_words = _re2.findall(r'[가-힣]{2,}', post.title)
    for w in post_words[:2]:
        if w not in comment_kws:
            comment_kws.append(w)

    comment_repo = CommentRepository(session)
    comment = await comment_repo.create(
        post_id=post.id,
        author_id=user_id,
        content=comment_text[:2000],
        keywords=_json2.dumps(comment_kws, ensure_ascii=False),
    )
    await session.flush()
    await event_bus.publish(CommentCreated(comment_id=comment.id, post_id=post.id, author_id=user_id))

    # Strengthen knowledge graph with comment keywords
    from src.domains.agent.knowledge_graph import KnowledgeGraphRepository, WEIGHT_COMMENT
    kg = KnowledgeGraphRepository(session)
    await kg.strengthen_edges(user_id, comment_kws, weight_delta=WEIGHT_COMMENT)

    # Track affinity in DB + evaluate follow
    _rel_repo = PersonaRelationshipRepository(session)
    await _rel_repo.record_interaction(user_id, post.author_id, sentiment_delta=0.05)
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
        comment_affinities = await _get_affinities(session, user_id, comment_author_ids)
        parent = select_comment(persona, comments.items, comment_author_nicks, comment_affinities)
        if not parent:
            return

    await post_repo.increment_view_count(post.id)

    user_repo = UserRepository(session)
    post_author = await user_repo.get_by_id(post.author_id)
    post_author_name = post_author.nickname if post_author else "알 수 없음"
    comment_author = await user_repo.get_by_id(parent.author_id)
    comment_author_name = comment_author.nickname if comment_author else "알 수 없음"

    rel_hint = await _build_relationship_hint(session, user_id, parent.author_id, comment_author_name)
    reply_text = await generator.generate_reply(
        persona, post.title, post.content, post_author_name,
        parent.content, comment_author_name,
        relationship_hint=rel_hint,
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

    # Track affinity in DB for both post author and comment author
    _rel_repo = PersonaRelationshipRepository(session)
    await _rel_repo.record_interaction(user_id, post.author_id, sentiment_delta=0.05)
    await _rel_repo.record_interaction(user_id, parent.author_id, sentiment_delta=0.05)
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
    affinities = await _get_affinities(session, user_id, author_ids)
    post = select_post(persona, posts.items, author_nicknames, engagement_data, following_ids, sentiments, affinities)
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

    # Track affinity in DB
    _rel_repo = PersonaRelationshipRepository(session)
    await _rel_repo.record_interaction(user_id, post.author_id, sentiment_delta=0.05)

    logger.info("[%s] Quick reaction on post %s: %s", persona.nickname, post.id, reaction_text)
