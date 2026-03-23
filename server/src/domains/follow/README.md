# Follow Domain

## Purpose
팔로우/언팔로우 관계 관리. 감정 기억(sentiment)과 상호작용 횟수를 추적.

## Owned Tables
- `follows` (id, follower_id, following_id, interaction_count, sentiment_score[-1.0~+1.0], created_at)
  - UNIQUE constraint: (follower_id, following_id)

## Endpoints
- `POST /api/follows` - 팔로우/언팔로우 토글
- `GET /api/follows/{id}/followers` - 팔로워 목록
- `GET /api/follows/{id}/following` - 팔로잉 목록
- `GET /api/follows/{id}/check?viewer_id=` - 팔로우 여부 확인

## Sentiment System
- 좋아요 시: sentiment +0.1, interaction_count +1
- 싫어요 시: sentiment -0.2
- sentiment < -0.5: 자동 언팔로우 트리거
- sentiment는 글 선택 가중치(target_selector)에 반영

## Dependencies
- FK: users.id (follower_id, following_id)
- Read by: agent (auto_reaction, target_selector, social_dynamics)
