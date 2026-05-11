# SSGI 무료 배포 가이드

> Vercel + Render + Neon 3종 조합. 모두 무료 티어. **월 비용 $0**.
> 총 소요 시간 약 1시간.

---

## 아키텍처

```
사장님 브라우저 (mobile / desktop)
        │
        ▼ HTTPS
┌───────────────────────────────────────────┐
│  Vercel (Frontend, Next.js 14)            │
│  https://ssgi.vercel.app                  │
│  - 7 페이지 정적 빌드 + Edge SSR           │
│  - 100GB bandwidth 무료                   │
└───────────────────┬───────────────────────┘
                    │ fetch /api/*
                    │ HTTPS + CORS
                    ▼
┌───────────────────────────────────────────┐
│  Render Free (Backend, FastAPI)           │
│  https://ssgi-backend.onrender.com        │
│  - 512MB RAM / 750h 월 무료                │
│  - 15분 idle 후 sleep → cold start ~30초  │
│  - ChromaDB self-host (벡터 DB)           │
│  - APScheduler 3개 크론                    │
└───────────────────┬───────────────────────┘
                    │ asyncpg + sslmode=require
                    ▼
┌───────────────────────────────────────────┐
│  Neon (PostgreSQL 15 Serverless)          │
│  postgres://...neon.tech/ssgi             │
│  - 0.5GB 무료 (사용자 ~1만명 충분)         │
│  - 자동 sleep + warm up                    │
└───────────────────────────────────────────┘

[크론 회피] GitHub Actions 매 14분 → Render /health ping
```

| 서비스 | 무료 한도 | 결제 정보 필요? |
|---|---|---|
| **Vercel** Hobby | 100GB bandwidth / month | ❌ |
| **Render** Free | 750h compute / month | ❌ |
| **Neon** Free | 0.5GB storage / 100h compute | ❌ |
| **GitHub Actions** | 2,000분 / month (퍼블릭 무제한) | ❌ |

---

## Phase 1 — Database (Neon, 10분)

### 1.1 Neon 가입 + Project 생성
1. https://neon.tech 가입 (GitHub OAuth)
2. **New Project**
   - Name: `ssgi`
   - Region: `AWS ap-northeast-1 (Tokyo)` (한국 가장 가까움)
   - Postgres version: `15`
3. 연결 문자열 복사:
   ```
   postgresql://user:pass@ep-xxx-pooler.ap-northeast-1.aws.neon.tech/ssgi?sslmode=require
   ```

### 1.2 Alembic 마이그레이션 (로컬에서 1회)
```bash
cd backend
source .venv/bin/activate
export DATABASE_URL="postgresql+asyncpg://user:pass@ep-xxx.neon.tech/ssgi?sslmode=require"
alembic upgrade head
```

### 1.3 시드 데이터 (보조금 22건)
```bash
python -m scripts.seed_subsidies
```

→ Neon dashboard에서 `subsidy` 테이블에 22건 확인.

---

## Phase 2 — Backend (Render Free, 20분)

### 2.1 GitHub repo 준비
- 코드는 이미 `git@github.com:Tok-Baro/SSGI_AI_Coach.git`
- `backend/` 디렉터리 그대로 사용

### 2.2 Render 가입 + Web Service 생성
1. https://render.com 가입 (GitHub OAuth)
2. **New + → Web Service**
3. GitHub repo 연결: `SSGI_AI_Coach`
4. 설정:
   - **Name**: `ssgi-backend`
   - **Region**: Singapore (Tokyo 미지원)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && alembic upgrade head
     ```
   - **Start Command**:
     ```bash
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan**: **Free**

### 2.3 환경 변수 (Environment) 26건

| Key | Value | 설명 |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@ep-xxx.neon.tech/ssgi?sslmode=require` | Neon URL (asyncpg driver) |
| `SECRET_KEY` | `python -c "import secrets; print(secrets.token_urlsafe(32))"` | JWT 서명 키 |
| `JWT_ALGORITHM` | `HS256` | |
| `JWT_EXPIRATION_DAYS` | `30` | ADR 006 |
| `OPENAI_API_KEY` | `sk-...` | GPT-4o |
| `OPENAI_MODEL` | `gpt-4o` | |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | |
| `KAKAO_REST_API_KEY` | 카카오 디벨로퍼스 발급 | |
| `KAKAO_CLIENT_SECRET` | (선택) | |
| `KAKAO_REDIRECT_URI` | `https://ssgi.vercel.app/auth/kakao/callback` | **프론트 URL** |
| `BUSINESS_NUMBER_API_KEY` | 국세청 사업자 진위확인 키 | |
| `KAKAO_LOCAL_API_KEY` | 카카오 로컬 검색 (REST API와 같음) | |
| `SEOUL_OPENAPI_KEY` | 서울 열린데이터광장 키 | |
| `FCM_SERVICE_ACCOUNT_JSON` | Firebase 서비스 계정 (단일 라인 JSON) | |
| `CORS_ORIGINS` | `https://ssgi.vercel.app,https://*.vercel.app` | 프론트 도메인 |
| `CHROMA_PERSIST_DIR` | `/tmp/chroma` | Render ephemeral disk |
| `ENVIRONMENT` | `production` | secret_key 강제 검증 |
| `LOG_LEVEL` | `INFO` | |
| ... | (config.py 참조 26개 전체) | |

### 2.4 배포 + 검증
1. **Create Web Service** 클릭
2. 빌드 ~5분 (첫 배포는 의존성 설치 때문에 길게)
3. URL 확인: `https://ssgi-backend.onrender.com`
4. 검증:
   ```bash
   curl https://ssgi-backend.onrender.com/health
   # → {"status":"ok","version":"1.0.0"}
   ```
5. Swagger Docs: `https://ssgi-backend.onrender.com/docs`

### 2.5 ChromaDB 시드 (재배포마다 재생성)
Render Free는 disk가 ephemeral (재시작 시 초기화). 시드를 startup hook에:

`backend/app/main.py` startup 이벤트에 (이미 존재 시 skip):
```python
@app.on_event("startup")
async def seed_chroma_if_empty():
    from app.services.rag_service import rag_service
    if rag_service.collection.count() == 0:
        from scripts.seed_subsidies import index_to_chroma
        await index_to_chroma()  # 22건 자동 인덱싱
```

→ 매 cold start 시 자동 인덱싱 (~5초 추가).

---

## Phase 3 — Frontend (Vercel, 10분)

### 3.1 Vercel 가입 + Import
1. https://vercel.com 가입 (GitHub OAuth)
2. **Add New → Project**
3. GitHub repo `SSGI_AI_Coach` 선택
4. **Configure**:
   - **Framework Preset**: Next.js (자동 감지)
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (자동)
   - **Output Directory**: `.next` (자동)

### 3.2 환경 변수 (Vercel UI)

| Key | Value |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://ssgi-backend.onrender.com` |
| `NEXT_PUBLIC_KAKAO_REST_API_KEY` | 카카오 REST API 키 (프론트 노출 OK) |
| `NEXT_PUBLIC_KAKAO_REDIRECT_URI` | `https://ssgi.vercel.app/auth/kakao/callback` |
| `NEXT_PUBLIC_FIREBASE_API_KEY` | (FCM 사용 시) |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | (FCM 사용 시) |
| `NEXT_PUBLIC_FIREBASE_VAPID_KEY` | (FCM 사용 시) |

### 3.3 배포 + 검증
1. **Deploy** 클릭
2. 빌드 ~2분
3. URL: `https://ssgi-{random}.vercel.app` → 프로젝트 설정에서 `ssgi.vercel.app`로 변경
4. 검증: 브라우저에서 열고 카카오 로그인 버튼 클릭

---

## Phase 4 — CORS + Kakao 콜백 등록 (5분)

### 4.1 Kakao Developers Console
1. https://developers.kakao.com 로그인
2. 내 애플리케이션 → **카카오 로그인** → **Redirect URI**
3. 추가:
   - `https://ssgi.vercel.app/auth/kakao/callback` (프로덕션)
   - `http://localhost:3000/auth/kakao/callback` (개발)

### 4.2 Backend CORS 확인
`backend/app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
```

→ 환경변수 `CORS_ORIGINS=https://ssgi.vercel.app,https://*.vercel.app` 설정.

### 4.3 통신 테스트
1. 프론트 → http://localhost:3000 (또는 ssgi.vercel.app)
2. 카카오 로그인 → 콜백 → 대시보드
3. Network 탭에서 `OPTIONS preflight + POST /auth/kakao` 확인

---

## Phase 5 — 크론 회피 (Render Free Sleep) (15분)

### 5.1 문제
- Render Free는 15분 idle 후 sleep → cold start 30초
- APScheduler 크론 (7AM daily action 등)이 sleep 중이면 안 돌아감

### 5.2 해결: GitHub Actions Cron (가장 안정)

`.github/workflows/keep-alive.yml`:
```yaml
name: Keep Render Backend Awake

on:
  schedule:
    # 매 14분마다 (Render sleep 15분 직전)
    - cron: '*/14 * * * *'
  workflow_dispatch:

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping backend
        run: |
          curl -f https://ssgi-backend.onrender.com/health || exit 1
          echo "Pinged at $(date)"
```

→ GitHub Actions 무료 티어 (퍼블릭 repo 무제한, 프라이빗 2,000분/월).
→ 매 14분 ping = 월 약 4,300회 = ~30분 사용 (충분).

### 5.3 일일 7AM 액션 크론 (별도 워크플로우)

`.github/workflows/daily-action.yml`:
```yaml
name: Daily Action 7AM Trigger

on:
  schedule:
    - cron: '0 22 * * *'  # UTC 22:00 = KST 07:00
  workflow_dispatch:

jobs:
  trigger:
    runs-on: ubuntu-latest
    steps:
      - name: POST /admin/trigger/daily-action
        run: |
          curl -X POST https://ssgi-backend.onrender.com/admin/trigger/daily-action \
            -H "Authorization: Bearer ${{ secrets.ADMIN_TOKEN }}"
```

→ Backend에 `/admin/trigger/daily-action` 엔드포인트 추가 필요 (인증 필수):
```python
@app.post("/admin/trigger/daily-action")
async def trigger_daily_action(token: str = Header(alias="Authorization")):
    if token != f"Bearer {settings.admin_token}":
        raise HTTPException(401)
    await generate_daily_actions_for_all()
    return {"status": "triggered"}
```

→ APScheduler 그대로 둬도 OK이지만, GitHub Actions 트리거가 sleep 안전.

---

## 배포 후 점검 체크리스트

```
[ ] Neon DB — alembic upgrade head 성공
[ ] Neon DB — subsidy 테이블 22건 시드
[ ] Render — /health 200 OK
[ ] Render — /docs Swagger UI 접근
[ ] Render — ChromaDB 자동 시드 (startup 로그 확인)
[ ] Vercel — 7 페이지 빌드 성공
[ ] Vercel — / 랜딩 페이지 정상 노출
[ ] Kakao — Redirect URI 등록 (프로덕션 + 개발)
[ ] CORS — 프론트→백엔드 fetch 200 OK
[ ] 카카오 로그인 → 온보딩 → 대시보드 end-to-end
[ ] GitHub Actions — keep-alive ping 활성화
[ ] GitHub Actions — daily-action cron 활성화
```

---

## 비용 예측 (월간)

| 항목 | 무료 한도 | SSGI 예상 사용 | 결제 발생? |
|---|---|---|---|
| Vercel bandwidth | 100GB | ~5GB (사용자 1,000명 기준) | ❌ |
| Vercel build | 6,000분 | ~30분 | ❌ |
| Render compute | 750h | 730h (24/7 + sleep) | ❌ (한도 내) |
| Neon storage | 0.5GB | ~100MB (사용자 1,000명 + 액션 30,000건) | ❌ |
| Neon compute | 100h | ~50h | ❌ |
| GitHub Actions | 2,000분 | ~50분 (ping + cron) | ❌ |
| **합계** | — | — | **$0/월** |

→ 사용자 1,000명까지 무료 운영 가능. 5,000명+ 시 Neon Pro ($19) 필요.

---

## 위험 + 대응

| 위험 | 대응 |
|---|---|
| Render Free 15분 sleep | GitHub Actions 14분 ping (위 5.2) |
| Render Free cold start 30초 | 첫 사용자 대기 화면 (Loading...) — 카카오 콜백에 이미 있음 |
| Render Free 512MB RAM | ChromaDB 최소 모드 (22건 → 100MB), GPT-4o stream 응답 |
| Render disk ephemeral | ChromaDB 시드 매 cold start (~5초) |
| Neon 100h compute | autoscale-to-zero, 무료 plan 모니터링 |
| OpenAI 비용 | 별도 — 사용량 비례 (GPT-4o ~$50/1,000 사용자) |

---

## 도메인 (선택, 나중에)

기본:
- Frontend: `ssgi.vercel.app`
- Backend: `ssgi-backend.onrender.com`

커스텀 (예: `ssgi.kr`):
1. 도메인 구매 (가비아, 후이즈 — 약 1.5만원/년)
2. Vercel: Project → Settings → Domains → `ssgi.kr` 추가
3. DNS: 가비아 → CNAME `cname.vercel-dns.com`
4. SSL: Vercel 자동 발급 (Let's Encrypt)

---

## 단계 요약 (1시간 총 소요)

| Phase | 시간 | 작업 |
|---|---|---|
| 1. Neon DB | 10분 | 가입 + 마이그레이션 + 시드 |
| 2. Render Backend | 20분 | 가입 + Web Service + 환경변수 26개 |
| 3. Vercel Frontend | 10분 | Import + 환경변수 6개 |
| 4. CORS + Kakao | 5분 | Redirect URI 등록 + 통신 테스트 |
| 5. GitHub Actions | 15분 | keep-alive + daily cron |
| **합계** | **60분** | |

---

> **다음 단계**: 발표·심사 후 사용자 100명+ 가입 시 → Neon Pro ($19) 또는 Supabase Pro ($25)로 업그레이드. Render → Fly.io ($5 가벼운 VM)로 sleep 회피.
</content>
