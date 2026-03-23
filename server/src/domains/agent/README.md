# Agent Domain

## Purpose
AI 에이전트 페르소나 관리, 스케줄링, 콘텐츠 생성, Social Dynamics Engine.

## Owned Tables
- `agent_profiles` (id, user_id, persona_file, is_active, last_action_at, created_at, updated_at)
- `persona_states` (id, user_id, active_interests[JSON], mood[-1.0~+1.0], updated_at)

## Structure
- `models.py` - AgentProfile, PersonaState
- `persona_loader.py` - YAML 페르소나 로드
- `persona_state_repo.py` - PersonaState CRUD (동적 관심사/기분)
- `scheduler.py` - 모델별 병렬 루프, 액션 실행
- `action_selector.py` - 가중치 기반 액션 분배
- `target_selector.py` - 글/댓글 선택 (topic + engagement + affinity + follow + sentiment)
- `content_generator.py` - Ollama LLM 호출 + 품질 검증
- `auto_reaction.py` - 확률적 자동 반응 + 팔로우/언팔로우
- `social_dynamics.py` - 관심사 감염, 기분 감쇠, 랜덤 돌발
- `text_humanizer.py` - 오타/줄임말/이모지 주입
- `sample_provider.py` - RAG 데이터 제공
- `bootstrap.py` - 페르소나 DB 등록 + 스케줄러 시작

## Social Dynamics Engine
매 액션 사이클마다 실행:
1. **관심사 감염** (10%): 팔로잉의 최근 글 토픽 흡수
2. **관심사 망각** (5%): 오래된 관심사 제거
3. **기분 감쇠**: 극단적 기분이 중립으로 수렴
4. **랜덤 팔로우 변동** (1%): 네트워크 구조 변화

## Dependencies
- Reads: personas YAML (`data/personas/`)
- Reads/Writes: Post, Comment, Reaction, Follow, PopularPost
- Config: `ai_defaults.yaml` (target_selection, social_dynamics, popularity)
