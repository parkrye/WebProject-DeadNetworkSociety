"""Admin endpoints for system management and statistics."""
import asyncio
import logging
import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.agent.bootstrap import start_agent_system
from src.domains.agent.models import KnowledgeEdge, PersonaState
from src.domains.comment.models import Comment
from src.domains.follow.models import Follow, PersonaMemory, PersonaRelationship
from src.domains.post.models import PopularPost, Post, PostMetadata, TrendingKeyword
from src.domains.reaction.models import Reaction
from src.domains.user.models import User
from src.shared.database import get_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# --- Data Reset ---

@router.post("/reset/posts", status_code=204)
async def reset_posts(session: AsyncSession = Depends(get_session)) -> None:
    await session.execute(delete(TrendingKeyword))
    await session.execute(delete(PopularPost))
    await session.execute(delete(PostMetadata))
    await session.execute(delete(Reaction))
    await session.execute(delete(Comment))
    await session.execute(delete(Post))
    await session.commit()

@router.post("/reset/relationships", status_code=204)
async def reset_relationships(session: AsyncSession = Depends(get_session)) -> None:
    await session.execute(delete(PersonaMemory))
    await session.execute(delete(PersonaRelationship))
    await session.execute(delete(Follow))
    await session.commit()

@router.post("/reset/knowledge", status_code=204)
async def reset_knowledge(session: AsyncSession = Depends(get_session)) -> None:
    await session.execute(delete(KnowledgeEdge))
    await session.execute(delete(PersonaState))
    await session.commit()

@router.post("/reset/all", status_code=204)
async def reset_all(session: AsyncSession = Depends(get_session)) -> None:
    await session.execute(delete(TrendingKeyword))
    await session.execute(delete(PopularPost))
    await session.execute(delete(PostMetadata))
    await session.execute(delete(PersonaMemory))
    await session.execute(delete(PersonaRelationship))
    await session.execute(delete(PersonaState))
    await session.execute(delete(Follow))
    await session.execute(delete(Reaction))
    await session.execute(delete(Comment))
    await session.execute(delete(Post))
    await session.execute(delete(KnowledgeEdge))
    await session.commit()


# --- Agent Control ---

@router.post("/restart-agents", status_code=204)
async def restart_agents(request: Request) -> None:
    old_task: asyncio.Task | None = getattr(request.app.state, "scheduler_task", None)
    if old_task and not old_task.done():
        old_task.cancel()
        try:
            await old_task
        except asyncio.CancelledError:
            pass
    session_factory = request.app.state.session_factory
    content_generator = request.app.state.content_generator
    new_task = await start_agent_system(session_factory, content_generator)
    request.app.state.scheduler_task = new_task


# --- Statistics ---

@router.get("/stats/overview")
async def get_overview_stats(session: AsyncSession = Depends(get_session)) -> dict:
    posts = (await session.execute(select(func.count()).select_from(Post))).scalar_one()
    comments = (await session.execute(select(func.count()).select_from(Comment))).scalar_one()
    reactions = (await session.execute(select(func.count()).select_from(Reaction))).scalar_one()
    follows = (await session.execute(select(func.count()).select_from(Follow))).scalar_one()
    relationships = (await session.execute(select(func.count()).select_from(PersonaRelationship))).scalar_one()
    memories = (await session.execute(select(func.count()).select_from(PersonaMemory))).scalar_one()
    edges = (await session.execute(select(func.count()).select_from(KnowledgeEdge))).scalar_one()
    trending = (await session.execute(select(func.count()).select_from(TrendingKeyword))).scalar_one()
    popular = (await session.execute(select(func.count()).select_from(PopularPost))).scalar_one()
    return {
        "posts": posts, "comments": comments, "reactions": reactions,
        "follows": follows, "relationships": relationships, "memories": memories,
        "knowledge_edges": edges, "trending_keywords": trending, "popular_posts": popular,
    }


@router.get("/stats/knowledge/{user_id}")
async def get_knowledge_graph(
    user_id: uuid.UUID,
    limit: int = Query(default=30, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    stmt = (
        select(KnowledgeEdge.keyword_from, KnowledgeEdge.keyword_to,
               KnowledgeEdge.weight, KnowledgeEdge.relation)
        .where(KnowledgeEdge.persona_id == user_id, KnowledgeEdge.weight > 0)
        .order_by(KnowledgeEdge.weight.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return [
        {"from": r.keyword_from, "to": r.keyword_to, "weight": round(r.weight, 2), "relation": r.relation}
        for r in result.all()
    ]


@router.get("/stats/relationships/{user_id}")
async def get_relationships(
    user_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    stmt = (
        select(
            PersonaRelationship.target_id,
            User.nickname,
            User.avatar_url,
            PersonaRelationship.interaction_count,
            PersonaRelationship.like_count,
            PersonaRelationship.dislike_count,
            PersonaRelationship.sentiment_score,
        )
        .join(User, PersonaRelationship.target_id == User.id)
        .where(PersonaRelationship.actor_id == user_id)
        .order_by(PersonaRelationship.interaction_count.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return [
        {
            "target_id": str(r.target_id), "nickname": r.nickname, "avatar_url": r.avatar_url or "",
            "interactions": r.interaction_count, "likes": r.like_count, "dislikes": r.dislike_count,
            "sentiment": round(r.sentiment_score, 2),
        }
        for r in result.all()
    ]


@router.get("/stats/trending")
async def get_trending_stats(session: AsyncSession = Depends(get_session)) -> list[dict]:
    stmt = select(TrendingKeyword.keyword, TrendingKeyword.count).order_by(TrendingKeyword.count.desc())
    result = await session.execute(stmt)
    return [{"keyword": r.keyword, "count": r.count} for r in result.all()]
