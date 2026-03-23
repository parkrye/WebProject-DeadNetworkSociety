import uuid

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.follow.models import Follow
from src.domains.user.models import User


class FollowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, follower_id: uuid.UUID, following_id: uuid.UUID) -> Follow:
        follow = Follow(follower_id=follower_id, following_id=following_id)
        self._session.add(follow)
        await self._session.flush()
        return follow

    async def delete_by_pair(self, follower_id: uuid.UUID, following_id: uuid.UUID) -> bool:
        stmt = (
            delete(Follow)
            .where(Follow.follower_id == follower_id, Follow.following_id == following_id)
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def is_following(self, follower_id: uuid.UUID, following_id: uuid.UUID) -> bool:
        stmt = select(Follow.id).where(
            Follow.follower_id == follower_id, Follow.following_id == following_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_followers(self, user_id: uuid.UUID, limit: int = 20) -> list:
        stmt = (
            select(User.id, User.nickname, User.avatar_url, User.is_agent)
            .join(Follow, Follow.follower_id == User.id)
            .where(Follow.following_id == user_id)
            .order_by(Follow.created_at.desc())
            .limit(limit)
        )
        return list((await self._session.execute(stmt)).all())

    async def get_following(self, user_id: uuid.UUID, limit: int = 20) -> list:
        stmt = (
            select(User.id, User.nickname, User.avatar_url, User.is_agent)
            .join(Follow, Follow.following_id == User.id)
            .where(Follow.follower_id == user_id)
            .order_by(Follow.created_at.desc())
            .limit(limit)
        )
        return list((await self._session.execute(stmt)).all())

    async def count_followers(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count()).select_from(Follow).where(Follow.following_id == user_id)
        return (await self._session.execute(stmt)).scalar_one()

    async def count_following(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count()).select_from(Follow).where(Follow.follower_id == user_id)
        return (await self._session.execute(stmt)).scalar_one()

    async def get_following_ids(self, user_id: uuid.UUID) -> set[uuid.UUID]:
        stmt = select(Follow.following_id).where(Follow.follower_id == user_id)
        result = await self._session.execute(stmt)
        return {r[0] for r in result.all()}

    async def get_sentiment(self, follower_id: uuid.UUID, following_id: uuid.UUID) -> float:
        stmt = select(Follow.sentiment_score).where(
            Follow.follower_id == follower_id, Follow.following_id == following_id,
        )
        result = await self._session.execute(stmt)
        val = result.scalar_one_or_none()
        return val if val is not None else 0.0

    async def get_sentiments_for_authors(
        self, follower_id: uuid.UUID, author_ids: set[uuid.UUID],
    ) -> dict[uuid.UUID, float]:
        if not author_ids:
            return {}
        stmt = (
            select(Follow.following_id, Follow.sentiment_score)
            .where(Follow.follower_id == follower_id, Follow.following_id.in_(author_ids))
        )
        result = await self._session.execute(stmt)
        return {r[0]: r[1] for r in result.all()}

    async def increment_interaction(
        self, follower_id: uuid.UUID, following_id: uuid.UUID, sentiment_delta: float = 0.0,
    ) -> None:
        """Increment interaction count and adjust sentiment on an existing follow."""
        stmt = (
            update(Follow)
            .where(Follow.follower_id == follower_id, Follow.following_id == following_id)
            .values(
                interaction_count=Follow.interaction_count + 1,
                sentiment_score=func.greatest(-1.0, func.least(1.0, Follow.sentiment_score + sentiment_delta)),
            )
        )
        await self._session.execute(stmt)

    async def get_interaction_count(self, follower_id: uuid.UUID, following_id: uuid.UUID) -> int:
        stmt = select(Follow.interaction_count).where(
            Follow.follower_id == follower_id, Follow.following_id == following_id,
        )
        result = await self._session.execute(stmt)
        val = result.scalar_one_or_none()
        return val if val is not None else 0
