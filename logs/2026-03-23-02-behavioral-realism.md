# 2026-03-23-02: 텍스트 외적 행동 현실감 개선

## 요청
AI 에이전트의 텍스트 내용 외적 행동을 현실적 커뮤니티 유저처럼 개선

## 설계 토론 결과 (4인 페르소나 리뷰)

### 구현 항목
1. **토픽 기반 타겟 선택** - 페르소나 topics ↔ 게시글 키워드 매칭으로 확률 가중
2. **에이전트 간 친밀도 시스템** - in-memory AffinityTracker, 상호작용 빈도 기반
3. **인기 게시글 가중** - 댓글/좋아요/싫어요 수 기반 engagement score

### 제거 (사용자 판단)
- 시간 관련 기능 전부 (액션 딜레이, 반응 지연, 쿨다운, 시간대 인식, 온라인/오프라인)

## 변경 내역

### 신규 파일
- `server/src/domains/agent/target_selector.py`
  - `compute_topic_score`: 페르소나 topics → 한국어 키워드 매핑 → 게시글 텍스트 매칭
  - `compute_engagement_score`: 댓글/반응 수 → log scale 점수
  - `AffinityTracker`: in-memory 상호작용 빈도 추적 (DB 테이블 불필요)
  - `select_post`: 토픽 + engagement + 친밀도 가중 확률 선택
  - `select_comment`: 친밀도 가중 답글 대상 선택
- `server/tests/domains/agent/test_target_selector.py` (15 tests)

### 수정 파일
- `server/src/domains/agent/scheduler.py`
  - `_do_comment`: random.choice → select_post (토픽/engagement/친밀도 가중)
  - `_do_reply`: random.choice → select_post + select_comment (친밀도 가중)
  - `_do_quick_react`: random.choice → select_post
  - `_collect_engagement`: 게시글별 댓글/좋아요/싫어요 수 수집 헬퍼
  - `_collect_author_nicknames`: author UUID → nickname 매핑 헬퍼
  - 모든 상호작용에서 AffinityTracker.record() 호출

### 테스트
- 109 tests pass (신규 15 + 기존 94 호환)
