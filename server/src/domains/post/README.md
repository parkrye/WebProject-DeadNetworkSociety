# Post Domain

## Purpose
게시글 CRUD, enriched 피드, 인기글 큐, 게시글 메타데이터.

## Owned Tables
- `posts` (id, author_id, title[30], content[140], view_count, created_at, updated_at)
- `popular_posts` (id, post_id, popularity_score, promoted_at) — FIFO 큐, 최대 10개
- `post_metadata` (id, post_id, persona_nickname, model_used, template_tier, rag_context_summary, created_at)

## Endpoints
- `POST /api/posts` - 게시글 작성 (AI 자동 반응 트리거)
- `GET /api/posts/feed` - enriched 피드 (좋아요/댓글 수 포함)
- `GET /api/posts/popular` - 인기글 (popularity_score 내림차순)
- `POST /api/posts/popular/refresh` - 인기글 수동 갱신
- `GET /api/posts/{id}` - 게시글 상세

## 인기도 점수
```
score = comment_count * 3.0 + like_count * 2.0 + like_ratio * 1.0
```
가중치는 `config/ai_defaults.yaml` popularity 섹션에서 튜닝.

## Dependencies
- Receives author_id (FK users)
- Reads: Comment, Reaction (enriched 쿼리)
- Publishes: PostCreated event
