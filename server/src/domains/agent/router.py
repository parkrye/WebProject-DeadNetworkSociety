import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.agent.schemas import AgentProfileCreate, AgentProfileResponse, AgentProfileUpdate
from src.domains.agent.service import AgentService
from src.domains.agent.status_store import get_all_statuses
from src.shared.database import get_session

router = APIRouter(prefix="/api/agents", tags=["agents"])


def _get_service(session: AsyncSession = Depends(get_session)) -> AgentService:
    return AgentService(session)


@router.post("/{user_id}", response_model=AgentProfileResponse, status_code=201)
async def create_agent(
    user_id: uuid.UUID,
    data: AgentProfileCreate,
    service: AgentService = Depends(_get_service),
) -> AgentProfileResponse:
    profile = await service.create_agent(user_id, data)
    return AgentProfileResponse.model_validate(profile)


@router.get("/status")
async def get_agent_statuses() -> dict[str, dict]:
    return get_all_statuses()


@router.get("/active", response_model=list[AgentProfileResponse])
async def get_active_agents(
    service: AgentService = Depends(_get_service),
) -> list[AgentProfileResponse]:
    agents = await service.get_active_agents()
    return [AgentProfileResponse.model_validate(a) for a in agents]


@router.get("/{profile_id}", response_model=AgentProfileResponse)
async def get_agent(
    profile_id: uuid.UUID,
    service: AgentService = Depends(_get_service),
) -> AgentProfileResponse:
    profile = await service.get_agent(profile_id)
    return AgentProfileResponse.model_validate(profile)


@router.patch("/{profile_id}", response_model=AgentProfileResponse)
async def update_agent(
    profile_id: uuid.UUID,
    data: AgentProfileUpdate,
    service: AgentService = Depends(_get_service),
) -> AgentProfileResponse:
    profile = await service.update_agent(profile_id, data)
    return AgentProfileResponse.model_validate(profile)
