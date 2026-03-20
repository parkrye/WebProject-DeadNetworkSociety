import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.comment.models import Comment
from src.domains.post.models import Post
from src.domains.post.schemas import PostCreate, PostEnrichedResponse, PostResponse, PostUpdate
from src.domains.post.service import PostService
from src.domains.reaction.models import Reaction
from src.domains.user.models import User
from src.shared.database import get_session
from src.shared.pagination import PaginationParams

router = APIRouter(prefix="/api/posts", tags=["posts"])


def _get_service(session: AsyncSession = Depends(get_session)) -> PostService:
    return PostService(session)


@router.post("", response_model=PostResponse, status_code=201)
async def create_post(
    data: PostCreate,
    service: PostService = Depends(_get_service),
) -> PostResponse:
    post = await service.create_post(data)
    return PostResponse.model_validate(post)


@router.get("/feed", response_model=list[PostEnrichedResponse])
async def get_feed(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> list[PostEnrichedResponse]:
    offset = (page - 1) * size

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

    stmt = (
        select(
            Post,
            User.nickname.label("author_nickname"),
            func.coalesce(like_sub.c.cnt, 0).label("like_count"),
            func.coalesce(dislike_sub.c.cnt, 0).label("dislike_count"),
            func.coalesce(comment_sub.c.cnt, 0).label("comment_count"),
        )
        .join(User, Post.author_id == User.id)
        .outerjoin(like_sub, Post.id == like_sub.c.target_id)
        .outerjoin(dislike_sub, Post.id == dislike_sub.c.target_id)
        .outerjoin(comment_sub, Post.id == comment_sub.c.post_id)
        .order_by(Post.created_at.desc())
        .offset(offset)
        .limit(size)
    )

    result = await session.execute(stmt)
    rows = result.all()

    return [
        PostEnrichedResponse(
            id=row.Post.id,
            author_id=row.Post.author_id,
            author_nickname=row.author_nickname,
            title=row.Post.title,
            content=row.Post.content,
            like_count=row.like_count,
            dislike_count=row.dislike_count,
            comment_count=row.comment_count,
            created_at=row.Post.created_at,
            updated_at=row.Post.updated_at,
        )
        for row in rows
    ]


@router.get("", response_model=list[PostResponse])
async def get_posts(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    service: PostService = Depends(_get_service),
) -> list[PostResponse]:
    result = await service.get_posts(PaginationParams(page=page, size=size))
    return [PostResponse.model_validate(p) for p in result.items]


@router.get("/{post_id}", response_model=PostEnrichedResponse)
async def get_post(
    post_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> PostEnrichedResponse:
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
    stmt = (
        select(
            Post,
            User.nickname.label("author_nickname"),
            func.coalesce(like_sub.c.cnt, 0).label("like_count"),
            func.coalesce(dislike_sub.c.cnt, 0).label("dislike_count"),
            func.coalesce(comment_sub.c.cnt, 0).label("comment_count"),
        )
        .join(User, Post.author_id == User.id)
        .outerjoin(like_sub, Post.id == like_sub.c.target_id)
        .outerjoin(dislike_sub, Post.id == dislike_sub.c.target_id)
        .outerjoin(comment_sub, Post.id == comment_sub.c.post_id)
        .where(Post.id == post_id)
    )
    result = await session.execute(stmt)
    row = result.one_or_none()
    if not row:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Post not found")
    return PostEnrichedResponse(
        id=row.Post.id,
        author_id=row.Post.author_id,
        author_nickname=row.author_nickname,
        title=row.Post.title,
        content=row.Post.content,
        like_count=row.like_count,
        dislike_count=row.dislike_count,
        comment_count=row.comment_count,
        created_at=row.Post.created_at,
        updated_at=row.Post.updated_at,
    )


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
