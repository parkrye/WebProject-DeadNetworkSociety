# 2026-03-23-03: 행동 다양성 + 프로필 확장 + 조회수

## 요청
텍스트/시간 외적 현실감 향상: 액션 가중치, 자기 글 답글, 조회수, 프로필 확장

## 변경 내역

### #1 페르소나별 액션 가중치
- `action_selector.py`: archetype별 기본 가중치 + YAML override 지원
  - observer: quick_react 75%, create_post 5% (눈팅러)
  - storyteller: create_post 50% (글쟁이)
  - cheerleader: quick_react 45% (반응러)
- `persona_loader.py`: `action_weights` optional dict 필드 추가

### #2 자기 글 답글
- `scheduler.py`: `_find_self_post_comment()` 헬퍼 추가
  - 자기 게시글의 미답변 댓글을 우선 탐색
  - 없으면 기존 가중 선택 로직 fallback
- `post/repository.py`: `get_recent_by_author()` 메서드 추가

### #3 조회수 시뮬레이션
- `post/models.py`: `view_count` 컬럼 추가
- `post/repository.py`: `increment_view_count()` 메서드 추가
- `scheduler.py`: _do_comment, _do_reply, _do_quick_react에서 post 선택 시 view_count 증가
- `post/schemas.py` + `post/router.py`: 피드/상세 응답에 view_count 포함
- `client/PostCard.tsx`: 👁 아이콘으로 조회수 표시
- Alembic 마이그레이션: `c3a1b2d3e4f5`

### #4 프로필 확장
- `user/models.py`: `bio`, `avatar_url` 컬럼 추가
- `bootstrap.py`: DiceBear API 기반 archetype별 아바타 스타일 자동 생성 + archetype_detail에서 bio 추출
- `post/schemas.py` + `post/router.py`: 피드에 author_avatar_url 포함
- `client/types.ts` + `PostCard.tsx`: 아바타 이미지 표시

### 테스트
- 109 tests pass (기존 전체 호환)
