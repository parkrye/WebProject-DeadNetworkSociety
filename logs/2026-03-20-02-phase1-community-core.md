# Phase 1: 커뮤니티 코어 도메인 구현

**날짜**: 2026-03-20
**작업**: 4개 핵심 도메인 (user, post, comment, reaction) 구현

## 변경 내역

### 1. User 도메인
- `models.py`: users 테이블 (nickname UNIQUE, is_agent)
- `schemas.py`: UserCreate, UserUpdate, UserResponse
- `repository.py`: CRUD + 페이지네이션 + nickname 중복 검사
- `service.py`: 비즈니스 로직 + 409 Conflict 처리
- `router.py`: POST/GET/PATCH/DELETE `/api/users`
- 11개 테스트 통과

### 2. Post 도메인
- `models.py`: posts 테이블 (author_id FK, title, content)
- `schemas.py`: PostCreate, PostUpdate, PostResponse
- `repository.py`: CRUD + 페이지네이션
- `service.py`: 비즈니스 로직 + PostCreated 이벤트 발행
- `router.py`: POST/GET/PATCH/DELETE `/api/posts`
- 7개 테스트 통과

### 3. Comment 도메인
- `models.py`: comments 테이블 (post_id FK, parent_id self-ref FK, depth)
- `schemas.py`: CommentCreate, CommentUpdate, CommentResponse
- `repository.py`: CRUD + post별 조회 + 페이지네이션
- `service.py`: 비즈니스 로직 + depth 자동 계산 + CommentCreated 이벤트
- `router.py`: POST/GET/PATCH/DELETE `/api/comments`, GET `/api/comments/by-post/{post_id}`
- 7개 테스트 통과

### 4. Reaction 도메인
- `models.py`: reactions 테이블 (polymorphic target_type+target_id, UNIQUE 제약)
- `schemas.py`: ReactionCreate, ReactionResponse, ReactionCountResponse (regex 패턴 검증)
- `repository.py`: toggle 지원 (create/delete) + 집계
- `service.py`: toggle 로직 (같은 타입=제거, 다른 타입=전환) + ReactionCreated 이벤트
- `router.py`: POST `/api/reactions` (토글), GET `/api/reactions/counts/{type}/{id}`
- 7개 테스트 통과

### 5. 인프라 수정
- `base_model.py`: server_default -> Python-side default로 변경 (SQLite 호환)
- `conftest.py`: aiosqlite 인메모리 DB + 모델 임포트 + dependency override
- `main.py`: 4개 도메인 라우터 등록

## 테스트 결과
- **33개 테스트 전체 통과** (1.70초)
