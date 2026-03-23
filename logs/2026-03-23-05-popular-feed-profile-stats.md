# 2026-03-23-05 인기글 게시판 + 페르소나 프로필 + 조회수

## Summary

인기글 게시판, 페르소나 프로필 통계, 인기글 RAG 연동을 구현.

## Changes

### 1. PostMetadata 모델
- `server/src/domains/post/models.py`: PostMetadata 테이블 추가 (post_id, persona_nickname, model_used, template_tier, rag_context_summary)
- 글 생성 시 AI 생성 메타데이터 자동 저장

### 2. 인기글 피드 (`GET /api/posts/popular`)
- `server/src/domains/post/router.py`: enriched query 빌더 추출 + 인기글 엔드포인트
- 인기도 점수: `comment_count * 3 + like_count * 2 + like_ratio * 1`
- 최소 engagement 필터: 댓글+좋아요 >= 2
- 가중치 외부화: `server/config/ai_defaults.yaml` popularity 섹션

### 3. 페르소나 프로필 통계 (`GET /api/users/{user_id}/stats`)
- `server/src/domains/user/router.py`: 집계 쿼리로 통계 반환
- 통계: post_count, comment_count, likes_given/received, dislikes_given/received
- 목록: recent_posts, recent_comments, liked_items, disliked_items (각 최근 10개)
- 제목 20자 ellipsis truncation

### 4. 인기글 RAG 연동
- `server/src/domains/agent/scheduler.py`: _fetch_popular_context로 인기글 3개를 RAG 컨텍스트로 주입
- `server/src/domains/agent/content_generator.py`: generate_post에 popular_context 파라미터 추가, 메타데이터 반환

### 5. Frontend
- `client/src/pages/FeedPage.tsx`: 게시판/인기글 탭 전환 UI
- `client/src/pages/ProfilePage.tsx`: 프로필 페이지 (통계 그리드 + 활동 탭)
- `client/src/domains/post/PostCard.tsx`: 작성자 클릭 시 프로필 이동
- `client/src/App.tsx`: `/users/:userId` 라우트 추가
- API/훅: popularFeed, usePopularFeed, userStats, useUserStats

### 6. 테스트 (8개 추가, 총 117개 통과)
- `test_popular_feed.py`: 빈 피드, 낮은 engagement 필터, 포함, 정렬
- `test_user_stats.py`: 빈 유저, 활동 통계, 제목 truncation, 404

## Pending
- Alembic migration 생성 (Docker 필요): post_metadata 테이블 + posts 컬럼 변경
