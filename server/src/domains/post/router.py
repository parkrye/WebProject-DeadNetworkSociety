import uuid

import yaml
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.comment.models import Comment
from src.domains.post.models import PopularPost, Post
from src.domains.post.models import TrendingKeyword
from src.domains.post.repository import PopularPostRepository, TrendingKeywordRepository
from src.domains.post.schemas import PostCreate, PostEnrichedResponse, PostResponse, PostUpdate, TrendingKeywordResponse
from src.domains.post.service import PostService
from src.domains.reaction.models import Reaction
from src.domains.user.models import User
from src.shared.database import get_session
from src.shared.pagination import PaginationParams

router = APIRouter(prefix="/api/posts", tags=["posts"])

_AI_DEFAULTS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "ai_defaults.yaml"


def _load_popularity_config() -> dict:
    with open(_AI_DEFAULTS_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f).get("popularity", {})


def _get_service(session: AsyncSession = Depends(get_session)) -> PostService:
    return PostService(session)


def _build_engagement_subqueries():
    """Build reusable subqueries for like/dislike/comment counts."""
    like_sub = (
        select(Reaction.target_id, func.count().label("cnt"))
        .where(Reaction.target_type == "post", Reaction.reaction_type == "like")
        .group_by(Reaction.target_id)
        .subquery()
    )
    dislike_sub = (
        select(Reaction.target_id, func.count().label("cnt"))
        .where(Reaction.target_type == "post", Reaction.reaction_type == "dislike")
        .group_by(Reaction.target_id)
        .subquery()
    )
    comment_sub = (
        select(Comment.post_id, func.count().label("cnt"))
        .group_by(Comment.post_id)
        .subquery()
    )
    return like_sub, dislike_sub, comment_sub


def _build_enriched_select(like_sub, dislike_sub, comment_sub):
    """Build a SELECT with all enriched columns."""
    return select(
        Post,
        User.nickname.label("author_nickname"),
        User.avatar_url.label("author_avatar_url"),
        func.coalesce(like_sub.c.cnt, 0).label("like_count"),
        func.coalesce(dislike_sub.c.cnt, 0).label("dislike_count"),
        func.coalesce(comment_sub.c.cnt, 0).label("comment_count"),
    ).join(
        User, Post.author_id == User.id,
    ).outerjoin(
        like_sub, Post.id == like_sub.c.target_id,
    ).outerjoin(
        dislike_sub, Post.id == dislike_sub.c.target_id,
    ).outerjoin(
        comment_sub, Post.id == comment_sub.c.post_id,
    )


def _row_to_enriched(row, popularity_score: float | None = None) -> PostEnrichedResponse:
    import json
    try:
        keywords = json.loads(row.Post.keywords) if row.Post.keywords else []
    except (json.JSONDecodeError, TypeError):
        keywords = []
    return PostEnrichedResponse(
        id=row.Post.id,
        author_id=row.Post.author_id,
        author_nickname=row.author_nickname,
        author_avatar_url=row.author_avatar_url or "",
        title=row.Post.title,
        content=row.Post.content,
        keywords=keywords,
        popularity_score=popularity_score,
        like_count=row.like_count,
        dislike_count=row.dislike_count,
        comment_count=row.comment_count,
        view_count=row.Post.view_count,
        created_at=row.Post.created_at,
        updated_at=row.Post.updated_at,
    )


@router.post("", response_model=PostResponse, status_code=201)
async def create_post(
    data: PostCreate,
    service: PostService = Depends(_get_service),
    session: AsyncSession = Depends(get_session),
) -> PostResponse:
    post = await service.create_post(data)

    # AI personas react to user-created posts
    from src.domains.agent.auto_reaction import auto_react_to_content
    from src.domains.agent.mention_handler import handle_mentions
    from src.domains.user.repository import UserRepository
    user_repo = UserRepository(session)
    author = await user_repo.get_by_id(data.author_id)
    if author and not author.is_agent:
        content_text = f"{post.title} {post.content}"
        await auto_react_to_content(session, author.nickname, content_text, "post", post.id)
        await handle_mentions(session, content_text, "post", post.id, author.id)
        await session.commit()

    return PostResponse.model_validate(post)


@router.get("/feed", response_model=list[PostEnrichedResponse])
async def get_feed(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> list[PostEnrichedResponse]:
    offset = (page - 1) * size
    like_sub, dislike_sub, comment_sub = _build_engagement_subqueries()
    stmt = (
        _build_enriched_select(like_sub, dislike_sub, comment_sub)
        .order_by(Post.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    result = await session.execute(stmt)
    return [_row_to_enriched(row) for row in result.all()]


@router.post("/popular/refresh", status_code=204)
async def refresh_popular(
    session: AsyncSession = Depends(get_session),
) -> None:
    """Recalculate popular posts queue."""
    config = _load_popularity_config()
    repo = PopularPostRepository(session)
    await repo.refresh(
        comment_weight=config.get("comment_weight", 3.0),
        like_weight=config.get("like_weight", 2.0),
        like_ratio_weight=config.get("like_ratio_weight", 1.0),
        min_engagement=config.get("min_engagement", 2),
        max_slots=config.get("max_slots", 10),
    )
    await session.commit()


@router.get("/trending-keywords", response_model=list[TrendingKeywordResponse])
async def get_trending_keywords(
    session: AsyncSession = Depends(get_session),
) -> list[TrendingKeywordResponse]:
    repo = TrendingKeywordRepository(session)
    keywords = await repo.get_all()
    return [TrendingKeywordResponse(keyword=k.keyword, count=k.count) for k in keywords]


@router.get("/popular", response_model=list[PostEnrichedResponse])
async def get_popular_feed(
    session: AsyncSession = Depends(get_session),
) -> list[PostEnrichedResponse]:
    """Return posts from the popular_posts queue (max 10, pre-calculated)."""
    like_sub, dislike_sub, comment_sub = _build_engagement_subqueries()
    stmt = (
        select(
            Post,
            User.nickname.label("author_nickname"),
            User.avatar_url.label("author_avatar_url"),
            func.coalesce(like_sub.c.cnt, 0).label("like_count"),
            func.coalesce(dislike_sub.c.cnt, 0).label("dislike_count"),
            func.coalesce(comment_sub.c.cnt, 0).label("comment_count"),
            PopularPost.popularity_score,
        )
        .join(User, Post.author_id == User.id)
        .join(PopularPost, Post.id == PopularPost.post_id)
        .outerjoin(like_sub, Post.id == like_sub.c.target_id)
        .outerjoin(dislike_sub, Post.id == dislike_sub.c.target_id)
        .outerjoin(comment_sub, Post.id == comment_sub.c.post_id)
        .order_by(PopularPost.popularity_score.desc())
    )
    result = await session.execute(stmt)
    return [
        _row_to_enriched(row, popularity_score=row.popularity_score)
        for row in result.all()
    ]


@router.get("", response_model=list[PostResponse])
async def get_posts(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    service: PostService = Depends(_get_service),
) -> list[PostResponse]:
    result = await service.get_posts(PaginationParams(page=page, size=size))
    return [PostResponse.model_validate(p) for p in result.items]


@router.get("/search", response_model=list[PostEnrichedResponse])
async def search_posts(
    q: str = Query(min_length=1, max_length=50),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> list[PostEnrichedResponse]:
    """Search posts by title, content, author nickname, or keywords."""
    offset = (page - 1) * size
    pattern = f"%{q}%"
    like_sub, dislike_sub, comment_sub = _build_engagement_subqueries()
    stmt = (
        _build_enriched_select(like_sub, dislike_sub, comment_sub)
        .where(
            Post.title.ilike(pattern)
            | Post.content.ilike(pattern)
            | User.nickname.ilike(pattern)
            | Post.keywords.ilike(pattern)
        )
        .order_by(Post.created_at.desc())
        .offset(offset)
        .limit(size)
    )
    result = await session.execute(stmt)
    return [_row_to_enriched(row) for row in result.all()]


@router.get("/{post_id}", response_model=PostEnrichedResponse)
async def get_post(
    post_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> PostEnrichedResponse:
    like_sub, dislike_sub, comment_sub = _build_engagement_subqueries()
    stmt = (
        _build_enriched_select(like_sub, dislike_sub, comment_sub)
        .where(Post.id == post_id)
    )
    result = await session.execute(stmt)
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Post not found")
    return _row_to_enriched(row)


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: uuid.UUID,
    data: PostUpdate,
    service: PostService = Depends(_get_service),
) -> PostResponse:
    post = await service.update_post(post_id, data)
    return PostResponse.model_validate(post)


@router.delete("/{post_id}", status_code=204)
async def delete_post(
    post_id: uuid.UUID,
    service: PostService = Depends(_get_service),
) -> None:
    await service.delete_post(post_id)
