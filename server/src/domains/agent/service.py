import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.agent.models import AgentProfile
from src.domains.agent.persona_loader import Persona, load_persona, PERSONAS_DIR
from src.domains.agent.repository import AgentRepository
from src.domains.agent.schemas import AgentProfileCreate, AgentProfileUpdate
from src.shared.base_model import _utc_now


class AgentService:
    def __init__(self, session: AsyncSession) -> None:
        self._repository = AgentRepository(session)
        self._session = session

    async def create_agent(self, user_id: uuid.UUID, data: AgentProfileCreate) -> AgentProfile:
        existing = await self._repository.get_by_user_id(user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Agent profile already exists for this user",
            )

        profile = await self._repository.create(
            user_id=user_id,
            persona_file=data.persona_file,
            is_active=data.is_active,
        )
        await self._session.commit()
        await self._session.refresh(profile)
        return profile

    async def get_agent(self, profile_id: uuid.UUID) -> AgentProfile:
        profile = await self._repository.get_by_id(profile_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent profile not found")
        return profile

    async def get_active_agents(self) -> list[AgentProfile]:
        return await self._repository.get_active_agents()

    async def update_agent(self, profile_id: uuid.UUID, data: AgentProfileUpdate) -> AgentProfile:
        profile = await self.get_agent(profile_id)
        profile = await self._repository.update(
            profile,
            is_active=data.is_active,
        )
        await self._session.commit()
        await self._session.refresh(profile)
        return profile

    async def record_action(self, profile_id: uuid.UUID) -> None:
        profile = await self.get_agent(profile_id)
        await self._repository.update(profile, last_action_at=_utc_now())
        await self._session.commit()
