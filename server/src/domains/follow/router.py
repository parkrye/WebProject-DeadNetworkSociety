import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.follow.repository import FollowRepository
from src.domains.follow.schemas import FollowResponse, FollowToggle, FollowUserItem
from src.shared.database import get_session

router = APIRouter(prefix="/api/follows", tags=["follows"])


@router.post("", response_model=FollowResponse | None)
async def toggle_follow(
    data: FollowToggle,
    session: AsyncSession = Depends(get_session),
) -> FollowResponse | None:
    """Toggle follow: follow if not following, unfollow if already following."""
    if data.follower_id == data.following_id:
        return None

    repo = FollowRepository(session)
    existing = await repo.is_following(data.follower_id, data.following_id)
    if existing:
        await repo.delete_by_pair(data.follower_id, data.following_id)
        await session.commit()
        return None

    follow = await repo.create(data.follower_id, data.following_id)
    await session.commit()
    return FollowResponse.model_validate(follow)


@router.get("/{user_id}/followers", response_model=list[FollowUserItem])
async def get_followers(
    user_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> list[FollowUserItem]:
    repo = FollowRepository(session)
    rows = await repo.get_followers(user_id, limit)
    return [
        FollowUserItem(user_id=r.id, nickname=r.nickname, avatar_url=r.avatar_url or "", is_agent=r.is_agent)
        for r in rows
    ]


@router.get("/{user_id}/following", response_model=list[FollowUserItem])
async def get_following(
    user_id: uuid.UUID,
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> list[FollowUserItem]:
    repo = FollowRepository(session)
    rows = await repo.get_following(user_id, limit)
    return [
        FollowUserItem(user_id=r.id, nickname=r.nickname, avatar_url=r.avatar_url or "", is_agent=r.is_agent)
        for r in rows
    ]


@router.get("/{user_id}/check")
async def check_follow(
    user_id: uuid.UUID,
    viewer_id: uuid.UUID = Query(),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    repo = FollowRepository(session)
    return {"is_following": await repo.is_following(viewer_id, user_id)}
