import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession as Session2

from src.domains.reaction.models import Reaction
from src.domains.reaction.schemas import ReactionCountResponse, ReactionCreate, ReactionDetailResponse, ReactionResponse
from src.domains.reaction.service import ReactionService
from src.domains.user.models import User
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


@router.get("/list/{target_type}/{target_id}", response_model=list[ReactionDetailResponse])
async def get_reaction_list(
    target_type: str,
    target_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> list[ReactionDetailResponse]:
    stmt = (
        select(Reaction, User.nickname)
        .join(User, Reaction.user_id == User.id)
        .where(Reaction.target_type == target_type, Reaction.target_id == target_id)
        .order_by(Reaction.created_at.desc())
    )
    result = await session.execute(stmt)
    return [
        ReactionDetailResponse(
            user_id=row.Reaction.user_id,
            user_nickname=row.nickname,
            reaction_type=row.Reaction.reaction_type,
            created_at=row.Reaction.created_at,
        )
        for row in result.all()
    ]


@router.get("/counts/{target_type}/{target_id}", response_model=ReactionCountResponse)
async def get_reaction_counts(
    target_type: str,
    target_id: uuid.UUID,
    service: ReactionService = Depends(_get_service),
) -> ReactionCountResponse:
    return await service.get_counts(target_type, target_id)
