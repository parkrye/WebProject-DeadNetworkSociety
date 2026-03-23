import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.comment.models import Comment
from src.domains.comment.schemas import CommentCreate, CommentEnrichedResponse, CommentResponse, CommentUpdate
from src.domains.comment.service import CommentService
from src.domains.user.models import User
from src.shared.database import get_session
from src.shared.pagination import PaginationParams

router = APIRouter(prefix="/api/comments", tags=["comments"])


def _get_service(session: AsyncSession = Depends(get_session)) -> CommentService:
    return CommentService(session)


@router.post("", response_model=CommentResponse, status_code=201)
async def create_comment(
    data: CommentCreate,
    service: CommentService = Depends(_get_service),
    session: AsyncSession = Depends(get_session),
) -> CommentResponse:
    comment = await service.create_comment(data)

    # AI personas react to user-created comments
    from src.domains.agent.auto_reaction import auto_react_to_content
    from src.domains.user.repository import UserRepository
    user_repo = UserRepository(session)
    author = await user_repo.get_by_id(data.author_id)
    if author and not author.is_agent:
        await auto_react_to_content(session, author.nickname, comment.content, "comment", comment.id)
        await session.commit()

    return CommentResponse.model_validate(comment)


@router.get("/by-post/{post_id}", response_model=list[CommentEnrichedResponse])
async def get_comments_by_post(
    post_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> list[CommentEnrichedResponse]:
    offset = (page - 1) * size
    stmt = (
        select(
            Comment,
            User.nickname.label("author_nickname"),
            User.avatar_url.label("author_avatar_url"),
        )
        .join(User, Comment.author_id == User.id)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())
        .offset(offset)
        .limit(size)
    )
    result = await session.execute(stmt)
    return [
        CommentEnrichedResponse(
            id=row.Comment.id,
            post_id=row.Comment.post_id,
            parent_id=row.Comment.parent_id,
            author_id=row.Comment.author_id,
            author_nickname=row.author_nickname,
            author_avatar_url=row.author_avatar_url or "",
            content=row.Comment.content,
            depth=row.Comment.depth,
            created_at=row.Comment.created_at,
            updated_at=row.Comment.updated_at,
        )
        for row in result.all()
    ]


@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: uuid.UUID,
    service: CommentService = Depends(_get_service),
) -> CommentResponse:
    comment = await service.get_comment(comment_id)
    return CommentResponse.model_validate(comment)


@router.patch("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: uuid.UUID,
    data: CommentUpdate,
    service: CommentService = Depends(_get_service),
) -> CommentResponse:
    comment = await service.update_comment(comment_id, data)
    return CommentResponse.model_validate(comment)


@router.delete("/{comment_id}", status_code=204)
async def delete_comment(
    comment_id: uuid.UUID,
    service: CommentService = Depends(_get_service),
) -> None:
    await service.delete_comment(comment_id)
