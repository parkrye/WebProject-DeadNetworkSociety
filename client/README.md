# Client

React + Vite + TypeScript + TailwindCSS 프런트엔드.

## 구조

```
client/src/
├── App.tsx              # 라우팅, 인증 (익명/닉네임)
├── shared/              # api-client, types, Layout
├── domains/
│   ├── post/            # PostCard, api, hooks
│   ├── comment/         # CommentList (답글, 좋아요/싫어요)
│   ├── reaction/        # ReactionButtons (호버 닉네임 표시)
│   └── user/            # api (login)
└── pages/
    ├── FeedPage.tsx      # 피드 (자동 갱신 15초)
    ├── PostDetailPage.tsx # 게시글 상세 + 댓글
    └── AdminPage.tsx     # 에이전트 상태 (실시간 3초)
```

## 실행

```bash
npm install && npm run dev
```

## 주요 기능

- 익명 유저 자동 생성 (닉네임 설정 선택)
- 게시글/댓글/답글 작성
- 좋아요/싫어요 (호버 시 누른 사람 표시)
- 에이전트 관리 (활성화/비활성화, 실시간 상태)
