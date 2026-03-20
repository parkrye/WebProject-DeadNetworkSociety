import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.agent.models import AgentProfile


class AgentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: uuid.UUID,
        persona_file: str,
        is_active: bool = True,
    ) -> AgentProfile:
        profile = AgentProfile(
            user_id=user_id,
            persona_file=persona_file,
            is_active=is_active,
        )
        self._session.add(profile)
        await self._session.flush()
        return profile

    async def get_by_id(self, profile_id: uuid.UUID) -> AgentProfile | None:
        return await self._session.get(AgentProfile, profile_id)

    async def get_by_user_id(self, user_id: uuid.UUID) -> AgentProfile | None:
        stmt = select(AgentProfile).where(AgentProfile.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_agents(self) -> list[AgentProfile]:
        stmt = select(AgentProfile).where(AgentProfile.is_active.is_(True))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self,
        profile: AgentProfile,
        is_active: bool | None = None,
        last_action_at: datetime | None = None,
    ) -> AgentProfile:
        if is_active is not None:
            profile.is_active = is_active
        if last_action_at is not None:
            profile.last_action_at = last_action_at
        await self._session.flush()
        return profile

    async def delete(self, profile: AgentProfile) -> None:
        await self._session.delete(profile)
        await self._session.flush()
