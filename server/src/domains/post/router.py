import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.post.schemas import PostCreate, PostResponse, PostUpdate
from src.domains.post.service import PostService
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


@router.get("", response_model=list[PostResponse])
async def get_posts(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    service: PostService = Depends(_get_service),
) -> list[PostResponse]:
    result = await service.get_posts(PaginationParams(page=page, size=size))
    return [PostResponse.model_validate(p) for p in result.items]


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: uuid.UUID,
    service: PostService = Depends(_get_service),
) -> PostResponse:
    post = await service.get_post(post_id)
    return PostResponse.model_validate(post)


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
