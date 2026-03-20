import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.user.models import User
from src.domains.user.repository import UserRepository
from src.domains.user.schemas import UserCreate, UserUpdate
from src.shared.pagination import PaginatedResult, PaginationParams


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self._repository = UserRepository(session)
        self._session = session

    async def create_user(self, data: UserCreate) -> User:
        existing = await self._repository.get_by_nickname(data.nickname)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Nickname '{data.nickname}' is already taken",
            )
        user = await self._repository.create(nickname=data.nickname, is_agent=data.is_agent)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def get_user(self, user_id: uuid.UUID) -> User:
        user = await self._repository.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    async def get_users(self, params: PaginationParams) -> PaginatedResult[User]:
        return await self._repository.get_list(params)

    async def update_user(self, user_id: uuid.UUID, data: UserUpdate) -> User:
        user = await self.get_user(user_id)
        if data.nickname and data.nickname != user.nickname:
            existing = await self._repository.get_by_nickname(data.nickname)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Nickname '{data.nickname}' is already taken",
                )
        user = await self._repository.update(user, nickname=data.nickname)
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def delete_user(self, user_id: uuid.UUID) -> None:
        user = await self.get_user(user_id)
        await self._repository.delete(user)
        await self._session.commit()
