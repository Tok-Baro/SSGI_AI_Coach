# QA Round 3 — Final Synthesis: SSGI AI Coach 데모데이 행동 계획

## 1. Executive Summary

**검증 규모**: 페르소나 300명(매트릭스) + 6명(7-day 시뮬레이션) + 10명 평가자(투자자 5 + 기술 5), 페이지 8개, P0 14건 → 메타 재정렬 9건, 검증 라운드 3회 (코드 grep + 라이브 로그 7,305줄 + 페르소나 시뮬)

### 가장 충격적인 발견 3건

1. **P020 정신건강 위험** — 관악 문구점 58세 폐업위험 페르소나가 SurvivalMatrixCard "패턴 유사도 80% critical"을 본 순간 회피 행동·잠재 정신건강 우려. ADR 001 무차별 적용은 도덕적·법적 책임 노출.
2. **risk_score 핵심 입력이 misnamed metric** — `quarterly_change_percent`는 시계열이 아니라 분기 내 (평균−중앙값)/중앙값 dispersion. 그 위에 risk_score, "전분기 대비 X%" UI 카피, GPT 환각이 쌓여 있음.
3. **RAG가 RAG가 아님** — ADR 005는 시드 인덱싱만 하고 active path는 SQL filter only. relevance_score=1.0 literal. INV1·임가람 30초 내 추궁 가능.

### 데모데이 통과 확률

- **현재**: **0~10%** (5분 시뮬에서 5명 투자자 중 4-5명이 30~90초 내 결함 detect)
- **3건 fix 후 (P0-A·B·C)**: **40~50%**
- **9건 fix 후 (P0-A~I)**: **70~80%**

### 다음 24시간 단일 결정

**데모 페르소나를 P002 (마포 카페 30대 SNS)로 고정하고, /marketing 탭과 SurvivalMatrixCard critical 케이스를 시연 동선에서 제외할 것인가**. 이 결정 후에야 P0 9건의 작업 순서가 의미를 가짐.

---

## 2. 데이터 진위 점수 (페이지별)

| 페이지 | 진위 | 핵심 결함 | 권장 수정 |
|---|---|---|---|
| Landing | 80% | OAuth state 부재, 시니어 가독성, 가치 카드 로컬 숫자 0 | state + text-xs 14px 재정의 |
| Callback | 90% | refresh rotation 시 구토큰 무효화 부재 | User.token_version 컬럼 |
| Onboarding | 75% | stepper 부재, /complete fanout, IP rate 부재, taxonomy 분열 | TAXONOMY_MAP + phased + stepper |
| **Dashboard** | **70%** | 47% 하드코딩, today_action silent fallback, quarterly_change_percent 명칭 오류, 보조금 SEED, social_proof N+1 | _cold_start None + is_fallback flag + QoQ 진짜 |
| /competition | 95% | quarterly_change_percent 명칭 오류 | 위 동일 |
| /deep-report | 입력 REAL · 출력 GPT prose | positioning_map x/y, impact/effort, KPI target 공식 0 | 백엔드 결정론 → GPT prose만 |
| /marketing | 입력 REAL · **숫자 GPT 환각 (CRITICAL)** | fit_score, ROI, uplift_won, attach_rate 무근거 + 키 mismatch | 위 + 키 mismatch |
| /menu-strategy | 동일 | coverage_pct, fit_score, expected_avg_ticket_change_pct 무근거 | 동일 |
| /survival-score | **95% (가장 깨끗)** | survival_action 5개 hardcoded dict | "기본 가이드" 라벨 또는 LLM |
| **/subsidies** | **30~40% (가장 위험)** | 100% SEED, taxonomy 불일치 한식/치킨/분식 매칭 0건, relevance=1.0, ChromaDB dead, application_url 도메인, source 누락 | TAXONOMY_MAP + 시드 22건 검증 + source 노출 |
| /coupons | 100% REAL DB | scan_count IP rate 변조, CreateCouponRequest 검증 부재 | HMAC + Pydantic Field |
| Offline / sw.js | 위험 | sw 2.js/3.js precache 배포, /icons/icon-*.png 부재, /api/* 캐시 user 분리 0 | git rm + 아이콘 + NetworkOnly |

---

## 3. 페르소나 시뮬레이션 결과

### 6명 retention 표

| 페르소나 | D0 가입 | D1 클릭 | D3 재방문 | D7 | D28 | 프로 | NPS |
|---|---|---|---|---|---|---|---|
| P001 종로 백반 60세 | 50% | 8% | 18% | 8% | 2% | 0% | -40 |
| P002 마포 카페 32세 | 88% | 60% | 70% | 55% | 28% | 0% | +10 |
| P008 마포 치킨 38세 | 82% | 55% | 65% | 50% | 22% | 0% | 0 |
| **P020 관악 문구점 58세** | **38%** | **12%** | **22%** | **5%** | **1%** | 0% | **-60** |
| P022 강남 카페 35세 | 92% | 80% | 75% | 50% | 18% | 0% | -10 |
| P024 연남 미용실 30대 | 90% | 70% | 75% | 60% | 35% | 0% | +20 |
| **평균** | **73%** | **48%** | **54%** | **38%** | **18%** | **0%** | **-13** |

INV1 D30 ≥ 25% **FAIL** (18%). 결제 모듈 부재로 프로 0% — INV1·INV4 즉시 탈락.

### 가장 위험한 페르소나 — P020

P020 관악 문구점 58세 폐업위험. 가입 직후 SurvivalMatrixCard "패턴 유사도 80% critical / 폐업 평균 53개월"이 자극적 빨간 그라데이션 + dashboard "당신이 놓친 247만원" 손실 카피 3연속. 손실 프레이밍 효과 조건 (검증 가능 + 책임 가능 행동) 두 조건 모두 미충족. 회피 행동 → 신뢰 붕괴 → **잠재 정신건강 우려**. NPS -60. ADR 001 무차별 적용 부메랑. **데모 시연에서 절대 보여주면 안 되고, 출시 전 세그먼트별 카피 분기 + 자살예방상담 1393 안내 의무화**.

---

## 4. 투자자 5명 평결 합본

| 투자자 | 현재 | 핵심 사유 | 9건 fix 후 |
|---|---|---|---|
| INV1 김도윤 (Series A) | **탈락** | retention 그래프 0, GPT 비용 가드 0, /marketing 무근거, LTV/CAC 0.89, 결제 모듈 부재 | 조건부 (텔레메트리 추가) |
| INV2 박순자 (Solo Angel) | **조건부 → 탈락** | "67점" 시니어 의미 실패, P008 1분 내 "자영업 안 해본 사람" | 합격 (시니어+taxonomy 후) |
| INV3 정희경 (서울시) | **탈락** | 출처 라벨 0, quarterly_change_percent 명칭 오류, 시드 hand-typed deadline 만료, source 누락 | 합격 (P0-D·H·B 후) |
| INV4 이재훈 (AC) | **탈락** | onboarding 60s spinner, 첫 가치 3분 초과, 결제 모듈 부재 | 조건부 (P0-C 후) |
| INV5 한지원 (CVC) | **탈락** | 카카오 알림톡 채널 부재 (send_to_me=본인 메모만), /icons/* 부재 | 조건부 (1개월 로드맵) |

**현재 합격 0 / 조건부 0 / 탈락 5**. 9건 fix 후 **합격 1~2 / 조건부 3 / 탈락 0~1**.

---

## 5. 기술 전문가 5명 합본

- **TECH1 윤대식**: 4 라우트 (`/marketing`, `/menu-strategy`, `/deep-report`, `/onboarding/complete`) DB 세션 점유 → 풀 고갈
- **TECH2 노수빈**: `sw 2.js`/`sw 3.js`가 precacheAndRoute에 등재되어 사용자 브라우저 배포 중
- **TECH3 임가람**: /marketing system prompt 평균 이상이지만 숫자 출력 공식 0건, few-shot 0건, T=0.7. impact_score 11·attach_rate 200% outlier 통과
- **TECH4 서민호**: OAuth state 부재 (CSRF), refresh rotation 무효화 0, /coupons/scan 인증 없음, /api/* 캐시 user 분리 0
- **TECH5 강유나**: text-xs/text-[8-11px] 192건. SurvivalMatrixCard critical이 시니어·폐업위험 신뢰 붕괴

**8x5 매트릭스 합격률 15%** (P=6, F=29, N=4, N/A=1). 9건 fix 후 50~60%.

---

## 6. 최종 P0 Fix List (9건, 실행 순서)

### P0-A: PWA precache 충돌파일 + 아이콘 부재
- **요약**: `sw 2.js`/`sw 3.js` precache 등재 + `/icons/icon-192/512.png` 부재 → PWA 설치 실패
- **위치**: `frontend/public/sw 2.js`, `sw 3.js`, `sw.js:1`, `frontend/public/icons/`
- **시간**: 30분
- **작업자**: 프론트엔드
- **검증**: `git status` untracked 사라짐, `sw.js` grep "sw 2.js" 0건, DevTools Manifest 에러 0
- **의존성**: 없음

### P0-B: business_type taxonomy 정규화
- **요약**: 카카오 raw "한식" vs 시드 "음식점" → 페르소나 ~140명 매칭 0건
- **위치**: `frontend/src/app/onboarding/page.tsx:87-89` + `backend/app/services/rag_service.py:125-128` + `backend/scripts/seed_subsidies.py:21-340`
- **시간**: 2시간 (TAXONOMY_MAP 모듈 + 시드 정규화 + 마이그레이션)
- **작업자**: 백엔드+프론트
- **검증**: P008·P001·P017 가입 → 매칭 ≥ 3건, "전 업종" 외 매칭 ≥ 2건
- **의존성**: 없음 (P0-H 후 권장)

### P0-C: phased pattern 4 라우트
- **요약**: `Depends(get_db)` + 외부 API gather + GPT 10~30s 동안 PG 점유
- **위치**: `backend/app/routers/onboarding.py:124-236`, `insights.py:201-205, 716-755, 1086-1125`
- **시간**: 4시간 (dashboard.py 패턴 복붙)
- **작업자**: 백엔드
- **검증**: 동시 10명 부하 ≤ 5s, P002 60s spinner 사라짐
- **의존성**: 없음

### P0-D: 47% 하드코딩 제거
- **요약**: `social_proof_service.py:48,54` 출처 0, ADR 002 위배
- **위치**: `social_proof_service.py:48,54` + `dashboard/page.tsx:509-513`
- **시간**: 20분
- **작업자**: PM+백엔드
- **검증**: 응답에 "47%" 0건, falsy 시 카드 숨김
- **의존성**: 없음

### P0-E: OAuth state + JWT token_version + insights rate limit (묶음)
- **요약**: OWASP A01·A02·API4 동시. 7개 endpoint 패턴화하면 5곳 일괄
- **위치**: `page.tsx:7`, `callback/page.tsx:18-23`, `auth.py:117-135`, `models/user.py`, `insights.py` 전체
- **시간**: 3시간 (state 30분 + token_version 1h + rate limit 1.5h)
- **작업자**: 백엔드+프론트
- **검증**: state 불일치 시 CSRF 에러, 구 refresh 거부, /insights 분당 6회 시 429
- **의존성**: 없음

### P0-F: GPT 환각 숫자 grounding/라벨
- **요약**: /marketing fit_score, ROI, uplift_won, attach_rate + /deep-report positioning x/y, impact/effort, KPI + /menu fit_score 모두 공식 0
- **위치**: `insights.py:862-1004, 933, 968-985, 811-814` (남성_매출 키 mismatch 동시)
- **시간**: 8시간 (단기 UI 라벨 1h / 장기 결정론 계산 7h)
- **작업자**: AI
- **검증**: `grounding_method: "formula" | "gpt_estimate"` 필드, golden set 5개 회귀 통과, outlier 0건
- **의존성**: P0-H 후 권장

### P0-G: 알림 발송 종단 검증
- **요약**: ADR 004 카카오 send_to_me=본인 메모만, firebase-admin 미설치 silent skip → 데모 알림 0건
- **위치**: `notification_service.py`, `kakao_service.py:18`, `requirements.txt`
- **시간**: 6시간 (firebase-admin 2h + NotificationLog 2h + ADR 004 재정의 2h)
- **작업자**: 백엔드
- **검증**: 데모 환경 푸시 1건 도달, NotificationLog success/fail 기록
- **의존성**: 없음

### P0-H: quarterly_change_percent 명칭 정정 + 출처 라벨
- **요약**: dispersion인데 risk_score "매출 트렌드"와 UI "전분기 대비 X%"가 시계열로 오해 + INV3 출처 라벨 동시 해결
- **위치**: `seoul_api_service.py:147-156`, `risk_score_engine.py:108-118`, `dashboard/page.tsx`, `insights/page.tsx`
- **시간**: 6시간 (이전 분기 fetch 4h + 출처 라벨 2h)
- **작업자**: 백엔드+프론트
- **검증**: `quarterly_change_percent` 진짜 QoQ + `area_dispersion_percent` 분리, "출처: 서울 VwsmTrdarSelngQq · 2024 4분기" fine-print
- **의존성**: P0-B 후 권장

### P0-I: 시니어 가독성 + 위험도 의미
- **요약**: text-xs/text-[8-11px] 192건 + dashboard "67점" 의미 불명 → C01 25명 + INV2 직격
- **위치**: `tailwind.config.ts`, `dashboard/page.tsx:166`, `insights/page.tsx`
- **시간**: 4시간 (Tailwind 재정의 1h + 4단계 등급 1h + 시니어 모드 토글 2h)
- **작업자**: 프론트+디자이너
- **검증**: text-xs = 14px, "위험도 67점 → 주의 단계" 한국어, 시니어 모드 18px
- **의존성**: 없음

**총 시간**: 33.5시간 (≈ 4-5일 1인 또는 2-3일 2인 병렬)

---

## 7. P1 Fix List (8건)

| ID | 요약 | 위치 | 시간 |
|---|---|---|---|
| P1-1 | apply-draft rate limit + plan_tier (GPT 비용 폭주) | `subsidies.py:79` | 1h |
| P1-2 | CreateCouponRequest Pydantic Field (음수, 50년, 1MB XSS) | `schemas/coupon.py:7-12` | 1h |
| P1-3 | scan_coupon HMAC 서명 (변조) | `coupons.py:119-140` | 2h |
| P1-4 | sw.js /api/* NetworkOnly (cross-user PII) | `sw.js:1` | 30m |
| P1-5 | today_action `is_fallback` flag + UI chip | `action_generator.py:148-150`, `dashboard/page.tsx` | 1h |
| P1-6 | onboarding stepper + IP rate limit | `onboarding/page.tsx:140-142`, `onboarding.py` | 2h |
| P1-7 | survival_action 5개 dict → "기본 가이드" 라벨 | `insights.py:1414-1426` | 2h |
| P1-8 | social_proof N+1 → 단일 GROUP BY | `social_proof_service.py` | 1h |

---

## 8. 데모데이 5분 시연 스크립트

**선정 페르소나**: **P002 마포 카페 30대 SNS 1년차** — D28 28%, NPS +10. 9건 fix 후 5분 막힘 없이 완주.

**제외 동선** (절대 보여주지 말 것):
- ❌ /insights/marketing (fit_score 92, ROI 230% — INV1 30초 내 환각 폭로)
- ❌ /insights/deep-report 60s 로딩 + positioning_map 환각
- ❌ SurvivalMatrixCard critical 빨간 그라데이션 (P020 정신건강 트리거)
- ❌ /coupons/scan 인증 노출
- ❌ F12 콘솔 (relevance_score=1.0, source 부재 발각)

**5분 동선**:
- **0:00~0:30** Landing → 카카오 1탭 → 0.25s callback ("이전 24s에서 0.25s로 개선" 멘트)
- **0:30~1:30** Onboarding stepper 1/3→2/3→3/3, /complete phased pattern (60s spinner 없음 강조)
- **1:30~2:30** Dashboard "주의 단계 (67/100)" + 출처 라벨 "서울 VwsmTrdarSelngQq · 2024 4분기" → INV3 합격 신호
- **2:30~3:30** 매칭 지원사업 → P002 카페로 정규화 → 마포구+카페 ≥3건 → "마포구 로컬크리에이터 800만원" 클릭 → application_url 신청 직링크
- **3:30~4:30** /insights/competition (95% REAL Seoul) → BarChart 벤치마크 → 출처 라벨
- **4:30~5:00** /coupons → QR 80×80 → 카톡 채널 공유 → "INV5가 좋아하는 카카오 시너지의 시작점"

**우회 멘트**: "AI 마케팅 전략 탭은 GPT 산출치 → 결정론적 공식 grounding 작업 중 (P0-F), 다음 1주 내 완료" — 정직성으로 INV3·임가람 호감.

---

## 9. 데모 후 1주 / 1개월 로드맵

### 1주 내 (Sprint +1)
- **결제 모듈 mock UI** — PortOne/Toss SDK + /upgrade 페이지 + 페이월 트리거 (INV1·INV4 LTV/CAC 진입)
- **GPT golden set 회귀** — backend/tests/golden/ 5×4 = 20개 스냅샷 + outlier 검증 + 손실 톤 정규식
- **P1 8건 일괄**
- **텔레메트리** — PostHog/GA4 (D7/D30 코호트, funnel, 알림 클릭률) — INV1 합격 도구

### 1개월 내 (Sprint +2~+4)
- **실보조금 50건 시드** — 22 → 50건. 정수현 PM 큐레이팅 + `source: "official_2026Q2"` + deadline 자동 만료 cron + ChromaDB legacy active path 전환 (relevance_score 진짜 cosine)
- **실사용자 테스트 5명** — C01·C03·C08·C09·C16 각 1명, 60분 인터뷰. 시니어 톤 분기 검증
- **카카오 비즈메시지/알림톡 정식** — 카카오싱크 인증 + 친구톡 채널 검수 → ADR 004 정상화. INV5 합격
- **INV3 발표 자료** — "서울시 API 8종", "k=10", "1년 내 폐업 사전 경보 정량 효과", QoQ 시계열 그래프

---

## 10. 한 줄 결론

**현재 5분 데모 0~10% 통과. P0-A·B·C 3건만 수정해도 40~50%, 9건 모두 70~80%. 다음 24시간 내 결정해야 할 단 하나는 "데모 페르소나를 P002로 고정하고 /marketing 탭과 SurvivalMatrixCard critical 케이스를 시연 동선에서 제외할 것인가"이며, 이 결정 없으면 P0 9건의 작업 순서가 의미를 갖지 못한다.**
