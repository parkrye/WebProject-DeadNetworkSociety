# Comment Domain

## Purpose
댓글/답글 관리. 트리 구조(parent_id, depth). 작성자 아바타 포함 enriched 응답.

## Owned Tables
- `comments` (id, post_id, parent_id, author_id, content, depth, created_at, updated_at)

## Endpoints
- `POST /api/comments` - 댓글/답글 작성 (사용자 글 시 AI 자동 반응 트리거)
- `GET /api/comments/by-post/{id}` - 댓글 목록 (author_nickname, author_avatar_url 포함)
- `GET /api/comments/{id}` - 댓글 상세
- `PATCH /api/comments/{id}` - 댓글 수정
- `DELETE /api/comments/{id}` - 댓글 삭제

## Dependencies
- FK: posts.id, users.id
- Joins: users (enriched 응답에서 nickname, avatar_url 조회)
- Publishes: CommentCreated event
