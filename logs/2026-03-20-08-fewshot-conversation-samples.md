# Few-shot 대화 샘플 시스템

**날짜**: 2026-03-20
**작업**: 220K 라벨링 대화 데이터를 few-shot 예시로 프롬프트에 주입

## 데이터 분석
- **소스**: TL1 한국어 SNS/대화 데이터 (220,581 JSON)
- **카테고리**: 16개 (SNS 189K, 방송, 게임, 음식, 일상, 취미 등)
- **토픽**: 9개 대분류, 50+ 세부 토픽 (multi_topic 라벨)
- **평균 발화**: 대화당 13.6개

## 변경 내역

### 1. 전처리 스크립트
- `scripts/preprocess_conversations.py`: 220K 파일 → 810개 대표 샘플
- 27개 토픽으로 분류 (daily, gaming, food, health, finance 등)
- 토픽당 30개 샘플 선별
- 발화 수 필터 (6~20개), 길이 제한 (200자)
- 출력: `data/conversation_samples.json` (1.1MB)

### 2. SampleProvider
- `sample_provider.py`: 페르소나 토픽 → 대화 샘플 매칭
- `TOPIC_TO_SAMPLE_KEY` 매핑 (80+ 토픽 → 27개 샘플 키)
- 매칭 실패 시 랜덤 fallback
- lazy loading (첫 호출 시 1회 로드)

### 3. ContentGenerator 통합
- `_build_fewshot_section()`: 매 프롬프트에 한국어 대화 예시 주입
- 프롬프트 구조:
  ```
  [시스템 프롬프트: 페르소나 + 아키타입]

  실제 한국어 대화 예시:
  ---
  [대화 주제: 일상 생활]
  P01: 오늘 뭐해?
  P02: 집에서 쉬고 있어
  ---
  이와 비슷한 자연스러운 한국어 톤으로 작성하세요.

  [액션별 지시사항]
  ```

## 테스트 결과
- **71개 테스트 전체 통과** (3.39초)
- 신규 테스트 6개: 토픽 매칭, fallback, 파일 미존재, 포맷, 프로덕션 로드, 프롬프트 주입
