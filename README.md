# 소상공인 AI 경영코치

> "추천합니다"가 아니라 **"놓치고 있습니다"** — 행동경제학 손실 프레이밍 기반 AI 경영 코치

서울시 빅데이터 활용 경진대회 2026 (창업 부문) 출품작

## 핵심 아이디어

소상공인이 놓치고 있는 **지원금, 매출 기회, 경쟁 대응**을 손실 프레이밍으로 매일 1개씩 알려주는 서비스.

- 손실 회피 편향(Loss Aversion) 활용 → 행동 전환율 2배↑
- k-anonymity 사회적 증거 → "같은 동네 43곳이 신청했어요"
- RAG 기반 지원사업 매칭 → 사업자 맞춤 추천
- QR 쿠폰 + 유동인구 연계 → 실시간 매출 기회 포착

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| **Frontend** | Next.js 14 (App Router) + TypeScript + Tailwind CSS + PWA |
| **Backend** | FastAPI (Python 3.11+) + SQLAlchemy 2.0 (async) |
| **Database** | PostgreSQL 15 + ChromaDB (벡터 DB) |
| **AI** | GPT-4o + OpenAI text-embedding-3-small (1536 dim) |
| **인증** | Kakao OAuth → JWT (HS256) |
| **배포** | Vercel (프론트) + Railway (백엔드 + PostgreSQL) |

## 프로젝트 구조

```
ssgi/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 앱 + APScheduler
│   │   ├── config.py            # Pydantic Settings
│   │   ├── database.py          # Async SQLAlchemy
│   │   ├── models/              # 5 테이블 (User, DailyAction, Subsidy, Coupon, Notification)
│   │   ├── schemas/             # 13 Pydantic 스키마
│   │   ├── routers/             # 7 라우터 (18 API 엔드포인트)
│   │   ├── services/            # 8 서비스 (Kakao, NTS, Seoul, RAG, AI, Coupon, Social, Notification)
│   │   ├── utils/               # auth, retry, cache, loss_framing
│   │   └── tasks/               # 3 크론 (daily_action, seoul_sync, subsidy_index)
│   ├── alembic/                 # DB 마이그레이션
│   ├── requirements.txt
│   ├── Dockerfile
│   └── railway.toml
├── frontend/
│   ├── src/
│   │   ├── app/                 # 7 페이지 (Next.js App Router)
│   │   ├── components/          # STTButton
│   │   ├── hooks/               # useAuth, useSTT
│   │   ├── lib/                 # api.ts, firebase.ts
│   │   └── types/               # TypeScript 인터페이스
│   ├── public/                  # manifest.json, sw.js, offline.html
│   └── next.config.js           # next-pwa 설정
├── docker-compose.yml           # 로컬 PostgreSQL
└── IMPLEMENTATION_SPEC.md       # 구현 명세서
```

## API 엔드포인트 (18개)

| Method | Path | 설명 |
|--------|------|------|
| POST | `/auth/kakao/callback` | 카카오 로그인 → JWT 발급 |
| GET | `/auth/me` | 현재 유저 정보 |
| POST | `/auth/fcm-token` | FCM 토큰 등록 |
| POST | `/onboarding/verify-business` | 사업자번호 검증 (국세청) |
| GET | `/onboarding/search-business` | 상호명 검색 (카카오 로컬) |
| POST | `/onboarding/complete` | 온보딩 완료 + 첫 액션 생성 |
| GET | `/dashboard` | 대시보드 집계 데이터 |
| GET | `/subsidies/matches` | RAG 지원사업 매칭 |
| POST | `/subsidies/apply-draft` | 사업계획서 초안 (GPT-4o) |
| GET | `/actions/today` | 오늘의 액션 |
| GET | `/actions/history` | 액션 히스토리 |
| POST | `/actions/{id}/complete` | 액션 완료 처리 |
| POST | `/coupons/create` | QR 쿠폰 생성 |
| GET | `/coupons` | 쿠폰 목록 |
| GET | `/coupons/{id}` | 쿠폰 상세 |
| POST | `/coupons/{id}/scan` | 쿠폰 스캔 |
| POST | `/voice/query` | 음성 질의 (STT → GPT-4o) |
| GET | `/health` | 헬스체크 |

## 로컬 개발 환경 설정

### 사전 요구사항

- Python 3.11+
- Node.js 18+
- Docker (PostgreSQL용)

### 1. 환경변수 설정

```bash
# backend/.env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_coach
KAKAO_REST_API_KEY=your_key
KAKAO_CLIENT_SECRET=your_secret
KAKAO_REDIRECT_URI=http://localhost:3000/auth/kakao/callback
NTS_API_KEY=your_key
SEOUL_API_KEY=your_key
OPENAI_API_KEY=your_key
SECRET_KEY=your_secret_key
CORS_ORIGINS=http://localhost:3000

# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_KAKAO_REST_API_KEY=your_key
NEXT_PUBLIC_KAKAO_REDIRECT_URI=http://localhost:3000/auth/kakao/callback
```

### 2. 데이터베이스 실행

```bash
docker compose up -d
```

### 3. 백엔드 실행

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### 4. 프론트엔드 실행

```bash
cd frontend
npm install
npm run dev
```

### 5. 접속

- 프론트엔드: http://localhost:3000
- 백엔드 API: http://localhost:8000
- API 문서 (Swagger): http://localhost:8000/docs

## 크론 작업

| 작업 | 스케줄 | 설명 |
|------|--------|------|
| `daily_action_batch` | 매일 07:00 | 전체 유저 일일 액션 생성 + 알림 |
| `seoul_data_sync` | 매주 월 03:00 | 서울시 API 데이터 사전 캐싱 |
| `subsidy_indexer` | 매주 월 04:00 | 보조금 ChromaDB 재인덱싱 |

## 외부 API 의존성

| API | 용도 |
|-----|------|
| Kakao OAuth | 소셜 로그인 |
| Kakao Local | 상호명 검색 |
| Kakao Talk (나에게 보내기) | 알림 발송 |
| 국세청 사업자 확인 | 사업자번호 검증 |
| 서울시 상권분석 (VwsmTrdarSelngQq) | 매출 데이터 |
| 서울시 생활인구 (SPOP_LOCAL_RESD_DONG) | 유동인구 |
| 서울시 문화행사 (culturalEventInfo) | 주변 행사 |
| OpenAI GPT-4o | AI 액션 생성, 사업계획서, 음성 응답 |
| OpenAI Embeddings | RAG 벡터 임베딩 |
| Firebase Cloud Messaging | 푸시 알림 |

## 배포

### Backend (Railway)

```bash
# railway.toml 이미 설정됨
# Railway 대시보드에서 PostgreSQL + 환경변수 설정 후 deploy
```

### Frontend (Vercel)

```bash
# Vercel 대시보드에서 frontend/ 디렉토리 지정 + 환경변수 설정 후 deploy
```

## 팀

| 역할 | 이름 | 담당 |
|------|------|------|
| 기획/데이터 | 정수현 | PM, 데이터 수집, 서울시 API 검증, 시드 데이터 |
| 백엔드 | 구혁모 | FastAPI, DB, 인증, 외부 API, 배포 |
| 프론트엔드 | 나은민 | Next.js, UI/UX, PWA |
| AI | 이준수 | RAG, GPT-4o 프롬프트, 크론 배치 |

## 라이선스

Seoul Big Data Competition 2026 출품작. All rights reserved.
