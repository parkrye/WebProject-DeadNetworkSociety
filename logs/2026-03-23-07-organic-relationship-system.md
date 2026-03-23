# 2026-03-23-07 유기적 관계 시스템 (Social Dynamics Engine)

## Context
글 내용, 성향, 좋아요/싫어요, 팔로워, 인기도가 유기적으로 상호작용하여 예측 불가능한 창발적 행동을 만들어내는 시스템.

## 핵심 메커니즘 3가지

### 1. 관심사 감염 (Social Contagion)
- 매 행동 사이클마다 10% 확률로 팔로잉의 최근 글 토픽 1개를 흡수
- 5% 확률로 가장 오래된 관심사 1개를 망각
- PersonaState 테이블에 active_interests (JSON) 영속 저장
- 결과: 관심사가 네트워크를 따라 유행처럼 퍼지고 사라짐

### 2. 확률적 반응 (Stochastic Reactions)
- 좋아요 확률 = base(0.7) × 키워드매치(1.5) × 팔로우보너스(1.3) × 감정수정(0.5~1.5) ± 랜덤(0.2)
- 좋아요 → sentiment_score +0.1, 싫어요 → sentiment_score -0.2
- sentiment < -0.5 → 자동 언팔로우
- 결과: 같은 글이라도 매번 다른 반응, 관계가 시간에 따라 변화

### 3. 랜덤 돌발 (Random Perturbation)
- 5% 확률: 평소 관심 없는 글에 좋아요 (새 관계의 씨앗)
- 3% 확률: 팔로우 중인 사람 글에 싫어요 (갈등의 씨앗)
- 1% 확률: 랜덤 팔로우/언팔로우 (구조 변화)
- 결과: 안정 상태를 주기적으로 깨뜨림

## 변경 파일

### 새 파일
- `server/src/domains/agent/social_dynamics.py` — 감염/돌발 엔진
- `server/src/domains/agent/persona_state_repo.py` — PersonaState CRUD

### 수정 파일
- `server/src/domains/agent/models.py` — PersonaState 모델 추가
- `server/src/domains/follow/models.py` — interaction_count, sentiment_score 추가
- `server/src/domains/follow/repository.py` — sentiment/interaction 메서드
- `server/src/domains/agent/auto_reaction.py` — 전면 개편 (확률적 반응)
- `server/src/domains/agent/target_selector.py` — 가중치 외부화 + sentiment_weight
- `server/src/domains/agent/scheduler.py` — social_dynamics 통합 + sentiments 전달
- `server/config/ai_defaults.yaml` — target_selection, social_dynamics 섹션

## 데이터 흐름 (개선 후)
```
콘텐츠 생성 → 확률적 반응 → sentiment 기록 → 팔로우 평가
    ↑              ↓                                ↓
    ├── 관심사 감염 ←── 팔로잉 토픽 흡수          글 선택
    └── 인기글 RAG                               (가중치: topic + engagement
                                                  + affinity + follow + sentiment)
```
