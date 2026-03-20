import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.reaction.models import Reaction


class ReactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: uuid.UUID,
        target_type: str,
        target_id: uuid.UUID,
        reaction_type: str,
    ) -> Reaction:
        reaction = Reaction(
            user_id=user_id,
            target_type=target_type,
            target_id=target_id,
            reaction_type=reaction_type,
        )
        self._session.add(reaction)
        await self._session.flush()
        return reaction

    async def get_by_user_and_target(
        self,
        user_id: uuid.UUID,
        target_type: str,
        target_id: uuid.UUID,
    ) -> Reaction | None:
        stmt = select(Reaction).where(
            Reaction.user_id == user_id,
            Reaction.target_type == target_type,
            Reaction.target_id == target_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, reaction: Reaction) -> None:
        await self._session.delete(reaction)
        await self._session.flush()

    async def delete_by_user_and_target(
        self,
        user_id: uuid.UUID,
        target_type: str,
        target_id: uuid.UUID,
    ) -> bool:
        stmt = delete(Reaction).where(
            Reaction.user_id == user_id,
            Reaction.target_type == target_type,
            Reaction.target_id == target_id,
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def count_by_target(self, target_type: str, target_id: uuid.UUID) -> dict[str, int]:
        stmt = (
            select(Reaction.reaction_type, func.count())
            .where(Reaction.target_type == target_type, Reaction.target_id == target_id)
            .group_by(Reaction.reaction_type)
        )
        result = await self._session.execute(stmt)
        counts: dict[str, int] = {}
        for reaction_type, count in result.all():
            counts[reaction_type] = count
        return counts
