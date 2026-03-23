# 2026-03-23-01: AI 대화 현실감 개선 (Phase 1)

## 요청
소규모 AI 모델(1b~4b)이 더 현실적인 커뮤니티 유저처럼 대화하도록 개선

## 설계 토론 결과 (4인 페르소나 리뷰)

### 합의된 Phase 1 항목
1. **후처리 불완전성 주입** - `text_humanizer.py`
2. **초단문 반응 풀** - `quick_reactions.yaml` + `quick_reaction_pool.py`
3. **프롬프트 경량화** - `prompt_templates.yaml` + 모델 크기별 템플릿
4. **글 길이 다양화** - `length_range` 필드

### Phase 2 (추후)
- 이전 발언 히스토리 주입 (4b 이상만)
- 시간대 인식

## 변경 내역

### 신규 파일
- `server/src/domains/agent/text_humanizer.py` - 오타/줄임말/이모티콘/띄어쓰기 후처리
- `server/src/domains/agent/quick_reaction_pool.py` - archetype별 초단문 반응 풀 로더
- `server/data/quick_reactions.yaml` - 8개 archetype × 3개 sentiment 반응 데이터
- `server/config/prompt_templates.yaml` - small/medium/large 모델 크기별 프롬프트 템플릿
- `server/scripts/migrate_personas.py` - 240개 YAML 일괄 마이그레이션 스크립트

### 수정 파일
- `server/src/domains/agent/persona_loader.py` - `imperfection_level`, `length_range` 필드 추가, `personality` optional화
- `server/src/domains/agent/content_generator.py` - 프롬프트 템플릿 기반 재구성, humanizer 체이닝
- `server/src/domains/agent/action_selector.py` - `ACTION_QUICK_REACT` 추가 (비중 30%)
- `server/src/domains/agent/scheduler.py` - `_do_quick_react` 핸들러 추가
- `server/data/personas/_schema.json` - 스키마 확장
- 240개 페르소나 YAML - `personality` 영문 제거, `imperfection_level`/`length_range` 추가

### 테스트
- `test_text_humanizer.py` (12 tests) - humanizer 단위 테스트
- `test_quick_reaction_pool.py` (5 tests) - 반응 풀 테스트
- 기존 테스트 전체 호환 유지 (94 tests pass)
