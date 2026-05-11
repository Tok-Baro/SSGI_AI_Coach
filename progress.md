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

### Phase 12-E: 개점일 입력 + 영업기간 정확화 (2026-05-04)
> 생존 매트릭스/손실 카운터의 "영업기간"을 가입일 추정 → 실제 개점일 기반으로 정확화
- [x] backend/app/models/user.py — `business_start_date: Date` 필드 추가
- [x] backend/alembic/versions/006_add_business_start_date.py — 마이그레이션 신규 + 적용 완료
- [x] backend/app/schemas/onboarding.py — `business_start_date: Optional[date]` 추가
- [x] backend/app/routers/onboarding.py — 저장 로직 추가
- [x] backend/app/routers/insights.py (survival-score) — 영업기간 계산: business_start_date 우선, 없으면 created_at fallback
- [x] backend/app/routers/dashboard.py — 누적 손실 카운터에 동일 적용 (정확한 손실 누적)
- [x] frontend/src/app/onboarding/page.tsx — 확인 단계에 개점일 input(date) 추가, max=today
- [x] frontend/src/lib/api.ts — `completeOnboarding` 시그니처에 `business_start_date?: string` 추가
- [x] QA: alembic 006 적용 OK, backend import 31 routes, TS 0 에러

### Phase 12-D: 세금 캘린더 카드 (2026-05-04)
> 부가세/종소세/4대보험/원천세 D-Day + 예상 납부액 + 절세 알림. GPT 0회.
- [x] frontend/src/app/dashboard/page.tsx — `TaxCalendarCard` 신규:
  - 다음 신고 강조 카드 (D-7 이내 적색 / D-30 이내 황색)
  - 부가세 일반(분기 4회 25일) / 간이(연 1회 1/25) / 종소세(5/31) / 4대보험·원천세(매월 10일)
  - 예상 납부액: 일반 부가세=분기매출×5%, 간이=연매출×1.5%, 종소세=연매출×6% (추정)
  - 절세 팁: 매입계산서 보관 / 사업용 카드 / 노란우산공제
  - LocalStorage `ssgi_tax_config` (월매출 + 일반/간이 토글)

### Phase 12-C: 인건비 시뮬레이터 (Labor Cost) (2026-05-04)
> "시급 표면 vs 실제 사장님 부담" — 알바 1명 채용 결정 보조
- [x] frontend/src/app/dashboard/page.tsx — `LaborCostCard` 신규 (배달 P&L 다음):
  - calcLabor(): 기본임금 + 주휴수당(주15h+) + 4대보험(9.4%) + 퇴직금(1년+) 결정론적 계산
  - 시급 표면가 vs 실제 시간당 부담 비교 (+X% 추가)
  - 회수에 필요한 월 매출 = 인건비 / 영업이익률 → 매출의 30%↑ 적색, 20%↓ 녹색
  - 두루누리/청년채용/일자리안정자금 지원금 안내
  - 9개 설정값 (시급/주근무/고용기간/매출/이익률/주휴·4대보험·퇴직금 토글) — LocalStorage `ssgi_labor_config`

### Phase 12-B: 배달앱 진짜 손익 계산기 (Delivery P&L) (2026-05-04)
> 사장님 일상 페인 #1 = "배민에서 팔수록 진짜 남는지 모름" 해결
> 백엔드 변경 0, GPT 호출 0, LocalStorage만으로 일상 가치 제공
- [x] frontend/src/app/dashboard/page.tsx — `DeliveryPnLCard` 신규 (생존 매트릭스 다음 위치):
  - 9개 설정값 (객단가/원가율/포장비/배달팁/배민·요기요 수수료·광고/카드수수료) — 디폴트 값 즉시 결과
  - LocalStorage `ssgi_pnl_config`로 영구 저장 (백엔드 모델 변경 0)
  - calcPerOrder(): 1건당 매장/배민/요기요 진짜 순익 결정론적 계산
  - 시각화: 3-bar 비교 (음수면 적색) + 월 100건 카드 + 비용 분해 details
  - 핵심 인사이트 자동 생성:
    · 손해 시: "배민/요기요 주문은 팔수록 손해" (적색)
    · 흑자 시: "배민 100건 ≒ 매장 N건" 등가 환산
  - editMode 토글: 9개 input 으로 사장님 실제 수치 입력 → 즉시 갱신
- [x] QA: TS 0 에러, Next.js build PASS (dashboard 7.32→10.6KB)

### Phase 12-A: 생존 매트릭스 — "AI 코치만 알 수 있는 손실" 정체성 (2026-05-04)
> 사용자 피드백: "지금까지 만든 거 다 사장님도 아는 것" → 진짜 차별화 영역으로 전환
> 폐업 가게 패턴 vs 우리 가게 위험 신호 매칭. GPT 0회, 결정론적 계산.
- [x] backend/app/services/seoul_api_service.py — `get_commercial_change_index` 응답에 폐업 분석 컬럼 4종 추가:
  - `survival_avg_months` (생존업체 평균 영업개월), `closed_avg_months` (폐업업체 평균 영업개월)
  - `closing_area_count`, `growing_area_count` (상권변화지표 분포 집계)
- [x] backend/app/routers/insights.py — `/insights/survival-score` 엔드포인트 신규 (주간 캐시, GPT 0회):
  - 위험 신호 5종 결정론적 룰: 매출 감소 / 동네 폐업률 / 상권 정체·축소 / 유동인구 감소 / 폐업 평균 영업기간 근접
  - 종합 점수 = 100 - (high*20 + med*10 + low*5)
  - risk_level 4단계: safe(≥80) / watch(≥60) / warning(≥40) / critical
  - your_position: 영업개월 vs 폐업 평균의 percentile (70~130%면 위험 구간)
  - survival_action: high signal 첫 항목에 매핑된 룰 기반 (할루시 없음)
- [x] frontend/src/lib/api.ts — `getSurvivalScore()` 메서드 추가
- [x] frontend/src/app/dashboard/page.tsx — `SurvivalMatrixCard` (위험도 카드 다음 위치):
  - 헤더: 4-단계 그라데이션 (safe 녹/watch 청/warning 주/critical 적) + 점수 + 패턴 유사도
  - 영업기간 위치 비교 막대 (폐업 평균 70~130% = 빨간 구간)
  - 5-신호 체크리스트 (트리거 시 색상 점 + 현재 수치)
  - "지금 해야 할 단 1가지" 액션 카드
- [x] QA: backend route 등록 OK (5번째 insights), TS 0 에러

### Phase 11-D: 메뉴 전략 카드 — 갭 분석 + 시즌 캘린더 + 차별화 1픽 (2026-05-04)
> 단순 메뉴 추천(할루시네이션 위험)이 아니라 데이터 갭 + 시즌성 + 차별화 3축 묶음
- [x] backend/app/routers/insights.py — `/insights/menu-strategy` 엔드포인트 신규 (주간 캐시):
  - 데이터: sales_detail(고객층) + benchmark(객단가 갭) + kakao.search_local(주변 경쟁사) + cultural_events + weather
  - GPT 응답 스키마: summary / gap_analysis(missing_categories[3]) / seasonal_calendar(4주) / differentiation_pick
  - 각 missing_category에 competitor_coverage_pct + fit_score + expected_avg_ticket_change_pct + implementation_cost
  - max_tokens 1800
- [x] frontend/src/lib/api.ts — `getMenuStrategy(refresh)` 메서드 추가
- [x] frontend/src/app/insights/page.tsx — `MenuStrategyCard` 컴포넌트 (마케팅 탭 객단가 카드 아래)
  - 접힌 상태로 시작 → 클릭 시 lazy load (비용 절약)
  - 갭 분석: 카테고리별 보유율/적합도/객단가 변화/도입비용 칩
  - 시즌 캘린더: 4주 border-left 카드 (테마 + 메뉴 아이디어 + 채널 액션)
  - 차별화 한 수: 그라데이션 강조 카드 (우리 적합 이유 / 경쟁사 못하는 이유 / 오늘 시작)
- [x] QA: backend route 등록 OK (/menu-strategy), Next.js build PASS (insights 12.8→13.9KB)

### Phase 11-C: 집중분석(deep) 탭 전문가 보강 — 시각화 + 시계열 (2026-05-04)
> "전부 줄글" 한계 해소 — 시각화 + Quadrant 매트릭스 + 시계열 diff + 정량 KPI
- [x] backend/app/routers/insights.py — `/deep-report` 응답 5종 신규 + max_tokens 2048→3500:
  - `executive_summary`: string → `{current, risk, recommendation}` 3-section 객체 (전문가 어조)
  - `tows_matrix`: SO/ST/WO/WT 4분면 전략 (SWOT 결합)
  - `positioning_map`: 가격×품질 2D 좌표 (us + competitors[] + interpretation)
  - `action_items[].impact_score / effort_score / category`: Impact-Effort 2×2 분석용
  - `monthly_goal`: string → `{summary, kpis: [{name, target, current, unit, rationale}]}` 정량 KPI
  - 신규 `_get_previous_cached()` 헬퍼 — 이전 주차 캐시 조회 (시계열 diff)
  - 응답에 `previous: {summary, risk_alert, generated_at}` 추가
- [x] frontend/src/app/insights/page.tsx — 신규 컴포넌트 6종 + 기존 텍스트 카드 6→5 압축:
  - `ExecutiveSummaryCard`: 다크 헤더 + 3 border-left section (현황/위험/권고)
  - `PreviousDiffCard`: 지난 진단 대비 변화 (위험 변동 알림)
  - `TowsMatrixCard`: 4-색 quadrant grid (SO 녹/ST 청/WO 황/WT 적)
  - `PositioningMapCard`: 240×240 SVG 2D 산점도 + 우리 가게 강조
  - `ActionImpactMatrix`: 2×2 Quadrant SVG (즉시실행/대형/자투리/제외) + 번호 매긴 리스트
  - `MonthlyGoalCard`: 그라데이션 헤더 + KPI별 진척도 게이지 (≥80% 녹색, ≥50% 황색, 미만 적색)
- [x] QA: backend insights.py import OK, Next.js build PASS (insights 10.8→12.8KB)

### Phase 11-B: 마케팅 탭 전문가 보강 — 근거·예산·채널·톤 (2026-05-04)
> "AI가 그냥 만들어낸 거 아냐?" 신뢰 격차 해소 + 예산 의사결정 보조 + 톤 다양화
- [x] backend/app/routers/insights.py — `/marketing` GPT 프롬프트 확장 (max_tokens 2400→4000):
  - `strategies[].evidence`: 데이터 근거 1줄 (description과 분리)
  - `budget_scenarios`: 0원/5만원/30만원 3-tier (headline + actions[] + expected_uplift_won)
  - `channel_priority`: 인스타/배민/SMS/전단 등 5개, fit_score + ROI + first_step (배달 비중 낮은 업종 가드 포함)
  - `copy_variants`: trust/friendly/urgent 3톤 × 4종 카피 (각 톤의 호소 전략 자체를 다르게)
- [x] frontend/src/app/insights/page.tsx
  - MarketingData 인터페이스 4종 신규 (BudgetScenario / ChannelScore / CopyVariant / CopyVariants)
  - 전략 카드: evidence 청록색 칩 (description 아래)
  - BudgetScenariosCard 신규: 3-tier gradient 카드 + 월 예상 uplift
  - ChannelPriorityCard 신규: fit_score 막대 정렬, ROI 색상 (≥100 녹색), first_step 후속 액션
  - CopyVariantsCard 신규: 신뢰/친근/긴급 3-탭 (기존 CopiesCard 대체, fallback 유지)
  - UpliftCard: 옵션 클릭 가능 → 30일 누적 매출 증분 SVG 라인+area 차트 (frontend 계산식)
- [x] QA: backend insights.py import OK, Next.js build PASS (insights 9.45→10.8KB)

### Phase 11-A: 메인 대시보드 전문가 보강 — 손실 카운터 + delta + peer percentile (2026-05-04)
> 사장님 페르소나 "그래서 뭐?" 해소 1차 — 정적 카드 → 시간 축 + 비교 축 추가
- [x] backend/app/routers/dashboard.py — 응답 필드 5종 추가:
  - `loss_counter`: unclaimed_amount_won / daily_loss_won / accumulated_loss_won / days_since_signup
  - `deltas`: risk_score_delta (어제-그제) / coupon_scan_delta_pct (7d vs 7d)
  - `peer_percentile` + `peer_sample`: 같은 업종 14일 risk_score 평균 비교 (k≥10 ADR-002)
  - `next_action_preview`: 매칭 보조금 2순위 → 오늘의 액션 완료 후 노출
  - `subsidy_matches[].match_reasons`: 업종/지역/마감/고액 칩 (매칭 근거 추적성)
- [x] frontend/src/types/index.ts — DashboardData 인터페이스 동기화 (Subsidy.match_reasons 포함)
- [x] frontend/src/app/dashboard/page.tsx
  - LossCounter 신규 컴포넌트: 그라데이션 카드 + setInterval 1초 카운터 + tabular-nums
  - DeltaBadge 신규 컴포넌트: ▲▼ + green/red, inversed 옵션 (위험도 감소가 좋음)
  - 위험도 카드: delta 배지 + "동종업계 상위 X%" 라인
  - 오늘의 액션 카드: 완료 시 "다음 후보" 미니 카드
  - 지원사업 매칭 카드: ✓ 매칭 사유 칩 (업종/지역/임박/고액)
  - 쿠폰 성과 카드: scan delta 배지 + 라벨 "스캔(7일)"
- [x] QA: backend dashboard.py import OK, Next.js build PASS (dashboard 6.35→7.3KB)

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

## 2026-05-09 — 프론트엔드 토스풍 UIUX 전체 리스킨

**범위**: 7개 페이지 + 컴포넌트 (3470줄)
**기조**: 행동·로직 100% 보존, 디자인 시스템만 교체

**기반 토큰 (tailwind.config.ts + globals.css)**
- 폰트: Inter → Pretendard Variable (CDN)
- 컬러: gray 팔레트 토스 톤(#F9FAFB ~ #191F28)으로 재정의
- 의미색 3종 신설: `loss-*`(#F04452), `warn-*`(#FEE500 카카오 유지), `success-*`(#00C896)
- 타이포: `display-sm/display/display-lg` 추가 (큰 숫자 hero용)
- 그림자: `shadow-card`, `shadow-card-hover`, `shadow-btn` (테두리 → 그림자 전환)
- 유틸: `press-effect` (모바일 탭 스케일), `tabular-nums`

**리스킨 페이지**
1. `page.tsx` — 가치제안 카드 + 카카오 CTA (이모지 아이콘)
2. `onboarding/page.tsx` — 3단계 stepper, bg-gray-50 입력 필드 토스 스타일
3. `dashboard/page.tsx` — 잠재 지원금 hero 그라디언트 카드(노랑), 카드 그림자 통일, 하단 네비 이모지
4. `insights/page.tsx` — 헤더 sticky, 탭 인디케이터 검정 line, NavItem 아이콘
5. `coupons/page.tsx` — 쿠폰 카드 큰 할인율 표시, 모달 drawer 핸들 추가
6. `subsidies/page.tsx` — 카드별 큰 금액 텍스트, 사업계획서 모달 토스풍
7. `auth/kakao/callback/page.tsx` + `error.tsx` + `STTButton.tsx` — 스피너·에러·플로팅 버튼 통일

**일괄 치환 (sed, BSD)**
- yellow-* → warn-*, red-* → loss-*, green-* → success-*
- 5개 파일 중 1809줄 insights 포함 약 270개 클래스 치환

**검증**
- `npx next build` ✓ (11/11 정적 페이지, 새 에러 0)
- `grep '[一-鿿]' src/` → 0건 (한자 메모리 룰 준수)

---

## 2026-05-11 — 상세기획서 덱: 음성·PDF·사업계획서·결제 화면 반영 (19→20장)

**파일**: `scripts/build_planning_doc.py` → `SSGI_상세기획서_심사위원용.pptx`

**추가 캡처 6종** (repo 루트 `KakaoTalk_Photo_2026-05-11-19-43-*.png`) → `SHOTS` 딕셔너리 키 신설
- `voice` 홈 AI 음성 질문("마케팅") 처리 중 / `pdf` PREMIUM PDF 진단서(67점·등급 C) / `bizplan` AI 사업계획서 초안(빈칸 자동 채움)
- `paywall` 인사이트>메뉴 Pro 전용 / `pay_up` SSGI Pro 업그레이드(혜택 5종·9,900원) / `pay_done` 결제 완료(테스트·만료일)

**슬라이드 매핑**
- 기능 ③(지원금 매칭) 2폰 → 3폰: `02·04·bizplan`, 제목 "사업계획서 초안까지"로 교체
- 기능 ⑤(AI 종합진단) 2폰 → 3폰: `08·03·pdf`
- 기능 ⑧(음성 질문) `03` → `voice·03` (실제 음성 창)
- **신규 기능 ⑨ — 카카오페이 결제 + Pro 업그레이드** (3폰 `paywall·pay_up·pay_done`, deck 16쪽). "결제 모듈 연동 완료·테스트 환경, 정식 결제 사업자 가맹 후 2026 Q3" 정직 표기 유지
- 갤러리 8폰 중 일부 교체(bizplan/voice/pdf/pay_done 노출), 표지 LIVE FEATURES 9→10, 개요 4번째 그룹 "접근·증빙·결제"

**리넘버**: 흐름도 16→17 / 갤러리 17→18 / UI·UX 18→19 / 백업 19→20, 푸터 "/19"→"/20", 목차 2열×10행 재배치(+⑨ 항목)

**검증**: `python3 scripts/build_planning_doc.py` ✓ 20장 / `bash scripts/render_pptx.sh` → s01~s20.png 전수 시각 확인 ✓ (겹침·넘침 0)
> ⚠️ `pdf` 캡처에 기존 데이터 글리치("237,517% 증가") 텍스트 포함 — 슬라이드 썸네일 크기에선 판독 불가하나 추후 백엔드 수정 시 재캡처 권장

**폰트 스케일 업 (ir-deck-visual 타이포 위계 적용)**: 전 슬라이드 글자 크기 비례 확대
- 헬퍼 기본값: eyebrow 9.5→11 / subtitle 11.5→13 / footer 8→9.5 / card body 10→12.5·title 13→15·num 26→32 / bignum number 38→46·label 9→11·caption 9.5→11.5 / rubric_badge 8.5→10
- feature_slide: section_title 23→26 / sub 10.5→12.5 / card body 9.5→12·title 12.5→14.5 / caption 9→11 (1폰 h 716→700, 카드 그리드 y0=358 footer 라인과 정확히 맞물림 — 변경 금지)
- 표지 SSGI 64→72·슬로건 32→35 / 목차 번호 12.5→14.5·항목 10.5→11.5(badge 영역과 겹치지 않게 title_w 동적 430/720) / 본문 슬라이드 03~07·17·19·20 카드·표·블록 일괄 +2~3pt
- 긴 본문 1건만 트림(기능 ⑨ "무엇을" ~130→~95자) — 박스 오버플로 방지

---

## 2026-05-11 — 업종 지식팩 아키텍처 P0 (industry.py → 데이터 외부화, 무중단 리팩터)

배경: 업종별 도메인 지식(KPI·채널·카피·가중치)을 "스킬처럼" 데이터 파일로 쌓아 웹에서 쓰는 아키텍처. 설계는 4단계(P0 무중단 리팩터 / P1 16업종군+학원 독립+온보딩 피커 / P2 risk_engine 업종화·insights 중복표 제거·subsidy 태그 / P3 출처칩·상권유형 override). 도메인 리서치 6건(업종분류체계 KSIC/서울상권 100업종 · 손익·KPI 벤치마크 · 마케팅채널 ROI · 폐업·행동경제학 논문 · 서울 공공데이터 · 지원사업 landscape) 수행 → P1~P2 콘텐츠 시드로 사용.

**P0 구현 (이번 단계 — 동작 변화 0):**
- `backend/app/knowledge/` 신설 — `schema.py`(Pydantic v2 `IndustryPack`: id/name/group/status/version/reviewed_date/sources/match{priority,keywords,...}/prompt_block/audit_weights/report_weights/kpi_thresholds, report_weights 합=1.0 검증), `registry.py`(packs/*.yaml 부팅 1회 로드 → `_base`→group→leaf deep-merge → `lru_cache`, `resolve()/classify()/get()/all_packs()`. classify 는 match.priority 오름차순 검사 = 기존 `_KEYWORDS` 순서 재현).
- `backend/app/knowledge/packs/` — `_base.yaml`(공통 디폴트: audit 전부 1.0, report 표준분포, kpi {} ) + `unknown.yaml` + 6개 군 YAML(`delivery_food`/`cafe`/`restaurant`/`fashion`/`service`/`retail` — 기존 `industry.py` 의 `_PROMPT_BLOCKS`·`_AUDIT_WEIGHTS`·`_REPORT_WEIGHTS`·`_KPI_THRESHOLDS`·키워드 **그대로 이관**, priority 10/20/30/40/50/60 = 옛 리스트 순서).
- `backend/app/utils/industry.py` → **얇은 shim**(레지스트리 호출). 기존 export 전부 유지: `SLUG_*` 7개 + `classify_industry`/`industry_prompt_block`/`industry_audit_weights`/`industry_report_weights`/`industry_kpi_thresholds`. 호출부(insights.py·action_generator.py·marketing_audit.py·report_generator.py) 무수정.
- `backend/scripts/validate_packs.py` — `python -m scripts.validate_packs` (group 존재·순환·스키마·report 합·sources 경고).
- `backend/requirements.txt` — `PyYAML>=6.0` 추가 (지식팩 로드용; .venv 엔 이미 설치돼 있었음).

**검증**: `python -m scripts.validate_packs` ✓ 7팩 통과 / `from app.main import app` ✓ / 구 하드코딩 기대값 대조 테스트(분류 14케이스 + prompt_block 내용 + audit/report/kpi 값 + 순서규칙 "치킨카페"→delivery_food) ✓ — **동작 동일 확인**.

### P1 — 세부 업종 분기 시작 + DB 컬럼 (이번 단계, 백엔드)

- **새 팩 2개**
  - `academy.yaml` (top-level) — 학원/교습소를 `service` 에서 독립. 자체 prompt_block·KPI 임계값(재등록률<60%·정원충족률<50%·강사료비율>55%·영업이익률<6%, BC카드 학원매출 2023 출처)·audit/report 가중치. 키워드 [학원/교습소/보습/입시/어학원/공부방/과외/…/태권도장/발레학원/코딩학원] priority 45 (service 50 보다 먼저). ksic ["85"]. (이전엔 "○○학원"→unknown 이었음 → 개선)
  - `restaurant.korean_meat.yaml` (leaf, `group: restaurant`) — 삼겹살/갈비/곱창/숯불구이/무한리필. group 상속 + prompt_block·테이블단가/회전율/단체예약 임계값·timing 1.2·social_proof 1.1 만 override (report_weights 는 합 1.0 제약상 부분 override 금지 → 상속). 키워드 priority 25. ksic ["56113"]. → leaf/group 상속 + leaf-priority 패턴 검증 완료.
  - `retail.yaml` 키워드 `소매업`/`소매` 추가 (백필 시 canonical "소매업" → retail 매칭).
  - ※ 나머지 ~10개 업종군(food.korean_general/chinese/japanese/…/beauty 등)은 "조언이 실제 갈리는 곳만" 원칙 — 의도적으로 미생성, 필요 시 점진 추가 (데이터 파일이라 코드 수정 없음).
- **API**: `GET /knowledge/industries` (`app/routers/knowledge.py`, main 에 등록) — 팩 목록(id/name/group/keywords/status/reviewed_date) → 온보딩 업종 피커·출처칩용.
- **DB**: `User.industry_slug` (String(64), nullable, index) 컬럼 + 마이그레이션 `008_add_industry_slug.py` (down=7314edff5bc1) + 백필 스크립트 `scripts/backfill_industry.py` (`classify_industry(business_type)` 로 기존 행 채움). `onboarding.complete_onboarding` 에서 **raw** 입력값(`req.business_type`, 정규화 전 — "편의점"→retail 더 정확)으로 `industry_slug` 저장.
- **검증**: `python -m scripts.validate_packs` ✓ 9팩 / `from app.main import app` ✓ (`/knowledge/industries` 등록) / 마이그레이션 008 import ✓ / classify 15케이스 ✓ (학원→academy, 삼겹살집/고깃집→restaurant.korean_meat, 한식당→restaurant 불변, 치킨/편의점/미용실/의류 불변, 소매업→retail 신규) / leaf 상속·partial override 머지 ✓ / `/knowledge/industries` 8팩 ✓.
- **⚠️ 실행 필요(DB 있는 환경에서)**: `alembic upgrade head` → `python -m scripts.backfill_industry`.

### P1c — `industry_slug` 소비 wiring + 온보딩 업종 피커 (이번 단계)

- **레지스트리**: `registry.resolve_for(slug, business_type)` — slug 우선, 비었거나 무효(없는 pack)면 business_type 분류로 폴백.
- **shim 오버로드** (`app/utils/industry.py`): `classify_industry`/`industry_prompt_block`/`industry_audit_weights`/`industry_report_weights`/`industry_kpi_thresholds` 모두 선택 2번째 인자 `industry_slug=None` 추가 (없으면 기존 동작 그대로 — 하위호환).
- **다운스트림 wiring** (모두 `user.industry_slug` 전달):
  - `insights.py` menu-strategy: `industry_prompt_block(current_user.business_type, current_user.industry_slug)`
  - `action_generator.py` ×3 (daily / BP / voice): `industry_prompt_block(user.business_type, user.industry_slug)`
  - `marketing_audit.evaluate(...)`: `industry_slug` 키워드 파라미터 추가 → `industry_audit_weights`·`_industry_channel_hint`·반환 `industry_slug` 에 전달. 호출부 `insights.py` 마케팅 엔드포인트가 `industry_slug=user.industry_slug` 전달.
  - `report_generator.assemble_report_data(...)`: `industry_slug` 파라미터 추가 → `industry_report_weights` 에 전달. 호출부 `reports.py` 가 `current_user.industry_slug` 전달.
- **온보딩**: `CompleteOnboardingRequest.industry_slug` (Optional, ≤64자) 추가. `complete_onboarding` 이 `classify_industry(req.business_type, req.industry_slug)` 로 저장 (피커 선택 우선).
- **`/knowledge/industries`** 응답에 `priority` 필드 추가 (프론트가 백엔드 분류 순서 미러용).
- **프론트** (`onboarding/page.tsx`): 마운트 시 `api.getIndustries()` → 가게 선택 시 카테고리/업종명을 keywords 와 priority 순으로 매칭해 기본 업종 추정(`guessIndustrySlug`) → "이 가게가 맞나요?" 화면에 `<select>`("자동 감지" + 업종군·세부 들여쓰기 목록)로 노출/수정 가능 → 완료 시 `industry_slug` 전송. `api.ts` `getIndustries()` + `completeOnboarding` 타입에 `industry_slug?`, `types/index.ts` `IndustryPackInfo` 추가.
- **검증**: `validate_packs` ✓ 9팩 / `from app.main import app` ✓ / wiring sanity(resolve_for slug우선/폴백, shim 오버로드, evaluate·assemble_report_data 시그니처에 industry_slug, 스키마 필드) ✓ / `/knowledge/industries` priority 포함 8팩 ✓ / `npx next build` ✓ 15/15 페이지(에러 0).

→ **P1 (P1a+b+c) 완료.**

### P2a — risk_score_engine 업종화 + 팩 콘텐츠 확장 + deep-report 업종표 외부화 (이번 단계)

- **스키마 확장** (`schema.py`): `IndustryPack` 에 `risk_signal_weights`(dict, 7시그널 배율 — `RISK_KEYS` 검증) + `subsidy_tags`(list[str]) 추가. `_base.yaml` 에 `risk_signal_weights` 7키 전부 1.0 + `subsidy_tags: []`.
- **팩 콘텐츠** — `risk_signal_weights` 부분 override + `subsidy_tags`:
  - cafe: population_trend 1.1·action_engagement 0.9 / `[digital, store_renovation, marketing]`
  - delivery_food: action_engagement 1.2·population_trend 0.9 / `[digital, marketing, store_renovation]`
  - restaurant: competition 1.1 / `[marketing, digital, store_renovation]`  (leaf restaurant.korean_meat 상속)
  - retail: population_trend 1.2 / `[digital, store_renovation, rent_utility]`
  - fashion: `[digital, marketing]`  / service: `[store_renovation, digital, education]`  / academy: competition 1.2·population_trend 0.8 / `[education, digital, store_renovation]`
- **risk_score_engine** (`compute(...)`): `industry_signal_weights: Optional[dict]=None` 파라미터 추가 → factor 빌드 후 `f.weight *= w.get(f.name, 1.0)` 보정(재분배 단계에서 정규화되므로 안전, all-1.0 이면 무변화). shim 에 `industry_risk_weights(business_type, industry_slug)` + `industry_subsidy_tags(...)` 추가. **4개 호출부 wiring**: onboarding / dashboard / reports / action_generator 가 `industry_signal_weights=industry_risk_weights(user.business_type, user.industry_slug)` 전달.
- **deep-report 프롬프트** (`insights.py` `get_deep_report`): 하드코딩 6업종 분기표(KPI/채널/손실프레임/객단가임계 + 외식업 손익임계) 삭제 → `{INDUSTRY_BLOCK}` placeholder → `system_prompt.replace("{INDUSTRY_BLOCK}", industry_prompt_block(current_user.business_type, current_user.industry_slug))` (system_prompt 가 `{X}` 예시 다수 포함한 plain string 이라 `.format()` 대신 `.replace()`). 상권유형/상권변화지표/HHI/채널룰#1 등 generic 부분은 유지.
- **검증**: `validate_packs` ✓ 9팩 / `from app.main import app` ✓ / `{INDUSTRY_BLOCK}` 잔재 없음(placeholder+replace 2회만) / risk_signal_weights 팩 반영·leaf 상속·shim·`compute` 가중치 곱·정규화 후 cafe-weighted > base / subsidy_tags ✓.

### P2b — 구조화 콘텐츠(hero_kpis·channels·copy_tone) + marketing-strategy 프롬프트 외부화 (이번 단계)

- **스키마** (`schema.py`): `KPI`/`Channel`/`CopyTone` Pydantic 모델 + `FIT_VALUES`(high|medium|low|avoid)·`CONFIDENCE_VALUES`(measured|estimated|hypothesis). `IndustryPack` 에 `hero_kpis: list[KPI]` / `channels: list[Channel]`(applicable·fit·entry_cost_won·monthly_budget_min/max_won·fee_pct·per_unit_cost_won·primary_metric·roi_note·confidence·source) / `copy_tone: CopyTone`(vocab·loss_frames·examples·do·dont) 추가. 전부 Optional/빈 디폴트 → 기존 6+leaf+unknown 팩 무영향.
- **콘텐츠** — 리서치 벤치마크로 3개 팩 채움: `cafe`(hero_kpis 5: 객단가/테이블점유시간/재방문율/평일매출비중/원가율 + channels 8: 네이버스마트플레이스·인스타광고·네이버플레이스CPC·카카오친구톡·블로그체험단·배민(low)·전단지(low)·무신사(avoid) + copy_tone) / `delivery_food`(hero_kpis 5: 객단가/배달비중/식재료비율/별점/영업이익률 + channels 8: 배민울트라콜·배민CPC·요기요·알림톡·당근·인스타(low)·네이버플레이스·무신사(avoid) + copy_tone) / `academy`(hero_kpis 4: 재등록률/정원충족률/강사료비율/영업이익률 + channels 7: 당근비즈프로필·당근광고·네이버플레이스·전단지·알림톡·인스타·배민무신사(avoid) + copy_tone). 모든 ROAS/ROI 는 `confidence: hypothesis`, 출처 있는 비용만 `measured`.
- **shim**: `industry_channels_block(business_type, industry_slug)` — `pack.channels` 를 "## 업종 채널 근거표 — 이 표 밖 ROI/ROAS 생성 금지" 마크다운으로 렌더 (applicable=False 채널은 생략, fit 한글화).
- **insights.py marketing-strategy 프롬프트** (`get_marketing_strategy`): 하드코딩 6업종 채널 우선순위표 + 채널별 비용/ROI 핵심 + 손익 임계 삭제 → `{INDUSTRY_BLOCK}` + `{CHANNELS_BLOCK}` placeholder → `system_prompt.replace("{INDUSTRY_BLOCK}", industry_prompt_block(...)).replace("{CHANNELS_BLOCK}", industry_channels_block(...))`.
- **검증**: `validate_packs` ✓ 9팩 / `from app.main import app` ✓ / cafe/delivery 5+8·academy 4+7 로드·leaf 빈 상속·타 팩 무영향 ✓ / placeholder 잔재 0(전부 replace 처리) / `industry_channels_block` 렌더 출력 확인 ✓.

### P2c — 지원사업 카테고리 태그 + RAG 매칭 부스트 (이번 단계)

- **태그 유틸** (`app/utils/subsidy_tags.py`): `SUBSIDY_CATEGORY_TAGS` 14종(policy_loan/credit_guarantee/consulting/digital/store_renovation/education/restart_exit/employment/marketing/rnd/rent_utility/commercial_district/voucher/tax_relief — 업종팩 `subsidy_tags` 와 동일 체계) + `_TAG_KEYWORDS` + `infer_subsidy_category_tags(text)` (제목+설명 소문자 부분일치로 추론).
- **DB**: `Subsidy.category_tags`(ARRAY(Text), nullable) 컬럼 + 마이그레이션 `009_add_subsidy_category_tags.py`(down=`008_industry_slug`). `seed_subsidies.py` 가 적재 시 `infer_subsidy_category_tags(title+description)` 로 자동 채움.
- **shim**: `industry_subsidy_tags(business_type, industry_slug)` (P2a 에 추가됨) 사용.
- **rag_service** (`search_subsidies_filtered`): `industry_slug: Optional[str]=None` 파라미터 추가. 후보 풀 `max(top_k*4, 12)` 로 확장 → 각 공고의 `category_tags`(없으면 `infer_…` 폴백) ∩ 사용자 업종팩 `subsidy_tags` 교집합 1개당 +0.12(최대 +0.3) 부스트 → `relevance_score = 1.0+boost`, `category_tags`·`tag_match` 키 추가 → `(relevance_score desc, deadline asc)` 정렬 → ICP 재순위 → `[:top_k]`. **6개 호출부 wiring**: onboarding/dashboard/subsidies/reports/insights×2 가 `industry_slug=current_user.industry_slug` 전달.
- **검증**: `validate_packs` ✓ 9팩 / `from app.main import app` ✓ (순환 import 없음) / `seed_subsidies` import ✓ / 마이그레이션 009 import ✓ / `infer_subsidy_category_tags` 7샘플 → 전부 표준 14종 내 / `industry_subsidy_tags` ✓ / 부스트 산식 시뮬(카페×디지털전환공고 overlap 3 → relevance 1.3) ✓.
- **⚠️ DB 환경에서**: `alembic upgrade head` → `python -m scripts.seed_subsidies` (재적재해야 `category_tags` 채워짐).

### P3a/b — 나머지 4팩 콘텐츠 채우기 + marketing_audit 채널 힌트 도출 (이번 단계)

- **콘텐츠** — `restaurant`/`retail`/`fashion`/`service` 4팩에 `hero_kpis`(각 5)·`channels`(7~8, fit·비용·지표·roi_note·confidence·source·applicable)·`copy_tone`(vocab·loss_frames·examples·do·dont) 추가. 리서치 벤치마크(농식품부 외식업체 경영실태조사·KB 자영업·업계 통설 등) 기반, ROAS/ROI 는 전부 `confidence: hypothesis`. + `restaurant.korean_meat` 에 자체 `hero_kpis`(테이블단가/회전율/단체예약비율/영업이익률 — group 의 "점심 회전율" 대신) override (channels/copy_tone 은 restaurant 상속). → **9팩(7군 + academy + korean_meat leaf) 전부 prompt_block·5종 가중치·hero_kpis·channels·copy_tone·subsidy_tags 보유.**
- **shim**: `industry_top_channel(business_type, industry_slug)` — `pack.channels` 중 `fit=='high'` 인 첫 채널명 반환.
- **marketing_audit**: 하드코딩 `_TOP_CHANNEL_LABEL` 딕셔너리 + `SLUG_*` 임포트 제거 → `_industry_channel_hint` 가 `industry_top_channel(...)` 사용.
- **검증**: `validate_packs` ✓ 9팩 / `from app.main import app` ✓ / 4팩 hero_kpis 5·channels 7~8·copy_tone / korean_meat hero_kpis 4(override)·channels 7(상속) / `industry_top_channel`(cafe→네이버스마트플레이스, delivery→배민울트라콜, service→네이버예약, unknown→None) / `_industry_channel_hint` ✓.

### P3c — 프론트 출처칩 (이번 단계)

- **백엔드** (`routers/knowledge.py`): `GET /knowledge/my-pack`(auth) — 로그인 사용자에게 적용 중인 팩(`resolve_for(industry_slug, business_type)`) → `{id, name, group, version, reviewed_date, source_count, sources:[{label,url,year}], is_unknown}`. `/knowledge/industries` 에도 `version`·`source_count` 추가.
- **프론트**: `MyIndustryPack`·`IndustrySource` 타입 + `api.getMyIndustryPack()`. 컴포넌트 `components/common/IndustryPackChip.tsx` — 마운트 시 `/my-pack` fetch → "이 진단은 [업종명] 플레이북 v_n · 검수 YYYY.MM.DD 기준 · 출처 N건" 칩 렌더, 클릭 시 sources 목록 + "업종 평균·벤치마크 추정값 포함, 실제와 다를 수 있음" 안내 펼침. 미등록(`is_unknown`)이거나 조회 실패 시 아무것도 렌더 안 함. **인사이트 페이지** 콘텐츠 영역 최상단(전 탭 공통)에 배치.
- **검증**: `validate_packs` ✓ 9팩 / `from app.main import app` ✓ (`/knowledge/my-pack`·`/industries` 등록) / `my_pack` 로직(cafe→"카페·베이커리 v1 검수 2026-05-11 출처 1건", slug 없으면 business_type 분류("치킨집"→delivery_food), 미등록→is_unknown) ✓ / `npx next build` ✓ 15라우트(에러 0, /insights 18.5kB). ⚠️ 실제 화면 렌더는 dev 서버·브라우저 없어 미확인 — 빌드·타입체크만 통과.

**남은 것 (P3 잔여)**:
- ① `match.seoul_business_codes`·`ksic_codes` 정밀화 — 서울 OA-15577 점포-상권 코드명세 + KSIC 10차 세세분류표 **다운로드 필요**
- ② 스키마 `seasonal_calendar`·`commercial_zone_fit`·`zone_overrides` + menu-strategy/location 활용 + `Store.commercial_zone_type` 저장·백필
- ③ subsidy 메타스키마 더 확장(eligible/excluded_ksic·revenue_ceiling·biz_age·owner_age — 하드 자격 필터링)
- ④ korean_meat copy_tone override (현재 restaurant "점심" 톤 상속 — prompt_block/hero_kpis 는 이미 고기·구이용)
- ⑤ 대시보드에도 출처칩 추가(현재 인사이트 페이지만)

---

## 2026-05-11 — 배포 마이그레이션 핫픽스 + 학원 5 leaf + data_caveats + 내 가게 정보 페이지

- **배포 핫픽스 (`8a1ca5d`)**: Render(Docker 빌드)에 마이그레이션 단계 없어서 008/009 미적용 → `users.industry_slug` 없음 → 로그인 전체 500. `backend/Dockerfile` CMD + `railway.toml` startCommand 를 `alembic upgrade head && uvicorn …` 로 변경 → 컨테이너 부팅 시 자동 마이그레이션. ⚠️ Render 배포 로그에서 `Running upgrade … -> 008_industry_slug` 찍히는지 확인 필요. (Render 대시보드에 Start Command override 걸려 있으면 거기도 같이 바꿔야 함.)
- **학원 5개 leaf 팩** — `academy.exam`(입시·교과) / `academy.coding`(코딩·로봇·SW) / `academy.art`(미술) / `academy.pe`(체육·태권도·발레·수영) / `academy.language`(어학) — group=academy 상속, 특성 다른 것만 override. priority 15 (restaurant 의 "회" 같은 1글자 키워드 오탐 회피 위해 앞쪽). 리서치(통계청 사교육비조사 2024·디지털새싹·태권도장 마케팅 논문 등) 기반 prompt_block·hero_kpis·channels·copy_tone·subsidy_tags·risk_signal_weights. 코딩학원은 정부 디지털교육 지원이 핵심이라 channels 에 "정부 사업 운영" 채널 + subsidy_tags digital 포함. 미술/어학은 입시 vs 취미·아동, 아동 vs 성인 두 갈래 — prompt_block 에 "사장님께 어느 쪽인지 확인" 명시. → 총 **14팩**.
- **`data_caveats` 스키마 필드** (`list[str]`) — 공공데이터 해석 함정. `academy` 에 4건(추정매출=카드승인일 기준 → 학원은 등록일·자동결제일에 매출 스파이크 → 요일·일자 패턴 곧이곧대로 해석 X / 학기·방학 시작월 결제 폭증 / CMS 자동이체 과소집계 / 추정매출=상권 동종업종 추정치≠실매출). leaf 들이 상속. `industry_prompt_block` 이 `prompt_block` 뒤에 "## 데이터 해석 주의" 섹션으로 자동 부착 → deep-report·menu·marketing·action_generator 프롬프트 전부 받음. shim 에 `industry_data_caveats`·`industry_name` 추가.
- **내 가게 정보 페이지** (요청: "온보딩 다시할수있는 개인 페이지") — 백엔드 `PATCH /onboarding/profile` (`UpdateProfileRequest/Response`, 사업자번호 재검증 없음, `industry_slug`/`business_type`/`business_start_date` 부분 수정). 프론트 `/profile` 페이지: 상호·주소·현재 업종(플레이북 v_n·검수일) 표시 + 업종 `<select>`(자동감지 + 업종군·세부 들여쓰기 — 학원이면 입시·코딩·미술·체육·어학 leaf 가 뜸) + 저장. 대시보드 헤더에 "내 가게" 링크 추가. `api.updateProfile()`. **DB 마이그레이션 불필요**(기존 컬럼만 사용).
- **검증**: `validate_packs` ✓ 14팩 / `from app.main import app` ✓ (`/onboarding/profile` 등록) / classify 27케이스(학원 5 leaf 정확 분류 + 타 업종 무영향) ✓ / data_caveats 상속·prompt_block 부착 ✓ / `npx next build` ✓ 16라우트(/profile 포함, 에러 0).

**※ 학원 카카오 카테고리는 가입 시 자동 추정이 부분적임** — 카카오 로컬 검색이 "입시,보습학원/외국어학원/미술학원/컴퓨터학원/태권도장" 식으로 세분돼 있으면 leaf 키워드와 매칭되지만, 그냥 "학원"으로만 등록된 경우 academy 군으로만 잡힘 → 사장님이 온보딩 피커 또는 `/profile` 에서 직접 세부 선택. + leaf 의 `hero_kpis` 가 "사장님께 물어볼 3~4개"(재등록률·정원충족률·월수강료)를 정의 → 추후 인테이크 폼으로 활용 가능.

- **외식 음식점 세부 6 leaf** (group=restaurant) — `restaurant.korean_general`(백반·국밥·찌개 — 점심 회전형) / `restaurant.noodle_seafood`(칼국수·냉면 / 횟집·해물탕 — 면류 점심형 vs 횟집 고가예약형 두 갈래) / `restaurant.chinese`(중국집·마라탕·양꼬치) / `restaurant.japanese`(돈까스·우동 / 초밥·오마카세 / 이자카야) / `restaurant.western_asian`(파스타·스테이크·브런치·쌀국수·아시안) / **`restaurant.pub`(호프·포차·와인바 — 지금까지 unknown 으로 빠지던 업종 신설)**. priority 22(restaurant 30·korean_meat 25 보다 먼저). 리서치(농식품부 외식업체 경영실태조사 2024·KCD 데이터랩) 기반 prompt_block·hero_kpis·channels(6개씩)·copy_tone·subsidy_tags·risk_signal_weights. report_weights 는 restaurant 상속(미오버라이드). + `cafe.yaml` 키워드에서 bare "브런치" 제거(양식 레스토랑과 모호) → "브런치카페" 만. → 총 **20팩** (restaurant 군 아래 leaf 7개).
- **검증(외식)**: `validate_packs` ✓ 20팩 / classify 17케이스(외식 6 leaf 정확 + 브런치레스토랑→western_asian·브런치카페→cafe + 타 업종 무영향) ✓ / `from app.main import app` ✓.

- **카페 4 leaf** (group=cafe) — `cafe.coffee`(커피전문점 — 저가커피 vs 좌석형) / `cafe.dessert_bakery`(디저트·베이커리 카페·케이크·브런치카페 — 인스타 비주얼·기프트 시즌·폐기율) / `cafe.bakery`(동네 빵집 — 폐기율이 hero·'오늘 나온 빵' 알림) / `cafe.beverage`(버블티·과일주스·스무디 — 여름 성수기 의존·겨울 비수기 대비). priority 16. + cafe 키워드에서 bare "브런치" 제거.
- **배달 4 leaf** (group=delivery_food) — `delivery_food.chicken`(치킨 — 별점·사이드 부착률·공공배달앱) / `delivery_food.bunsik`(분식 — 저단가라 세트·묶음이 hero) / `delivery_food.pizza_burger`(피자·버거·샌드위치 — 피자는 1+1 프로모션·토스트는 오피스가) / `delivery_food.jokbal`(족발·보쌈·야식 — 심야 22~02시·토요일 +93%). priority 6. 출처: KCD 데이터랩·요기요 데이터·정보공개서.
- **검증(배치②)**: `validate_packs` ✓ **28팩** / classify 35케이스 ✓ / `from app.main import app` ✓ (`/onboarding/profile` 등록).

**총 28팩** (academy 군+5leaf / restaurant 군+6leaf+korean_meat / cafe 군+4leaf / delivery_food 군+4leaf / retail / fashion / service / unknown).
**다음 배치(예정)**: ③ 미용·서비스 계열(`service` → hair(미용실)/nail(네일·왁싱)/skincare(피부·에스테틱)/laundry(세탁)/pc_karaoke(PC방·노래방·당구장) — 동물병원·자동차정비·사진관은 별도 검토) ④ 소매(`retail` → cvs/super/food) + 패션(`fashion` → apparel/cosmetics/shoes_bag/optical).

> **마지막 업데이트**: 2026-05-11
