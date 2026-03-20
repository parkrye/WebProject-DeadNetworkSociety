import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.user.schemas import UserCreate, UserResponse, UserUpdate
from src.domains.user.service import UserService
from src.shared.database import get_session
from src.shared.pagination import PaginationParams

router = APIRouter(prefix="/api/users", tags=["users"])


def _get_service(session: AsyncSession = Depends(get_session)) -> UserService:
    return UserService(session)


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    data: UserCreate,
    service: UserService = Depends(_get_service),
) -> UserResponse:
    user = await service.create_user(data)
    return UserResponse.model_validate(user)


@router.get("", response_model=list[UserResponse])
async def get_users(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    service: UserService = Depends(_get_service),
) -> list[UserResponse]:
    result = await service.get_users(PaginationParams(page=page, size=size))
    return [UserResponse.model_validate(u) for u in result.items]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    service: UserService = Depends(_get_service),
) -> UserResponse:
    user = await service.get_user(user_id)
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    service: UserService = Depends(_get_service),
) -> UserResponse:
    user = await service.update_user(user_id, data)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: uuid.UUID,
    service: UserService = Depends(_get_service),
) -> None:
    await service.delete_user(user_id)
