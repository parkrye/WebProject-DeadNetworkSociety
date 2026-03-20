import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.user.models import User
from src.shared.pagination import PaginatedResult, PaginationParams


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, nickname: str, is_agent: bool = False) -> User:
        user = User(nickname=nickname, is_agent=is_agent)
        self._session.add(user)
        await self._session.flush()
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_nickname(self, nickname: str) -> User | None:
        stmt = select(User).where(User.nickname == nickname)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_list(self, params: PaginationParams) -> PaginatedResult[User]:
        count_stmt = select(func.count()).select_from(User)
        total = (await self._session.execute(count_stmt)).scalar_one()

        stmt = (
            select(User)
            .order_by(User.created_at.desc())
            .offset(params.offset)
            .limit(params.size)
        )
        result = await self._session.execute(stmt)
        items = list(result.scalars().all())

        return PaginatedResult(items=items, total=total, page=params.page, size=params.size)

    async def update(self, user: User, nickname: str | None = None) -> User:
        if nickname is not None:
            user.nickname = nickname
        await self._session.flush()
        return user

    async def delete(self, user: User) -> None:
        await self._session.delete(user)
        await self._session.flush()
