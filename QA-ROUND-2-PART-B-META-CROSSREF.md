# QA Round 2 — Part B: Meta Cross-Reference

## 1. Cross-cutting issues (7건)

| # | 이슈 | 영향 페이지 | 영향 페르소나 | 단일 fix? |
|---|---|---|---|:---:|
| **CC-1 business_type taxonomy 분열** | onboarding raw → subsidies SQL, dashboard RAG, apply-draft prompt, daily_action_batch | C01·C02·C04·C05·C08·C13·C14 (~140명) + INV2·INV3 | **YES** — onboarding `BUSINESS_TYPE_MAP` 1 모듈 + 시드 normalize 마이그레이션 |
| **CC-2 silent fallback 미표시** | today_action + marketing/menu/deep GPT JSON parse fallback + onboarding `_safe()` | C09·C16 즉각 detect, P002·P022 | **YES** — 통일 envelope `{is_fallback, fallback_reason, source_kind}` + 프론트 chip |
| **CC-3 데이터 출처 라벨 0건** | dashboard, insights 4탭, subsidies, coupons | C16·INV3 직격 | **거의 YES** — `source: "Seoul VwsmTrdarSelngQq · 2024 4분기"` 필드 + UI fine-print |
| **CC-4 DB 세션 fanout 점유** | onboarding/complete, insights/marketing/menu/deep, dashboard Phase A | 모두 — C03·C08 spinner 이탈 | **YES** — dashboard.py phased pattern 4곳 복붙 |
| **CC-5 GPT 환각 숫자 (공식 0)** | insights /marketing fit_score/ROI/uplift/attach + /deep-report positioning x/y, impact/effort, KPI target + /menu fit_score, coverage_pct | C09·C16·INV1 30분 내 detect, INV2 50대 톤 거부 | NO — system prompt + 사후 grounding + few-shot + 회귀 4축 |
| **CC-6 시니어 한글 가독성 (text-xs/8-10px)** | landing L75, onboarding L194, insights SVG (text-[8/10/11px] 다수), dashboard, coupons QR | C01 ~25명 | **YES** — Tailwind text-xs 14px 재정의 + 시니어 모드 토글 |
| **CC-7 OWASP 빈틈 (CSRF + rate + JWT)** | landing OAuth state, callback state, /onboarding IP rate, /insights ?refresh GPT 분당 60회+, /coupons/scan 인증 없음, refresh rotation, subsidies/{id}/signal | INV3·INV1·INV4·TECH4 | NO — 7개 endpoint 패턴 적용. `_AuthRateTracker` 공통화하면 5개 일괄 |

## 2. Round 1 빠진 평가 축 (12건)

- **G-1 결제·과금 funnel**: `User.plan_tier` 컬럼만, 결제 라우터 0, Stripe/Toss/PortOne 0. **INV1·INV4 즉시 탈락 사유**
- **G-2 알림 발송 종단**: kakao_access_token 만료 fallback 미통보, **firebase-admin 미설치 시 silent skip** → 데모 환경 알림 0건. INV2·INV5 직격
- **G-3 APScheduler 크론**: `--reload`/워커 2+ 중복 실행 위험. daily_action 100명 GPT $1+/매일. APScheduler in-memory → 재시작 시 history 0
- **G-4 음성 STT**: Web Speech API iOS Safari 미지원. `voice.py:38-48` 단순 키워드 분류, "여기 사람이 안 와" → general fallback
- **G-5 PDF 리포트**: 60s 타임아웃. 한글 폰트 임베딩 미확인 → 깨진 사각형 PDF 가능
- **G-6 InsightCache 무효화**: week_key ISO 주차. **invalidation 트리거 없음** — onboarding 변경 시 캐시 그대로. 마감 지난 보조금 노출
- **G-7 다국어**: `<html lang="ko">` 고정. C12 종로 외국인 사장 페르소나 0건. STT lang="ko-KR" 고정
- **G-8 모바일 ≤320px**: SVG 포지셔닝맵·BarChart fixed viewBox로 360px 미만 폰에서 라벨 잘림. C01 시니어 구형 폰
- **G-9 PWA 설치·아이콘**: `/icons/icon-*.png` 부재 (Round 1-D P0-5)
- **G-10 백업·복구**: PG 자동 백업, ChromaDB persist 백업, GDPR 삭제 요청 처리 0건. INV3 감점
- **G-11 회귀 테스트**: backend/tests/, frontend/__tests__/ 디렉터리 부재. golden set 0
- **G-12 텔레메트리**: Sentry/GA4/PostHog 0건. retention/funnel/체류시간 측정 도구 0. **INV1·INV4 합격 기준**

## 3. 데모데이 P002·P008·P022 5분 시뮬레이션

### P002 마포 카페 30대 SNS

| 시각 | 동작 | 막힐 지점 |
|---|---|---|
| 0:00-0:15 | landing → 카카오 1탭 | OAuth state 없음 (CC-7) — 표면적 OK |
| 0:15-0:45 | 카카오 인증 0.25s | PRIORITY-VERIFY 통과 |
| 0:45-2:30 | 온보딩 3단계 | **막힘 90%**: /complete fanout (CC-4). 60s+ spinner → INV1·INV4 즉시 탈락 |
| 2:30-3:00 | 대시보드 risk_score 67 + 47% 하드코딩 | INV3 출처 추궁 |
| 3:00-4:00 | 매칭 지원사업 → 시드 마포 통과 | application_url 도메인 단위 — 외부 사이트 헤맴 |
| 4:00-5:00 | insights → /marketing fit_score 92 / ROI 230% | **CC-5 환각**. 30대 SNS = 임가람·INV1 같은 의심. INV1 REJECT |

### P008 마포 치킨 30대 배달앱

| 시각 | 동작 | 막힐 지점 |
|---|---|---|
| 0:00-2:00 | 가입 + onboarding | 통과 (단 fanout) |
| 2:00-2:45 | 매칭 지원사업 | **CC-1**: business_type "치킨" raw → 시드 모두 "음식점" → **매칭 0건**. "전 업종" 9건만 |
| 2:45-3:30 | "왜 카페 지원금이 우리 가게에?" | INV2 박순자 1분 내 "자영업 안 해본 사람" 코멘트. INV3 동시 탈락 |
| 3:30-4:30 | insights /competition | A탭 통과. **quarterly_change_percent 명칭 오류** — 본인 매출로 오해 |
| 4:30-5:00 | /marketing 배달 광고 ROI 230% | 환각. P008 핵심 고민 (배민 광고비) actionable 답 0건 |

### P022 강남 카페 35세 데이터분석

| 시각 | 동작 | 막힐 지점 |
|---|---|---|
| 0:00-1:30 | 가입 + onboarding | 통과 |
| 1:30-2:30 | 대시보드 매출 6,200만원 → risk 30점 녹색 | 빈 카드 위험. 즉시 콘솔 열어 출처 추궁 |
| 2:30-3:30 | insights SVG 포지셔닝맵 / SWOT / KPI gauge | **CC-5 환각 폭로**: positioning_map x/y 공식 0, KPI gauge 거짓 진척도. C16 30분 내 detect |
| 3:30-4:00 | /marketing budget_scenarios | "expected_uplift_won 1,250,000원" 공식 0 → 즉시 캐물음 |
| 4:00-4:30 | PDF 리포트 60s 타임아웃 | **G-5 한글 폰트 깨짐 가능** |
| 4:30-5:00 | F12 콘솔 응답 검사 | source 0건, relevance_score=1.0 literal, fit_score 무근거 → INV1·INV3 동시 탈락 |

### 5분 데모 종합

3명 평균 5분 안에 3-4건 명백한 막힘. **INV2 박순자는 P008 1분 내 탈락 단정**. INV1 김도윤 P022에서 retention 도구 0 + GPT 비용 가드 0 REJECT. **데모 통과 확률 현 상태 0~10%**.

## 4. ADR 001~006 일치도

| ADR | 결정 | 적용 | 누락 | 우선순위 |
|---|---|---|---|---|
| **001** 손실 프레이밍 | "추천합니다 → 놓치고 있습니다" | action_generator system prompt, dashboard loss_message, subsidies | (1) dashboard UI에 loss_message 미노출, (2) **insights 4탭 손실 카피 0건** — "ROI 230% 향상" 이익 프레이밍, (3) action_generator fallback stub은 추천 톤, (4) 회귀 테스트 0건 | **HIGH** — 핵심 차별점 50% 미만 |
| **002** k-anonymity | 사회적 증거 k=10 | social_proof K_THRESHOLD=10 enforce | (1) **cold-start 47% 하드코딩** ADR 정신 위배, (2) PotentialSubsidyBadge UI에 k_value 안내 0건 | **HIGH** — INV1 "샘플 부족 fallback 명확해야" 위반 |
| **003** 하루 1액션 | UniqueConstraint | daily_action 모델 + on_conflict_do_nothing | UI에 "하루 1개" 가이드 0건. 액션 완료 후 새 액션 fallback 동선 0건 | MEDIUM |
| **004** Kakao > FCM > silent | notification 우선순위 | notification_service kakao 401 시 refresh | (1) **firebase-admin 미설치 silent skip** → 데모 알림 0건, (2) Kakao "나에게" API는 본인에게만 — 채널 가이드 0건, (3) NotificationLog 테이블 미확인 | **HIGH** — INV5 직격, 데모 통과 직접 막음 |
| **005** ChromaDB | RAG 비용 0 MVP | rag_service 인덱싱, legacy search_subsidies | **active path는 SQL 필터만**, ChromaDB 호출 0회. relevance_score=1.0. 벡터 임베딩 dead code → ADR 자체 의미 X | **HIGH (정직성)** — INV1·INV3·임가람 즉시 추궁 |
| **006** JWT 30일 | 소상공인 재접속 | jwt 30일 exp | refresh rotation 시 구토큰 무효화 부재. tokenVersion/blacklist/jti 0건. OWASP A02 | MEDIUM — User.token_version 컬럼 1건 |

**총평**: ADR 001(50%), 002(cold-start 위배), 005(dead code) 3개가 ADR 위반. 004(FCM silent skip)가 데모 환경 의존 리스크.

## 5. P0 재정렬 (Round 1 14건 → 합리적 9건)

### 진짜 P0 (9건)

| # | 이슈 | 출처 | 왜 P0 |
|---|---|---|---|
| **P0-A** | sw 2.js/3.js precache + /icons/icon-*.png 부재 | D-4·5, B-P1-8 | **5분 안에 TECH2 + INV5 즉시 탈락**. git rm + 이미지 2개. 시간 ROI 최고 |
| **P0-B** | business_type taxonomy 정규화 (CC-1) | D-1 | **P008 데모 1분 내 매칭 0건**. seed normalize + onboarding 매핑 1 모듈 |
| **P0-C** | onboarding/complete + insights 3개 phased (CC-4) | A-3, C-3, PRIORITY-VERIFY 1순위 | **P002 데모 60s spinner 직격**. dashboard 패턴 복붙 4곳 |
| **P0-D** | 47% 하드코딩 제거 + cold-start 정직 라벨 (ADR-002) | B-P0-1, DATA-AUTH RED #1 | 매번 모든 사용자 노출. INV1·INV3 즉시 탈락. 2줄 수정 |
| **P0-E** | OAuth state CSRF + JWT token_version + insights ?refresh rate limit (CC-7 묶음) | A-1, A-5, C-4 | OWASP A01·A02·API4 동시. INV3·TECH4. 패턴 1개 추출하면 7곳 일괄 |
| **P0-F** | GPT 환각 숫자 grounding/라벨 (CC-5) | C-2, B-2, DATA-AUTH RED #5 | C09·C16 30분 내 발각, INV1 REJECT. 단기: UI 칩 "추정치(AI 산출, 공식 미적용)" |
| **P0-G** | 알림 발송 종단 검증 (firebase-admin 설치 + 카톡 채널 인증 + NotificationLog) (G-2, ADR-004) | 신규 G-2 | **데모 환경 firebase 미설치 시 알림 0건**. INV2·INV5 직격 |
| **P0-H** | quarterly_change_percent 명칭/의미 정정 + 출처 라벨 (CC-3 묶음) | B-3, DATA-AUTH RED #4 | risk_score 핵심 factor가 misnamed metric 위 + INV3 출처 라벨 동시 해결 |
| **P0-I** | 시니어 가독성 + 위험도 의미 (CC-6) | A-1, B-4 | C01 25명 + INV2. Tailwind 재정의 + 4단계 등급 |

### P1 격하 (5건)

- onboarding stepper 부재 (시연자 입으로 보완)
- total_potential_amount 산술합 (UI 카피 1줄 라벨링)
- application_url 도메인 단위 (시연 보조금 3-4개만 손작업)
- eligibility_summary 1줄 (3-4개만 5-7 bullet)
- apply-draft rate limit + plan_tier (데모 후 1주 내)

## 6. 한 줄 요약 — 가장 시급한 3건

> **(1) sw 2.js/3.js git rm + /icons/icon-192/512.png 추가** — `sw.js` precache에 등재되어 사용자 브라우저로 배포 중. PWA 설치 실패. **30분 작업으로 TECH2·INV5 즉시 탈락 회피**.
>
> **(2) business_type taxonomy 정규화 (Kakao raw → canonical 10종)** — onboarding 매핑 1 모듈 + seed 정규화 마이그레이션. **P008 데모 1분 내 매칭 0건 차단**, RAG·apply-draft·daily_action 정확도 회복.
>
> **(3) onboarding/complete + insights 3개 phased pattern** — dashboard.py 패턴 복붙. **P002 데모 60s spinner 차단 + PRIORITY-VERIFY 1순위 + INV1·INV4 retention 진입**.

이 3건 미수정 시 P002·P008·P022 5분 데모 중 5명 투자자 4-5명이 첫 30~90초에 결함 detect. **통과 확률 0% (현재) → 40-50% (3건 fix) → 70-80% (P0 9건 fix)**.
