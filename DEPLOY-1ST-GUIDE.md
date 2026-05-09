# 1차 통과용 배포 가이드 (4시간)

목표: 심사위원이 직접 사이트 접속해 체험 가능 → "메인·세부화면 구동(20점) + UI/UX 완성도(20점)" 확보

준비물:
- GitHub 계정 + 프로젝트 push 완료
- 카카오 디벨로퍼스 계정 (이미 있음 — REST API 키 보유)
- 신용카드 (Railway 무료 크레딧 5달러로 충분, Vercel 무료)

---

## Step 1 — GitHub 푸시 (15분)

이미 git 리포지토리 있으면 스킵. 없으면:

```bash
cd /Users/ijunsu/Documents/Documents/capston/SSGI_AI_Coach
git status
# 만약 .env가 staged면 git rm --cached backend/.env 후 .gitignore 확인
git add -A
git commit -m "deploy: 1차 통과용 prod 준비"
git push origin main
```

**중요**: `backend/.env`, `firebase-sa.json` 같은 시크릿 파일 절대 push 금지. `.gitignore`에 이미 등록되어 있는지 확인.

```bash
grep -E "^\.env|firebase-sa" .gitignore
# 출력 있어야 정상
```

---

## Step 2 — Railway 백엔드 배포 (1시간 30분)

### 2.1 계정 + 프로젝트 생성 (10분)

1. https://railway.app 접속 → "Login with GitHub"
2. New Project → "Deploy from GitHub repo" → SSGI_AI_Coach 선택
3. **Root Directory** 설정: `backend` (중요 — 모노레포 구조)
4. 자동으로 `Dockerfile` 인식 → 빌드 시작 (실패해도 OK, 환경변수 먼저 설정)

### 2.2 PostgreSQL 추가 (10분)

1. 프로젝트 대시보드 → "+ New" → "Database" → "Add PostgreSQL"
2. 자동 생성된 `DATABASE_URL` 변수 → 백엔드 서비스에 자동 연결됨
3. **연결 방식 변경**: Railway 기본 URL은 `postgres://...`인데 우리 코드는 `postgresql+asyncpg://`가 필요함
   - 백엔드 서비스 → Variables → `DATABASE_URL` 수동 편집
   - 값을 `${{Postgres.DATABASE_URL}}` 대신 다음으로 교체:
   ```
   ${{Postgres.DATABASE_URL.replace('postgres://', 'postgresql+asyncpg://')}}
   ```
   - 또는 Postgres 변수에서 host/user/password 추출해 직접 작성:
   ```
   postgresql+asyncpg://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.PGHOST}}:${{Postgres.PGPORT}}/${{Postgres.PGDATABASE}}
   ```

### 2.3 환경변수 설정 (30분)

`backend/.env` 값을 Railway Variables에 복사. 백엔드 서비스 → Variables 탭:

| 변수 | 값 | 출처 |
|---|---|---|
| `APP_ENV` | `production` | 신규 |
| `APP_HOST` | `0.0.0.0` | .env |
| `APP_PORT` | `${{PORT}}` | Railway 자동 변수 |
| `SECRET_KEY` | (32바이트 랜덤) | `openssl rand -hex 32` 실행 |
| `CORS_ORIGINS` | `https://[vercel-url].vercel.app` | Step 3 후 갱신 |
| `KAKAO_REST_API_KEY` | (현재 .env 값) | .env |
| `KAKAO_CLIENT_SECRET` | (현재 .env 값) | .env |
| `KAKAO_REDIRECT_URI` | `https://[vercel-url].vercel.app/auth/kakao/callback` | Step 3 후 갱신 |
| `NTS_API_KEY` | (현재 .env 값) | .env |
| `SEOUL_API_KEY` | (현재 .env 값) | .env |
| `OPENAI_API_KEY` | (현재 .env 값) | .env |
| `OPENAI_MODEL` | `gpt-4o` | .env |
| `OPENAI_MAX_TOKENS` | `1024` | .env |
| `OPENAI_TEMPERATURE` | `0.7` | .env |
| `CHROMA_PERSIST_DIR` | `/app/chroma_data` | Dockerfile WORKDIR 기준 |
| `CHROMA_COLLECTION_NAME` | `subsidies` | .env |
| `LOG_LEVEL` | `INFO` | prod로 변경 |
| `DAILY_ACTION_CRON` | `0 7 * * *` | .env |
| `SEOUL_SYNC_CRON` | `0 3 * * 1` | .env |
| `SUBSIDY_INDEX_CRON` | `0 4 * * 1` | .env |

**FIREBASE_SERVICE_ACCOUNT_JSON**은 일단 비워둠 — 데모 환경엔 FCM 비활성. ADR-004 v2에서 "FCM 우선" 재정의했지만 1차는 OAuth + 화면 시연 위주이므로 알림 없이도 OK.

### 2.4 배포 + 마이그레이션 (20분)

1. Variables 저장 → 자동 재빌드 시작
2. 빌드 로그에서 `INFO: Application startup complete` 확인
3. **마이그레이션 실행**: Railway → 백엔드 서비스 → "Settings" → "Custom Start Command" 임시 변경:
   ```
   alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
   - 한 번 재배포 → 마이그레이션 7건 적용 확인
   - 이후 다시 원래 startCommand로 복귀: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **시드 보조금 인덱싱**: Railway CLI 또는 Run a Command 기능으로:
   ```
   python -m scripts.seed_subsidies
   ```
   - 보조금 22건 PG 삽입 + ChromaDB 인덱싱
5. Railway 도메인 활성화: Settings → "Generate Domain" → `[project]-production.up.railway.app` 형태 URL 발급

### 2.5 헬스체크 (5분)

```bash
curl -m 10 -o /dev/null -w "code=%{http_code}\n" https://[your-railway-url]/docs
# code=200 OK
curl https://[your-railway-url]/health
# {"status":"ok"} 같은 응답
```

---

## Step 3 — Vercel 프론트 배포 (45분)

### 3.1 계정 + 프로젝트 (10분)

1. https://vercel.com 접속 → "Login with GitHub"
2. "Add New" → "Project" → SSGI_AI_Coach 선택
3. **Root Directory** 설정: `frontend` (중요)
4. Framework: `Next.js` 자동 인식
5. Build Command: 기본값 `npm run build`
6. Install Command: `npm install`

### 3.2 환경변수 (15분)

Settings → Environment Variables. **Production**에 다음 추가:

| 변수 | 값 |
|---|---|
| `NEXT_PUBLIC_API_URL` | `https://[railway-backend-url]` (Step 2.4의 URL) |
| `NEXT_PUBLIC_KAKAO_REST_API_KEY` | (Kakao REST API 키 — JS Key 아님 주의) |
| `NEXT_PUBLIC_KAKAO_REDIRECT_URI` | `https://[your-vercel-url].vercel.app/auth/kakao/callback` |

**Vercel URL 미리 정해두기**: 프로젝트명 = subdomain. 예: `ssgi-ai-coach.vercel.app`. 처음 배포 시 Vercel이 자동으로 URL 발급하므로 한 번 배포 후 위 환경변수 갱신 필요.

### 3.3 배포 + 갱신 (20분)

1. "Deploy" 버튼
2. 첫 빌드 완료 → Vercel 도메인 발급 (`https://ssgi-ai-coach.vercel.app`)
3. **Step 2.3 환경변수 갱신**: Railway 백엔드의 `CORS_ORIGINS`, `KAKAO_REDIRECT_URI`에 위 Vercel URL 반영
4. **Step 3.2 환경변수 갱신**: Vercel의 `NEXT_PUBLIC_KAKAO_REDIRECT_URI`도 동일 URL
5. Railway + Vercel 둘 다 재배포

---

## Step 4 — 카카오 OAuth Redirect URI (15분)

1. https://developers.kakao.com 로그인
2. 내 애플리케이션 → SSGI 앱 선택
3. 카카오 로그인 → Redirect URI → "Add"
   - 기존: `http://localhost:3000/auth/kakao/callback` (개발용 유지)
   - 추가: `https://[your-vercel-url].vercel.app/auth/kakao/callback`
4. 동의 항목 → 활성: 닉네임, 프로필 사진, 이메일

**카카오 비즈니스 등록 안 했으면 일부 scope 제한** — 데모 환경에선 닉네임만으로도 충분.

---

## Step 5 — 데모 계정 사전 가입 (15분)

심사위원이 접속하면 새로 가입할 필요 없도록 미리 시연용 계정 1개 가입.

1. 본인 카카오 계정으로 https://[vercel-url].vercel.app 접속
2. 카카오 로그인 → 콜백 → 온보딩 진입
3. **시연용 페르소나로 입력**:
   - 사업자번호: 본인 또는 가짜 10자리 (NTS API 검증 통과 필요 — 본인 사업자번호 추천)
   - 가게 검색: "마포구 카페 OOO" 등 (시드 매칭 풍부한 페르소나 P002)
   - 개점일: 1년 미만으로 설정 (C03 클러스터)
4. 대시보드 진입 → 매칭 보조금 ≥ 3건 노출 확인
5. 폐업 매트릭스 카드 점수 확인 (서울 한식·카페 데이터 정상 로드)

심사위원 안내문에 다음 명시:
> "시연: https://[vercel-url].vercel.app — 카카오 로그인으로 즉시 체험 가능. 대시보드 + 폐업 매트릭스 + 지원사업 매칭 + QR 쿠폰 기능 확인 권장."

---

## Step 6 — 제출 직전 마지막 점검 (15분)

### 기능 점검 체크리스트

- [ ] 랜딩 페이지 (`https://[url]/`) 정상 표시 — 카카오 노란 버튼
- [ ] OAuth state 파라미터 URL에 포함 (CSRF 방어 확인)
- [ ] 카카오 로그인 → 콜백 0.25-1초 내 완료
- [ ] 온보딩 stepper 1/3 → 2/3 → 3/3 표시
- [ ] 대시보드 카드 8개 모두 로드 (위험도, 폐업 매트릭스, 매칭 보조금, 유동인구, 문화행사, PDF 리포트, 쿠폰)
- [ ] 인사이트 3탭 (경쟁/마케팅/집중분석) 모두 작동
- [ ] /marketing 카드에 "AI 추정" amber 배너 표시
- [ ] 출처 라벨 "서울 VwsmTrdarSelngQq · 2024 4분기" 노출
- [ ] /subsidies 매칭 ≥ 3건
- [ ] /coupons QR 발행 + 스캔 작동
- [ ] PWA: 모바일 Safari로 접속 시 "홈 화면에 추가" 가능

### 성능 점검

- [ ] 첫 페이지 로드 ≤ 3초
- [ ] 대시보드 첫 진입 ≤ 5초
- [ ] /insights/competition 첫 진입 ≤ 30초 (캐시 워밍 완료 후 ≤ 1초)

### 보안 점검

- [ ] HTTPS 강제 (Vercel + Railway 둘 다 자동)
- [ ] `.env` git에 push 안 됨 확인 (`git log --all -- backend/.env` 0줄)
- [ ] CORS는 Vercel 도메인만 허용 (CORS_ORIGINS 와일드카드 X)
- [ ] /docs 비공개 검토 (Production에서 Swagger UI 노출 X — 필요하면 main.py에서 `docs_url=None` 설정)

---

## Step 7 — 제출서류 안내문 작성

상세기획서 PPT 표지에 다음 추가 (기존 표지 슬라이드 하단):

```
시연 URL: https://[vercel-url].vercel.app
시연 가이드:
1. 카카오로 15초 로그인
2. 사업자번호 + 마포 카페 검색 (테스트 시드 데이터 매칭 풍부)
3. 대시보드에서 폐업 매트릭스 + 매칭 지원금 확인
4. 인사이트 탭의 'AI 추정' 라벨 정직성 확인
```

또는 별도 README.txt 파일을 제출 폴더에 동봉.

---

## 트러블슈팅

### 백엔드 502 Bad Gateway
- Railway 빌드 로그 확인 → 의존성 설치 실패면 `requirements.txt` 점검
- DATABASE_URL 형식 `postgresql+asyncpg://...` 확인

### 카카오 로그인 KOE320 에러
- Redirect URI 일치 안 함 → 카카오 콘솔 + Vercel 환경변수 + Railway `KAKAO_REDIRECT_URI` 셋이 정확히 같은지 확인 (https/http, 마지막 슬래시 등)

### CORS 에러 (브라우저 콘솔)
- Railway `CORS_ORIGINS`에 Vercel URL 정확히 박혔는지 확인 (앞에 https://, 뒤에 슬래시 없음)

### ChromaDB 인덱싱 실패
- Railway는 매 배포마다 디스크 휘발 — `CHROMA_PERSIST_DIR` 가 휘발 디스크면 매번 재인덱싱 필요
- 해결: Railway Volume 추가 or `python -m scripts.seed_subsidies` 매 배포 후 자동 실행

### NTS 사업자번호 검증 실패
- Tax authority API rate limit / 일일 한도 초과 가능
- 본인 진짜 사업자번호 사용하거나 검증 우회 해킹 (코드 레벨)

---

## 시간 분배 (4시간 총합)

| 단계 | 시간 |
|---|---|
| Step 1 GitHub | 15분 |
| Step 2 Railway | 1시간 30분 |
| Step 3 Vercel | 45분 |
| Step 4 카카오 콘솔 | 15분 |
| Step 5 데모 가입 | 15분 |
| Step 6 점검 | 15분 |
| Step 7 안내문 | 15분 |
| 트러블슈팅 여유 | 30분 |
| **총합** | **4시간** |

---

## 1차 통과 확률 변화

| 시나리오 | 통과 확률 |
|---|---|
| 배포 안 함 (PPT만) | 20% 이하 |
| 배포 완료 + 데모 가입 | **60-70%** |
| 배포 + 시드 50건 실데이터 + PostHog | 75-80% |

**현 작업으로 60-70% 확보**가 목표. 나머지는 발표 단계에서 보강.
