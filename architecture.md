# architecture.md — 시스템 아키텍처 & 데이터 흐름

> **이 파일은 AI 에이전트가 코드 변경 전 의존관계를 파악하는 구조 지도입니다.**

---

## 1. 전체 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                         사용자 (소상공인)                      │
│                    PWA (모바일 브라우저)                        │
└─────────────┬───────────────────────────────┬───────────────┘
              │ HTTPS                         │ Kakao OAuth
              ▼                               ▼
┌─────────────────────┐           ┌──────────────────────┐
│   Vercel (Frontend)  │           │  Kakao Auth Server   │
│   Next.js 14 SSG     │           │  kauth.kakao.com     │
│   - 7 Pages          │           └──────────────────────┘
│   - Zustand Store    │
│   - Service Worker   │
└─────────┬────────────┘
          │ API Calls (fetch)
          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Railway (Backend)                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  FastAPI App                           │   │
│  │                                                       │   │
│  │  ┌─────────┐  ┌──────────┐  ┌──────────┐            │   │
│  │  │ Routers │→ │ Services │→ │  Models   │            │   │
│  │  │ (7개)    │  │ (8개)     │  │ (5 tables)│            │   │
│  │  └─────────┘  └────┬─────┘  └─────┬────┘            │   │
│  │                     │              │                   │   │
│  │         ┌───────────┼──────────────┤                  │   │
│  │         ▼           ▼              ▼                   │   │
│  │  ┌──────────┐ ┌──────────┐ ┌────────────┐            │   │
│  │  │ External │ │ ChromaDB │ │ PostgreSQL │            │   │
│  │  │   APIs   │ │ (Vector) │ │     15     │            │   │
│  │  └──────────┘ └──────────┘ └────────────┘            │   │
│  │                                                       │   │
│  │  ┌──────────────────────────────────┐                │   │
│  │  │ APScheduler (3 Cron Jobs)        │                │   │
│  │  │ 07:00 daily_action               │                │   │
│  │  │ Mon 03:00 seoul_sync             │                │   │
│  │  │ Mon 04:00 subsidy_index          │                │   │
│  │  └──────────────────────────────────┘                │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 의존관계 그래프 (모듈 간)

```
config.py ──────────────────────────────────────┐
    │                                            │
    ▼                                            ▼
database.py                                  모든 서비스
    │
    ▼
models/ ─────────────┐
    │                 │
    ▼                 ▼
schemas/          routers/ ──→ services/ ──→ utils/
                      │            │
                      │            ├──→ kakao_service.py
                      │            ├──→ nts_service.py
                      │            ├──→ seoul_api_service.py
                      │            ├──→ rag_service.py ──→ ChromaDB + OpenAI
                      │            ├──→ action_generator.py ──→ OpenAI
                      │            ├──→ coupon_service.py ──→ qrcode lib
                      │            ├──→ social_proof_service.py ──→ DB
                      │            └──→ notification_service.py ──→ Kakao + FCM
                      │
                      └──→ utils/auth.py (JWT 검증 Depends)
```

### 의존 규칙 (위반 금지)
```
models/  ──X──→ routers/     (역방향 금지)
schemas/ ──X──→ services/    (역방향 금지)
utils/   ──X──→ routers/     (역방향 금지)
tasks/   ──→ services/ ──→ models/  (단방향만 허용)
```

---

## 3. 사용자 여정 (데이터 흐름)

### 3.1 로그인 → 온보딩

```
[사용자] ──카카오 로그인──→ [카카오 서버]
                              │
                         인가코드 발급
                              │
                              ▼
[Frontend callback] ──POST /auth/kakao/callback──→ [Backend]
                                                      │
                                              1. 카카오 토큰 교환
                                              2. 사용자 정보 조회
                                              3. DB upsert (users)
                                              4. JWT 발급
                                                      │
                                                      ▼
[Frontend] ◀──── JWT + UserResponse ────────────────────┘
    │
    │ (onboarding_completed == false)
    ▼
[온보딩 페이지]
    │
    ├── Step 1: POST /onboarding/verify-business ──→ 국세청 API
    ├── Step 2: GET  /onboarding/search-business ──→ 카카오 로컬 API
    └── Step 3: POST /onboarding/complete ──→ [Backend]
                                                │
                                        1. User 정보 업데이트
                                        2. 서울시 API 3종 호출 (parallel)
                                        3. RAG 지원사업 매칭
                                        4. 첫 일일 액션 생성
                                        5. FCM 토큰 등록
```

### 3.2 대시보드 (매일)

```
[07:00 Cron] ──→ generate_daily_actions_for_all()
                    │
                    ├── 전체 온보딩 완료 유저 조회
                    ├── 유저별 GPT-4o 액션 생성 (fallback: 결정론적)
                    ├── DB 저장 (daily_actions)
                    └── 알림 전송 (Kakao > FCM)

[사용자 접속] ──GET /dashboard──→ [Backend]
                                     │
                             1. 오늘의 액션 조회
                             2. 지원사업 RAG 매칭 (top 3)
                             3. 유동인구 데이터 (캐시)
                             4. 쿠폰 통계 집계
                             5. 손실 프레이밍 메시지 생성
                             6. 위험 점수 계산
                                     │
                                     ▼
[Frontend] ◀── DashboardData (JSON) ──┘
    │
    ├── 리스크 점수 카드 (손실 프레이밍)
    ├── 오늘의 액션 카드 (CTA 버튼)
    ├── 지원사업 미리보기 (마감 D-day)
    ├── 유동인구 트렌드
    └── 쿠폰 성과 요약
```

### 3.3 지원사업 매칭 (RAG)

```
[사용자] ──GET /subsidies/matches──→ [Backend]
                                        │
                                1. 쿼리 생성: "{구} {동} {업종} 소상공인 지원금"
                                2. OpenAI Embedding (1536 dim)
                                3. ChromaDB cosine similarity 검색
                                4. 중복 제거 + relevance > 0.3 필터
                                5. 마감일 기준 정렬
                                6. k-anonymity 사회적 증거 부착
                                7. 손실 프레이밍 메시지 생성
                                        │
                                        ▼
[Frontend] ◀── SubsidyMatchesResponse ──┘
    │
    ├── 손실 메시지 배너
    ├── 매칭 카드 (마감, 금액, 사회적 증거)
    └── [사업계획서 초안] 버튼
            │
            └── POST /subsidies/apply-draft ──→ GPT-4o
```

---

## 4. 외부 API 연동 맵

```
┌─────────────────────────────────────────────────────┐
│                   External APIs                      │
│                                                      │
│  [Kakao]                                             │
│  ├── OAuth: kauth.kakao.com/oauth/token             │
│  ├── UserInfo: kapi.kakao.com/v2/user/me            │
│  ├── Local: dapi.kakao.com/v2/local/search/keyword  │
│  └── Talk: kapi.kakao.com/v2/api/talk/memo/send     │
│                                                      │
│  [국세청]                                             │
│  └── 사업자 확인: api.odcloud.kr/api/nts-businessman │
│                                                      │
│  [서울시]                                             │
│  ├── 상권매출: data.seoul.go.kr/.../VwsmTrdarSelngQq │
│  ├── 생활인구: data.seoul.go.kr/.../SPOP_LOCAL_RESD  │
│  └── 문화행사: data.seoul.go.kr/.../culturalEventInfo│
│                                                      │
│  [OpenAI]                                            │
│  ├── GPT-4o: api.openai.com/v1/chat/completions     │
│  └── Embed: api.openai.com/v1/embeddings            │
│                                                      │
│  [Firebase]                                          │
│  └── FCM: fcm.googleapis.com/v1/messages:send       │
└─────────────────────────────────────────────────────┘

모든 외부 API 호출 규칙:
  1. @retry_async(max_retries=2, delay=1.0)
  2. timeout=10초
  3. 실패 시 None 반환 (서비스 중단 방지)
  4. TTL 캐시 적용 (서울시 API: 1시간, 인구: 30분)
```

---

## 5. 데이터베이스 ERD

```
┌──────────────┐     ┌──────────────────┐
│    users     │────<│  daily_actions   │
│──────────────│     │──────────────────│
│ id (UUID PK) │     │ id (UUID PK)     │
│ kakao_id     │     │ user_id (FK)     │
│ nickname     │     │ date             │
│ business_*   │     │ action_type      │
│ dong_name    │     │ title (손실프레임)│
│ gu_name      │     │ risk_score       │
│ lat, lng     │     │ cta_type/payload │
│ plan_tier    │     │ is_completed     │
│ onboarding_  │     │ UNIQUE(user,date)│
│ fcm_token    │     └──────────────────┘
│ kakao_tokens │
└──────┬───────┘     ┌──────────────────┐
       │────────────<│ coupon_templates │
       │             │──────────────────│
       │             │ id (UUID PK)     │
       │             │ user_id (FK)     │
       │             │ title            │
       │             │ discount_type    │
       │             │ qr_data/image    │
       │             │ scan_count       │
       │             └──────────────────┘
       │
       │────────────<┌──────────────────┐
                     │ notification_log │
                     │──────────────────│
                     │ id (UUID PK)     │
                     │ user_id (FK)     │
                     │ channel          │
                     │ message_type     │
                     │ status           │
                     └──────────────────┘

┌──────────────────┐
│    subsidies     │  (독립 테이블)
│──────────────────│
│ id (UUID PK)     │
│ title            │
│ organization     │
│ deadline         │
│ max_amount       │
│ target_types[]   │  ← ARRAY(Text)
│ target_regions[] │  ← ARRAY(Text)
│ embedding_id     │  → ChromaDB 연결
│ is_active        │
└──────────────────┘
```

---

## 6. 프론트엔드 페이지 맵

```
/                          → 랜딩 (ValueCards + 카카오 로그인)
  ├── /auth/kakao/callback → OAuth 콜백 처리
  ├── /onboarding          → 3단계 온보딩
  ├── /dashboard           → 메인 대시보드 (손실 프레이밍)
  │     ├── STTButton      → 음성 질의 (floating)
  │     └── NavBar         → 하단 네비게이션
  ├── /subsidies           → 지원사업 매칭 + 사업계획서 모달
  ├── /coupons             → QR 쿠폰 관리 + 생성 모달
  └── /offline.html        → PWA 오프라인 폴백
```

### 인증 흐름
```
페이지 로드 → useAuth.checkAuth()
  ├── 토큰 있음 → GET /auth/me → 성공 → 인증 상태
  ├── 토큰 있음 → GET /auth/me → 401 → 토큰 삭제 → 랜딩으로
  └── 토큰 없음 → 비인증 상태 → 랜딩으로
```

---

## 7. 변경 영향도 매트릭스

> **이 표를 보고 "내가 X를 수정하면 Y도 확인해야 한다"를 판단합니다.**

| 변경 대상 | 영향받는 파일 | 필수 검증 |
|-----------|-------------|-----------|
| `models/*.py` | schemas, routers, services, alembic | 마이그레이션 생성, 빌드 확인 |
| `schemas/*.py` | routers, frontend types | TypeScript 인터페이스 동기화 |
| `services/*.py` | routers, tasks | import 확인, 유닛 테스트 |
| `routers/*.py` | frontend api.ts | 엔드포인트 URL 동기화 |
| `config.py` | 모든 서비스 | 환경변수 문서 업데이트 |
| `utils/auth.py` | 모든 인증 필요 라우터 | JWT 토큰 테스트 |
| `frontend/types/` | 모든 프론트 페이지 | 빌드 확인 |
| `frontend/lib/api.ts` | 모든 프론트 페이지 | 빌드 확인 |

---

> **마지막 업데이트**: 2026-04-06
