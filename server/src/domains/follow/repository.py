import uuid

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

import math

from src.domains.follow.models import Follow, PersonaMemory, PersonaRelationship
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


class PersonaRelationshipRepository:
    """Persistent replacement for in-memory AffinityTracker."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record_interaction(
        self,
        actor_id: uuid.UUID,
        target_id: uuid.UUID,
        reaction_type: str | None = None,
        sentiment_delta: float = 0.0,
    ) -> PersonaRelationship | None:
        """Record an interaction. Creates row if not exists, updates if exists."""
        if actor_id == target_id:
            return None

        stmt = select(PersonaRelationship).where(
            PersonaRelationship.actor_id == actor_id,
            PersonaRelationship.target_id == target_id,
        )
        result = await self._session.execute(stmt)
        rel = result.scalar_one_or_none()

        if rel:
            rel.interaction_count += 1
            if reaction_type == "like":
                rel.like_count += 1
            elif reaction_type == "dislike":
                rel.dislike_count += 1
            rel.sentiment_score = max(-1.0, min(1.0, rel.sentiment_score + sentiment_delta))
            await self._session.flush()
        else:
            like_c = 1 if reaction_type == "like" else 0
            dislike_c = 1 if reaction_type == "dislike" else 0
            rel = PersonaRelationship(
                actor_id=actor_id,
                target_id=target_id,
                interaction_count=1,
                like_count=like_c,
                dislike_count=dislike_c,
                sentiment_score=max(-1.0, min(1.0, sentiment_delta)),
            )
            self._session.add(rel)
            await self._session.flush()

        return rel

    async def get_interaction_count(self, actor_id: uuid.UUID, target_id: uuid.UUID) -> int:
        stmt = select(PersonaRelationship.interaction_count).where(
            PersonaRelationship.actor_id == actor_id,
            PersonaRelationship.target_id == target_id,
        )
        result = await self._session.execute(stmt)
        val = result.scalar_one_or_none()
        return val if val is not None else 0

    async def get_affinity(self, actor_id: uuid.UUID, target_id: uuid.UUID) -> float:
        count = await self.get_interaction_count(actor_id, target_id)
        return math.log1p(count) if count > 0 else 0.0

    async def get_affinities_for_authors(
        self, actor_id: uuid.UUID, author_ids: set[uuid.UUID],
    ) -> dict[uuid.UUID, float]:
        if not author_ids:
            return {}
        stmt = (
            select(PersonaRelationship.target_id, PersonaRelationship.interaction_count)
            .where(
                PersonaRelationship.actor_id == actor_id,
                PersonaRelationship.target_id.in_(author_ids),
            )
        )
        result = await self._session.execute(stmt)
        return {r[0]: math.log1p(r[1]) for r in result.all()}

    async def get_sentiments_for_authors(
        self, actor_id: uuid.UUID, author_ids: set[uuid.UUID],
    ) -> dict[uuid.UUID, float]:
        if not author_ids:
            return {}
        stmt = (
            select(PersonaRelationship.target_id, PersonaRelationship.sentiment_score)
            .where(
                PersonaRelationship.actor_id == actor_id,
                PersonaRelationship.target_id.in_(author_ids),
            )
        )
        result = await self._session.execute(stmt)
        return {r[0]: r[1] for r in result.all()}


class PersonaMemoryRepository:
    """Stores hidden impressions one persona has about another."""

    MAX_MEMORIES_PER_PAIR = 5

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_memory(
        self, actor_id: uuid.UUID, target_id: uuid.UUID,
        memory_type: str, content: str,
    ) -> None:
        self._session.add(PersonaMemory(
            actor_id=actor_id, target_id=target_id,
            memory_type=memory_type, content=content[:200],
        ))
        await self._session.flush()

        count_stmt = (
            select(func.count()).select_from(PersonaMemory)
            .where(PersonaMemory.actor_id == actor_id, PersonaMemory.target_id == target_id)
        )
        total = (await self._session.execute(count_stmt)).scalar_one()
        if total > self.MAX_MEMORIES_PER_PAIR:
            oldest = await self._session.execute(
                select(PersonaMemory.id)
                .where(PersonaMemory.actor_id == actor_id, PersonaMemory.target_id == target_id)
                .order_by(PersonaMemory.created_at.asc())
                .limit(total - self.MAX_MEMORIES_PER_PAIR)
            )
            old_ids = [r[0] for r in oldest.all()]
            if old_ids:
                await self._session.execute(
                    delete(PersonaMemory).where(PersonaMemory.id.in_(old_ids))
                )

    async def get_memories(
        self, actor_id: uuid.UUID, target_id: uuid.UUID, limit: int = 5,
    ) -> list[PersonaMemory]:
        stmt = (
            select(PersonaMemory)
            .where(PersonaMemory.actor_id == actor_id, PersonaMemory.target_id == target_id)
            .order_by(PersonaMemory.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def format_memories_for_prompt(
        self, actor_id: uuid.UUID, target_id: uuid.UUID, target_nickname: str,
    ) -> str:
        memories = await self.get_memories(actor_id, target_id, limit=3)
        if not memories:
            return ""
        lines = [f"[{target_nickname}에 대한 기억]"]
        for m in memories:
            tag = "+" if m.memory_type == "positive" else "-"
            lines.append(f"  ({tag}) {m.content}")
        return "\n".join(lines)
