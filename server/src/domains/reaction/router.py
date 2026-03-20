import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.reaction.schemas import ReactionCountResponse, ReactionCreate, ReactionResponse
from src.domains.reaction.service import ReactionService
from src.shared.database import get_session

router = APIRouter(prefix="/api/reactions", tags=["reactions"])


def _get_service(session: AsyncSession = Depends(get_session)) -> ReactionService:
    return ReactionService(session)


@router.post("", response_model=ReactionResponse | None, status_code=200)
async def toggle_reaction(
    data: ReactionCreate,
    service: ReactionService = Depends(_get_service),
) -> ReactionResponse | None:
    reaction = await service.toggle_reaction(data)
    if reaction is None:
        return None
    return ReactionResponse.model_validate(reaction)


@router.get("/counts/{target_type}/{target_id}", response_model=ReactionCountResponse)
async def get_reaction_counts(
    target_type: str,
    target_id: uuid.UUID,
    service: ReactionService = Depends(_get_service),
) -> ReactionCountResponse:
    return await service.get_counts(target_type, target_id)
