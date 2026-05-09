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

> **마지막 업데이트**: 2026-05-04
