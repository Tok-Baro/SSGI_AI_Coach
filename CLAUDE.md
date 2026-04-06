# CLAUDE.md — 소상공인 AI 경영코치 하네스 규칙

> **이 파일은 AI 에이전트가 모든 작업 전/후에 반드시 참조하는 "진실의 단일 원천(SSOT)"입니다.**
> 변경 시 팀 리드(정수현) 승인 필요.

---

## 0. 하네스 프로토콜

```
[작업 시작 전]
1. progress.md를 읽고 현재 위치를 파악한다.
2. 이 파일(CLAUDE.md)의 규칙을 확인한다.
3. architecture.md에서 변경 대상의 의존관계를 파악한다.

[작업 중]
4. 논리적 충돌 발생 시 → 작업을 멈추고 사용자에게 승인을 요청한다.
5. 3개 이상 파일을 동시 변경 시 → 변경 이유를 먼저 설명한다.
6. 외부 API 호출부 수정 시 → 반드시 retry + fallback 패턴을 유지한다.

[작업 완료 후]
7. CLAUDE.md 규칙을 준수했는지 셀프 체크한다.
8. progress.md에 변경 사항을 업데이트한다.
9. 빌드/타입체크 검증 후 결과를 보고한다.
```

---

## 1. 프로젝트 개요

- **서비스**: 소상공인 AI 경영코치 (서울시 빅데이터 경진대회 2026)
- **핵심 차별점**: 손실 프레이밍 + k-anonymity 사회적 증거 + RAG 매칭
- **한 줄 원칙**: "추천합니다"가 아니라 **"놓치고 있습니다"**

---

## 2. 기술 스택 (변경 금지)

| 레이어 | 기술 | 버전 잠금 |
|--------|------|-----------|
| Frontend | Next.js (App Router) + TypeScript + Tailwind | 14.x |
| Backend | FastAPI + SQLAlchemy (async) | Python 3.11+ |
| Database | PostgreSQL | 15.x |
| Vector DB | ChromaDB | 0.5.x |
| AI Model | GPT-4o + text-embedding-3-small | OpenAI API |
| 인증 | Kakao OAuth → JWT (HS256) | - |
| 배포 | Vercel (FE) + Railway (BE) | - |

> **금지**: 스택 변경, ORM 교체, 인증 방식 변경은 사전 승인 없이 불가.

---

## 3. 코딩 규칙

### 3.1 Backend (Python)

```
- 타입 힌트 필수 (모든 함수 인자 + 반환값)
- Pydantic v2 스키마로 요청/응답 검증
- DB 세션은 반드시 `get_db()` 의존성 주입으로 관리
- 외부 API 호출은 반드시 `@retry_async` 데코레이터 적용
- 에러 발생 시 HTTPException으로 한국어 메시지 반환
- print() 금지 → logger 사용
- 환경변수는 config.py의 Settings 클래스에서만 관리
```

### 3.2 Frontend (TypeScript)

```
- "use client" 지시어 명시 (서버/클라이언트 컴포넌트 구분)
- API 호출은 반드시 api.ts의 ApiClient 메서드를 통해
- 모든 API 호출에 에러 핸들링 (.catch 또는 try-catch)
- useSearchParams는 반드시 <Suspense> 경계 안에서 사용
- Hooks는 조건부 호출 금지 (React Rules of Hooks)
- Zustand 스토어에 persist 미들웨어 필수
- 하드코딩 URL 금지 → 환경변수 사용
```

### 3.3 공통

```
- 커밋 메시지: 한국어 본문 + type prefix (feat/fix/docs/refactor/test)
- 시크릿 파일 커밋 절대 금지 (.env, firebase-sa.json, API_SECRETS.md)
- 새 외부 의존성 추가 시 반드시 사유 설명
- 데이터베이스 스키마 변경은 Alembic 마이그레이션으로만
```

---

## 4. 아키텍처 제약 (Architecture Decision Records)

| ADR# | 결정 | 근거 | 변경 금지 |
|------|------|------|-----------|
| 001 | 손실 프레이밍 메시지 | 행동경제학 논문 근거, 경진대회 핵심 | YES |
| 002 | k-anonymity 임계값 = 10 | 개인정보 보호 + 통계적 유의성 | YES |
| 003 | 하루 1개 액션 (UniqueConstraint) | 정보 과부하 방지, UX 연구 근거 | YES |
| 004 | Kakao > FCM > silent fail | 카카오톡 도달률 최고, graceful degradation | NO |
| 005 | ChromaDB PersistentClient | 벡터 DB 비용 0원, MVP에 적합 | NO |
| 006 | JWT 30일 만료 | 소상공인 재접속 패턴 고려 | NO |

---

## 5. 파일 구조 규칙

```
backend/
  app/
    models/     → SQLAlchemy 모델만 (비즈니스 로직 금지)
    schemas/    → Pydantic 스키마만 (DB 로직 금지)
    routers/    → HTTP 핸들링만 (비즈니스 로직은 services로 위임)
    services/   → 핵심 비즈니스 로직 (DB 직접 접근 최소화)
    utils/      → 순수 유틸리티 (상태 없는 함수)
    tasks/      → APScheduler 크론 작업만

frontend/
  src/
    app/        → 페이지 컴포넌트 (라우팅)
    components/ → 재사용 UI 컴포넌트
    hooks/      → 커스텀 훅 (상태 관리)
    lib/        → API 클라이언트, Firebase 등 라이브러리
    types/      → TypeScript 인터페이스
```

> **금지**: 레이어 간 역방향 의존 (예: models에서 routers import)

---

## 6. 검증 체크리스트 (작업 후 필수)

```
[ ] Backend: Python import 에러 없음
[ ] Frontend: `npx next build` 성공
[ ] Frontend: TypeScript 타입체크 에러 0건
[ ] 새 API 엔드포인트 추가 시 → api.ts에 메서드 추가됨
[ ] 새 모델 추가 시 → Alembic 마이그레이션 생성됨
[ ] 시크릿 파일이 git에 포함되지 않음
[ ] progress.md 업데이트됨
```

---

## 7. 비상 프로토콜

### Context Drift (AI가 규칙을 잊었을 때)
```
"CLAUDE.md를 다시 읽고, progress.md의 현재 위치를 확인한 후,
마지막 성공 커밋부터 다시 시작해."
```

### Cascading Failure (연쇄 에러)
```
"작업을 중단해. git stash로 현재 변경사항을 임시 저장하고,
마지막 성공 커밋(git log)을 보여줘. 어디서부터 꼬였는지 분석하자."
```

### 폭주 방지 (3회 이상 같은 에러)
```
"같은 에러가 3번 반복되면 자동으로 멈춰.
에러 원인 분석 + 3가지 해결 방안을 제시하고 내 선택을 기다려."
```

---

## 8. 팀 역할

| 이름 | 역할 | 담당 영역 |
|------|------|-----------|
| 정수현 | PM / 데이터 | 기획, 서울시 API, 시드 데이터, 하네스 관리 |
| 구혁모 | 백엔드 | FastAPI, DB, 인증, 배포 |
| 나은민 | 프론트엔드 | Next.js, UI/UX, PWA |
| 이준수 | AI | RAG, GPT-4o 프롬프트, 크론 배치 |

---

## 9. Git 리모트

```
origin: git@github.com:Tok-Baro/SSGI_AI_Coach.git
branch: main (단일 브랜치, feature branch는 추후)
```

> **마지막 업데이트**: 2026-04-06
