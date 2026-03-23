import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domains.comment.models import Comment
from src.domains.follow.repository import FollowRepository
from src.domains.post.models import PopularPost, Post
from src.domains.reaction.models import Reaction
from src.domains.user.models import User
from src.domains.user.schemas import (
    ActivityItem,
    RankingEntry,
    UserCreate,
    UserLogin,
    UserProfileStats,
    UserResponse,
    UserUpdate,
)
from src.domains.user.service import UserService
from src.shared.database import get_session
from src.shared.pagination import PaginationParams

router = APIRouter(prefix="/api/users", tags=["users"])

ACTIVITY_LIST_LIMIT = 10
TITLE_TRUNCATE_LENGTH = 20


def _get_service(session: AsyncSession = Depends(get_session)) -> UserService:
    return UserService(session)


def _truncate(text: str, max_len: int = TITLE_TRUNCATE_LENGTH) -> str:
    return text[:max_len] + "..." if len(text) > max_len else text


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    data: UserCreate,
    service: UserService = Depends(_get_service),
) -> UserResponse:
    user = await service.create_user(data)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=UserResponse)
async def login_or_register(
    data: UserLogin,
    service: UserService = Depends(_get_service),
) -> UserResponse:
    user = await service.login_or_register(data)
    return UserResponse.model_validate(user)


@router.get("", response_model=list[UserResponse])
async def get_users(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=500),
    service: UserService = Depends(_get_service),
) -> list[UserResponse]:
    result = await service.get_users(PaginationParams(page=page, size=size))
    return [UserResponse.model_validate(u) for u in result.items]


@router.get("/ranking", response_model=list[RankingEntry])
async def get_ranking(
    session: AsyncSession = Depends(get_session),
) -> list[RankingEntry]:
    """Rank all users by total popularity score from popular_posts."""
    stmt = (
        select(
            User.id,
            User.nickname,
            User.avatar_url,
            User.is_agent,
            func.coalesce(func.sum(PopularPost.popularity_score), 0.0).label("total_score"),
            func.count(PopularPost.id).label("post_count"),
        )
        .outerjoin(Post, User.id == Post.author_id)
        .outerjoin(PopularPost, Post.id == PopularPost.post_id)
        .group_by(User.id)
        .having(func.coalesce(func.sum(PopularPost.popularity_score), 0.0) > 0)
        .order_by(func.sum(PopularPost.popularity_score).desc())
    )
    result = await session.execute(stmt)
    return [
        RankingEntry(
            rank=i + 1,
            user_id=row.id,
            nickname=row.nickname,
            avatar_url=row.avatar_url or "",
            is_agent=row.is_agent,
            total_popularity_score=float(row.total_score),
            popular_post_count=row.post_count,
        )
        for i, row in enumerate(result.all())
    ]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    service: UserService = Depends(_get_service),
) -> UserResponse:
    user = await service.get_user(user_id)
    return UserResponse.model_validate(user)


@router.get("/{user_id}/stats", response_model=UserProfileStats)
async def get_user_stats(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> UserProfileStats:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Aggregate counts
    post_count = (await session.execute(
        select(func.count()).select_from(Post).where(Post.author_id == user_id)
    )).scalar_one()

    comment_count = (await session.execute(
        select(func.count()).select_from(Comment).where(Comment.author_id == user_id)
    )).scalar_one()

    likes_given = (await session.execute(
        select(func.count()).select_from(Reaction)
        .where(Reaction.user_id == user_id, Reaction.reaction_type == "like")
    )).scalar_one()

    dislikes_given = (await session.execute(
        select(func.count()).select_from(Reaction)
        .where(Reaction.user_id == user_id, Reaction.reaction_type == "dislike")
    )).scalar_one()

    # Likes/dislikes received on user's posts
    likes_received = (await session.execute(
        select(func.count()).select_from(Reaction)
        .join(Post, (Reaction.target_id == Post.id) & (Reaction.target_type == "post"))
        .where(Post.author_id == user_id, Reaction.reaction_type == "like")
    )).scalar_one()

    dislikes_received = (await session.execute(
        select(func.count()).select_from(Reaction)
        .join(Post, (Reaction.target_id == Post.id) & (Reaction.target_type == "post"))
        .where(Post.author_id == user_id, Reaction.reaction_type == "dislike")
    )).scalar_one()

    # Recent posts (limit 10)
    recent_posts_result = await session.execute(
        select(Post)
        .where(Post.author_id == user_id)
        .order_by(Post.created_at.desc())
        .limit(ACTIVITY_LIST_LIMIT)
    )
    recent_posts = [
        ActivityItem(
            id=p.id,
            type="post",
            title=_truncate(p.title),
            view_count=p.view_count,
            created_at=p.created_at,
        )
        for p in recent_posts_result.scalars().all()
    ]

    # Recent comments (limit 10)
    recent_comments_result = await session.execute(
        select(Comment)
        .where(Comment.author_id == user_id)
        .order_by(Comment.created_at.desc())
        .limit(ACTIVITY_LIST_LIMIT)
    )
    recent_comments = [
        ActivityItem(
            id=c.id,
            type="comment",
            title=_truncate(c.content),
            created_at=c.created_at,
        )
        for c in recent_comments_result.scalars().all()
    ]

    # Liked items (posts only, limit 10)
    liked_result = await session.execute(
        select(Post)
        .join(Reaction, (Reaction.target_id == Post.id) & (Reaction.target_type == "post"))
        .where(Reaction.user_id == user_id, Reaction.reaction_type == "like")
        .order_by(Reaction.created_at.desc())
        .limit(ACTIVITY_LIST_LIMIT)
    )
    liked_items = [
        ActivityItem(
            id=p.id,
            type="post",
            title=_truncate(p.title),
            view_count=p.view_count,
            created_at=p.created_at,
        )
        for p in liked_result.scalars().all()
    ]

    # Disliked items (posts only, limit 10)
    disliked_result = await session.execute(
        select(Post)
        .join(Reaction, (Reaction.target_id == Post.id) & (Reaction.target_type == "post"))
        .where(Reaction.user_id == user_id, Reaction.reaction_type == "dislike")
        .order_by(Reaction.created_at.desc())
        .limit(ACTIVITY_LIST_LIMIT)
    )
    disliked_items = [
        ActivityItem(
            id=p.id,
            type="post",
            title=_truncate(p.title),
            view_count=p.view_count,
            created_at=p.created_at,
        )
        for p in disliked_result.scalars().all()
    ]

    # Popularity: best rank among current popular posts + total score
    popular_result = await session.execute(
        select(PopularPost.popularity_score)
        .join(Post, PopularPost.post_id == Post.id)
        .where(Post.author_id == user_id)
        .order_by(PopularPost.popularity_score.desc())
    )
    user_popular_scores = [r[0] for r in popular_result.all()]
    total_popularity_score = sum(user_popular_scores)

    best_popular_rank = None
    if user_popular_scores:
        best_score = user_popular_scores[0]
        all_scores_result = await session.execute(
            select(PopularPost.popularity_score)
            .order_by(PopularPost.popularity_score.desc())
        )
        all_scores = [r[0] for r in all_scores_result.all()]
        for i, s in enumerate(all_scores):
            if s <= best_score:
                best_popular_rank = i + 1
                break

    # Follow counts
    follow_repo = FollowRepository(session)
    followers_count = await follow_repo.count_followers(user_id)
    following_count = await follow_repo.count_following(user_id)

    return UserProfileStats(
        user_id=user.id,
        nickname=user.nickname,
        bio=user.bio,
        avatar_url=user.avatar_url,
        is_agent=user.is_agent,
        post_count=post_count,
        comment_count=comment_count,
        likes_given=likes_given,
        likes_received=likes_received,
        dislikes_given=dislikes_given,
        dislikes_received=dislikes_received,
        followers_count=followers_count,
        following_count=following_count,
        best_popular_rank=best_popular_rank,
        total_popularity_score=total_popularity_score,
        recent_posts=recent_posts,
        recent_comments=recent_comments,
        liked_items=liked_items,
        disliked_items=disliked_items,
    )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    service: UserService = Depends(_get_service),
) -> UserResponse:
    user = await service.update_user(user_id, data)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: uuid.UUID,
    service: UserService = Depends(_get_service),
) -> None:
    await service.delete_user(user_id)
