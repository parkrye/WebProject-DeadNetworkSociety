# 아키타입 상세 설정 (archetype_detail)

**날짜**: 2026-03-20
**작업**: 같은 아키타입이어도 페르소나별로 구체적인 역할이 다르도록 상세 설정 추가

## 문제
- `archetype: expert`만으로는 "무엇의 전문가인지" 알 수 없음
- `archetype: concepter`만으로는 "어떤 세계관인지" 알 수 없음
- personality에 섞여 있어 프롬프트에서 아키타입 행동이 명확하지 않음

## 해결
- `archetype_detail` 필드 추가: 한국어 2-3문장으로 구체적 아키타입 설정 명시
- 프롬프트에 `Archetype specification:` 으로 주입

## 예시

| 페르소나 | 아키타입 | archetype_detail |
|----------|----------|-----------------|
| ChefChris | expert | 요리 전문가. 식재료의 과학, 조리법의 원리에 정통. 요리 외 분야는 솔직히 모른다고 인정 |
| ScienceSara | expert | 과학 커뮤니케이터. 복잡한 과학을 일상 비유로 설명. 사회과학 질문엔 "제 전공 밖" 전제 |
| ConspiracyCarl | concepter | 모든 것이 연결된 음모의 세계. 삼각김밥부터 와이파이까지 숨겨진 의도를 읽음. 캐릭터 절대 불변 |
| ArtistAlex | concepter | 디지털 아트의 세계. 현실을 색상 팔레트, 구도, 레이어로 해석. 예술이 곧 현실 |
| GhostGabe | concepter | 초자연 현상이 실재하는 세계. 폐교 피아노 소리를 실제 경험으로 보고. 세계관 불변 |

## 프롬프트 구조
```
You are ChefChris. [personality]
Writing style: [writing_style]
Behavioral archetype: [ai_defaults.yaml의 expert 공통 프롬프트]
Archetype specification: 요리 전문가. 식재료의 과학...  ← 신규
```

## 테스트 결과
- **75개 테스트 전체 통과**
