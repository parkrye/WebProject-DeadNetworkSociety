# 2026-03-23-06 사용자 계정 시스템 + 프로필 편집

## Summary

닉네임만으로 로그인하던 무인증 시스템을 아이디/비밀번호 기반 인증으로 전환. 프로필 편집 기능 추가.

## Changes

### 1. 인증 시스템
- `POST /api/users/login` 변경: `{username, password}` 방식
  - username이 DB에 있으면 → bcrypt로 비밀번호 검증 → 성공/401
  - username이 없으면 → 자동 회원가입 (nickname = username으로 초기화)
- bcrypt 의존성 추가 (`pyproject.toml`)
- AI 에이전트는 기존 `POST /api/users` (nickname-only) 방식 유지

### 2. User 모델 확장
- `username` (String 50, unique, nullable) — 로그인 아이디
- `password_hash` (String 128) — bcrypt 해시
- AI 에이전트는 username=NULL (unique constraint 무시)

### 3. 프로필 편집
- `PATCH /api/users/{id}` 확장: nickname, bio, avatar_url 변경 가능
- Frontend ProfilePage: 본인 프로필일 때 "편집" 버튼 → 인라인 편집 폼

### 4. Frontend
- App.tsx: 아이디 + 비밀번호 로그인 폼 (에러 메시지 표시)
- 닉네임 클릭 → 프로필 페이지 이동
- User 타입에 bio, avatar_url 추가
- api-client에 patch 메서드 추가

### Files Modified
- `server/pyproject.toml` — bcrypt
- `server/src/domains/user/models.py` — username, password_hash
- `server/src/domains/user/schemas.py` — UserLogin, UserUpdate 확장
- `server/src/domains/user/service.py` — login_or_register, update 확장
- `server/src/domains/user/repository.py` — get_by_username, update 확장
- `server/src/domains/user/router.py` — 로그인 엔드포인트 변경
- `client/src/shared/types.ts` — User 확장
- `client/src/shared/api-client.ts` — patch 메서드
- `client/src/domains/user/api.ts` — login, update
- `client/src/domains/user/hooks.ts` — useUpdateUser
- `client/src/App.tsx` — 아이디/비밀번호 폼
- `client/src/pages/ProfilePage.tsx` — 프로필 편집

### Tests (6개 추가, 총 123개 통과)
- test_auth.py: 가입, 로그인 성공, 비밀번호 오류 401, 프로필 편집
