import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.comment.schemas import CommentCreate, CommentResponse, CommentUpdate
from src.domains.comment.service import CommentService
from src.shared.database import get_session
from src.shared.pagination import PaginationParams

router = APIRouter(prefix="/api/comments", tags=["comments"])


def _get_service(session: AsyncSession = Depends(get_session)) -> CommentService:
    return CommentService(session)


@router.post("", response_model=CommentResponse, status_code=201)
async def create_comment(
    data: CommentCreate,
    service: CommentService = Depends(_get_service),
) -> CommentResponse:
    comment = await service.create_comment(data)
    return CommentResponse.model_validate(comment)


@router.get("/by-post/{post_id}", response_model=list[CommentResponse])
async def get_comments_by_post(
    post_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    service: CommentService = Depends(_get_service),
) -> list[CommentResponse]:
    result = await service.get_comments_by_post(post_id, PaginationParams(page=page, size=size))
    return [CommentResponse.model_validate(c) for c in result.items]


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
