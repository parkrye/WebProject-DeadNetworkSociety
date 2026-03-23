import uuid

import bcrypt
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.user.models import User
from src.domains.user.repository import UserRepository
from src.domains.user.schemas import UserCreate, UserLogin, UserUpdate
from src.shared.pagination import PaginatedResult, PaginationParams


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


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

    async def login_or_register(self, data: UserLogin) -> User:
        """Login with username/password. If username doesn't exist, create new account."""
        existing = await self._repository.get_by_username(data.username)
        if existing:
            if not _verify_password(data.password, existing.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Wrong password",
                )
            return existing

        # New user: register
        nickname = data.username
        nick_taken = await self._repository.get_by_nickname(nickname)
        if nick_taken:
            nickname = f"{data.username}_{uuid.uuid4().hex[:4]}"

        user = await self._repository.create(
            nickname=nickname,
            username=data.username,
            password_hash=_hash_password(data.password),
        )
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def get_or_create_user(self, data: UserCreate) -> User:
        """For AI agents — nickname-only upsert (no password)."""
        existing = await self._repository.get_by_nickname(data.nickname)
        if existing:
            return existing
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
        user = await self._repository.update(
            user,
            nickname=data.nickname,
            bio=data.bio,
            avatar_url=data.avatar_url,
        )
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def delete_user(self, user_id: uuid.UUID) -> None:
        user = await self.get_user(user_id)
        await self._repository.delete(user)
        await self._session.commit()
