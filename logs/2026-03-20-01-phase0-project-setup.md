# Phase 0: 기술 스택 및 아키텍처 설계 - 프로젝트 초기 설정

**날짜**: 2026-03-20
**작업**: 기반 설정 (Phase 0)

## 변경 내역

### 1. 인프라 설정
- `docker-compose.yml`: PostgreSQL 16 + Ollama 서비스 구성
- `.gitignore`: Python/Node/Docker/IDE 패턴 설정

### 2. 백엔드 (server/)
- `pyproject.toml`: FastAPI, SQLAlchemy 2.0, Alembic, APScheduler, httpx, ruff, mypy, pytest 의존성
- `config/settings.py`: pydantic-settings 기반 환경 설정
- `config/ai_defaults.yaml`: AI 에이전트 수치 데이터 외부화
- `alembic/`: async 마이그레이션 환경 설정
- `src/main.py`: FastAPI 앱 팩토리 + CORS + health check
- `src/shared/`:
  - `database.py`: async SQLAlchemy 엔진 + 세션 팩토리
  - `base_model.py`: Base, TimestampMixin, UUIDPrimaryKeyMixin
  - `event_bus.py`: In-process async pub/sub 디스패처
  - `events.py`: PostCreated, CommentCreated, ReactionCreated 이벤트
  - `pagination.py`: PaginationParams, PaginatedResult
- `src/domains/`: user, post, comment, reaction, agent 스켈레톤 + README
- `tests/conftest.py`: httpx AsyncClient 픽스처
- `tests/test_health.py`: health check 테스트
- `data/personas/_schema.json`: AI 페르소나 YAML 스키마

### 3. 프런트엔드 (client/)
- Vite + React + TypeScript 프로젝트 스캐폴딩
- TailwindCSS v4 + @tailwindcss/vite 플러그인 설정
- @tanstack/react-query 통합
- API 프록시 설정 (/api -> localhost:8000)
- `src/shared/`: api-client, types, Layout 컴포넌트
- `src/domains/`: post, comment, reaction, user 디렉터리
- `src/pages/` 디렉터리

### 4. 문서
- CLAUDE.md 기술 스택 테이블 완성

## 도메인 구조 (5개)

| 도메인 | 책임 |
|--------|------|
| user | 계정, 인증 (인간+AI 통합) |
| post | 게시글 CRUD |
| comment | 댓글/답글 트리 구조 |
| reaction | 좋아요/싫어요 (polymorphic) |
| agent | AI 페르소나, 스케줄링, 콘텐츠 생성 |

## 다음 단계
- Phase 1: user -> post -> comment -> reaction 도메인 순차 구현
