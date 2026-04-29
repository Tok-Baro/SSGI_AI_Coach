# progress.md — 프로젝트 진행 상황

> **이 파일은 AI 에이전트가 매 작업 시작 시 읽고, 완료 시 업데이트하는 "현재 위치" 문서입니다.**

---

## 현재 상태: MVP 코드 완성 + Known Issues 해결 완료

**마지막 성공 커밋**: `8a5eb1c` (2026-04-06)
**마지막 성공 빌드**: Next.js 7페이지 빌드 OK, Backend import 전체 PASS

---

## 완료된 작업

### Phase 0: 프로젝트 기반 (2026-04-04)
- [x] FastAPI 프로젝트 구조 생성
- [x] Next.js 14 App Router 구조 생성
- [x] PostgreSQL docker-compose 설정
- [x] Pydantic Settings (config.py) — 26개 환경변수
- [x] Async SQLAlchemy engine + session factory
- [x] 5개 DB 모델 (User, DailyAction, Subsidy, CouponTemplate, NotificationLog)
- [x] 13개 Pydantic 스키마
- [x] JWT 인증 유틸리티 (create/decode/get_current_user)

### Phase 1: 인증 + 온보딩 (2026-04-04)
- [x] Kakao OAuth 콜백 → JWT 발급
- [x] 국세청 사업자번호 검증
- [x] 카카오 로컬 상호명 검색
- [x] 3단계 온보딩 플로우 (사업자번호 → 검색 → 확인)

### Phase 2: 핵심 기능 (2026-04-04)
- [x] RAG 파이프라인 (ChromaDB + OpenAI Embeddings)
- [x] 일일 액션 생성기 (GPT-4o + fallback)
- [x] 대시보드 API (손실 프레이밍 집계)
- [x] 지원사업 RAG 매칭 + 사업계획서 초안 (GPT-4o)
- [x] QR 쿠폰 생성/스캔

### Phase 3: 알림 + 음성 (2026-04-04)
- [x] 알림 서비스 (Kakao Talk > FCM > silent fail)
- [x] 3개 크론 작업 (daily_action 7AM, seoul_sync Mon 3AM, subsidy_index Mon 4AM)
- [x] 손실 프레이밍 메시지 템플릿 14개
- [x] k-anonymity 사회적 증거 서비스
- [x] STT 음성 질의 (Web Speech API → GPT-4o)

### Phase 4: 프론트엔드 (2026-04-04)
- [x] 7개 페이지 (랜딩, 카카오 콜백, 온보딩, 대시보드, 지원사업, 쿠폰, 오프라인)
- [x] PWA 설정 (manifest.json, service worker, offline fallback)
- [x] Zustand 인증 스토어
- [x] STTButton 컴포넌트

### Phase 5: 배포 준비 (2026-04-04)
- [x] Dockerfile + railway.toml
- [x] Alembic 설정 (async migration)
- [x] .gitignore (시크릿 파일 제외)

### Phase 6: 검증 + 버그픽스 (2026-04-04~06)
- [x] Backend 10/10 모듈 검증 PASS
- [x] Frontend Next.js 빌드 + TypeScript 타입체크 PASS
- [x] SQLAlchemy case() 구문 수정 (dashboard)
- [x] Suspense 경계 추가 (kakao callback)
- [x] 온보딩 체크 추가 (dashboard)
- [x] 쿠폰 스캔 flush 추가
- [x] 주소 파싱 정규식 강화

### Phase 7: Known Issues 전체 수정 (2026-04-06)
- [x] secret_key 프로덕션 강제화
- [x] CORS 메서드 제한 (GET, POST, OPTIONS)
- [x] Kakao 토큰 갱신 로직 (refresh_token)
- [x] 쿠폰 스캔 rate limiting (IP당 1분/5회)
- [x] RAG asyncio.Lock 동시접근 보호
- [x] Zustand persist 미들웨어
- [x] FCM 토큰 등록 연결 (온보딩 완료 시)
- [x] 하단 네비게이션 동적 active 상태
- [x] subsidies/coupons 에러 핸들링

### Phase 8: 문서화 (2026-04-06)
- [x] README.md
- [x] VERIFICATION_REPORT.md
- [x] IMPLEMENTATION_SPEC.md 최신화

### Phase 9: 하네스 엔지니어링 (2026-04-06)
- [x] CLAUDE.md (규칙 + 코딩 스타일)
- [x] progress.md (이 파일)
- [x] architecture.md (시스템 구조)

### Phase 10-A: 주간 마케팅 PDF 리포트 (2026-04-28)
> zubair-trabzada/ai-marketing-claude의 6-카테고리 가중 점수 + 3-tier 액션 패턴 이식
- [x] requirements.txt: reportlab>=4.2.0 추가
- [x] backend/app/services/report_generator.py 신규 (320줄)
  - 6 카테고리 가중치: 매출 트렌드(25%) + 보조금 활용(20%) + 유동인구 활용(20%) + 경쟁 포지셔닝(15%) + 액션 실행률(10%) + 위험도 추세(10%)
  - severity 4단계: Critical/High/Medium/Low (zubair 색상 팔레트)
  - 3-tier 액션 플랜: Quick Wins / Medium-Term / Strategic
  - 한글 폰트 자동 등록 (TTF 우선, HYSMyeongJo CID 폴백)
- [x] backend/app/routers/reports.py 신규 — GET /reports/weekly (PDF 스트리밍)
- [x] backend/app/main.py — reports 라우터 등록
- [x] frontend/src/lib/api.ts — downloadWeeklyReport() Blob 다운로드
- [x] frontend/src/app/dashboard/page.tsx — PDF 다운로드 카드 + 로딩/에러 상태
- [x] QA: PDF 정상 생성 (85KB 4-page, AppleGothic 임베드, 데이터 풀/0건 두 케이스 통과)
- [x] QA: Next.js 빌드 PASS (11페이지)

### Phase 10-B: 5-차원 마케팅 진단 (2026-04-28)
> coreyhaines31/marketingskills의 page-cro 7단계 → 소상공인 도메인 5-차원 압축 + zubair 5-병렬 패턴
- [x] backend/app/services/marketing_audit.py 신규 (300줄)
  - 5-차원: positioning · message_fit · timing · social_proof · friction
  - asyncio.gather 병렬 평가, 결정론적 점수 (GPT 0회)
  - 각 차원별 손실 프레이밍 headline + insight + 1-액션 + cta_type
  - severity 4단계 (critical/high/medium/low)
- [x] backend/app/routers/insights.py — `/insights/marketing-audit` 신규 (주간 캐시)
- [x] backend/app/services/action_generator.py — `audit_weakness` 옵셔널 파라미터로 GPT 프롬프트에 약점 차원 주입
- [x] frontend/src/lib/api.ts — `getMarketingAudit()` 메서드
- [x] frontend/src/app/insights/page.tsx — "진단" 탭 + DimensionCard 컴포넌트
- [x] QA: backend 평가 함수 end-to-end 테스트 (5-차원 점수 산출 정확)
- [x] QA: Next.js 빌드 PASS (insights 8.34→9.21KB)

### Phase 10-C: ICP Learner 매칭 자동 학습 (2026-04-28)
> ericosiu/ai-marketing-skills의 sales-pipeline/icp_learning_analyzer.py 패턴 → 보조금 도메인 적용
- [x] backend/app/models/subsidy_interaction.py 신규 (학습 신호 테이블)
  - signal_type: view(0.2) / click(1.0) / draft(3.0) / apply(5.0)
- [x] backend/alembic/versions/005_add_subsidy_interactions.py 마이그레이션
- [x] backend/app/services/icp_learner.py 신규 (200줄)
  - learn_user_profile(): 90일 윈도우, 30일 반감기 시간 가중치, 가중 중앙값/min/max
  - score_subsidy(): 0~1 boost (organization 0.4 + amount range 0.3 + keyword 0.3)
  - rerank_with_icp(): 기존 점수 + ICP boost - 마감 페널티
  - log_signal(): 신호 기록 헬퍼
- [x] backend/app/services/rag_service.py — `user_id` 옵셔널 파라미터 + 후보 풀 3배 확장 + ICP 재순위
- [x] backend/app/routers/subsidies.py
  - apply-draft 호출 시 'draft' 신호 자동 로깅
  - POST /subsidies/{id}/signal?signal_type=... 신규
  - GET /subsidies/icp-profile 신규 (학습된 프로필 조회)
- [x] dashboard/insights/reports/onboarding 라우터 — search_subsidies_filtered 호출에 user_id 전달
- [x] frontend/src/lib/api.ts — logSubsidySignal() + getIcpProfile() 메서드
- [x] frontend/src/app/dashboard/page.tsx — 보조금 카드 클릭 시 'click' 신호 자동 로깅
- [x] frontend/src/app/subsidies/page.tsx — 신청 페이지 링크 클릭 시 'apply' 신호 자동 로깅
- [x] QA: ICP 점수 산출 정확 (시간 감쇠/가중 중앙값/재순위 단위 테스트 통과)
- [x] QA: Next.js 빌드 PASS (dashboard 6.35KB)

---

## 다음 할 일 (Todo)

### 즉시 (API 키 확보 후)
- [ ] Kakao Developers 앱 등록 + REST API 키 발급
- [ ] 국세청 API 인증키 발급
- [ ] 서울시 열린데이터 API 키 발급
- [ ] OpenAI API 키 세팅
- [ ] `docker compose up` → `alembic upgrade head`
- [ ] `python -m scripts.seed_subsidies` (보조금 15건 + ChromaDB 인덱싱)
- [ ] 카카오 로그인 → 온보딩 → 대시보드 E2E 실연동 테스트

### 배포 단계
- [ ] Railway 프로젝트 생성 + PostgreSQL addon + 환경변수 설정
- [ ] Vercel 프로젝트 생성 + 환경변수 설정
- [ ] 프로덕션 CORS_ORIGINS + KAKAO_REDIRECT_URI 변경
- [ ] Lighthouse PWA 점수 > 90 확인
- [ ] SSL + 커스텀 도메인 (선택)

### 고도화 (대회 전)
- [ ] 실제 보조금 데이터 크롤링/수집 (50건+)
- [ ] 서울시 API 실데이터 검증 (상권분석, 생활인구, 문화행사)
- [ ] 사용자 테스트 (소상공인 3명+)
- [ ] Sentry 에러 모니터링 연동
- [ ] 성능 최적화 (API 응답시간 < 1초)

---

## 세이브 포인트 (Rollback 지점)

| 커밋 | 내용 | 안전도 |
|------|------|--------|
| `8a5eb1c` | Known Issues 전체 수정 + 시드데이터 | SAFE |
| `ac8ecd2` | 문서화 완료 (README, VERIFICATION) | SAFE |
| `79d075b` | Phase 5-6 완료 + 버그픽스 | SAFE |
| `516ac30` | MVP 전체 구현 (Phase 0-4) | SAFE |

> **롤백 방법**: `git reset --hard <커밋해시>` (위험!) 또는 `git revert <커밋해시>` (안전)

---

## 알려진 제한사항

1. Python 3.9 환경 (로컬) — 프로덕션은 3.11+ Docker 이미지 사용
2. 보조금 시드 데이터는 유사/가상 데이터 — 실데이터로 교체 필요
3. localStorage JWT — MVP에서는 수용, 프로덕션에서는 httpOnly 쿠키 전환 검토
4. 서울시 API 호출 제한 — 일일 1,000건, 캐싱으로 대응

> **마지막 업데이트**: 2026-04-06
