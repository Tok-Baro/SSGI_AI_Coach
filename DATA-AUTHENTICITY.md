# 데이터 진위 감사 리포트

검증일: 2026-05-07. 정적 코드 분석 + 라이브 API probe (curl 샌드박스 차단으로 코드 매칭으로 대체)
범례: REAL(외부 API/DB 직출) · DERIVED(REAL→공식) · GPT(GPT-4o 출력) · SEED(시드 상수) · HARDCODED(literal) · CACHED(InsightCache 주간)

## 1. 페이지별 필드 추적 요약

### 대시보드 (`backend/app/routers/dashboard.py`)
| 필드 | 출처 | 위치 | 위험도 |
|---|---|---|---|
| user.* | REAL DB | dashboard.py:228-232 | ok |
| risk_score | DERIVED | risk_score_engine.py:83-269 (6-factor 가중평균) | ok |
| risk_factors[] | DERIVED | risk_score_engine.py:108-241 | ok |
| risk_trend[] | REAL DB | DailyAction.risk_score history | ok |
| trend_direction | DERIVED | risk_score_engine.py:257-265 | ok |
| **today_action.title/description** | GPT (fallback 있음) | action_generator.py:135-150, 152-189 silent stub | medium |
| today_action.risk_score | DERIVED | RiskScoreEngine | ok |
| **subsidy_matches[]** | SEED | rag_service.py:93-169, seed_subsidies.py:21-340 | HIGH |
| subsidy_matches[].relevance_score | HARDCODED 1.0 | rag_service.py:151 | medium |
| total_potential_amount | DERIVED sum of SEED | dashboard.py:149 | medium |
| loss_counter.daily_loss_won | DERIVED `/365` | dashboard.py:173 | medium |
| loss_counter.accumulated_loss_won | DERIVED 합성 | dashboard.py:174-176 | medium |
| peer_percentile | DERIVED w/ k≥10 ✓ | dashboard.py:194-199 ADR-002 | ok |
| upcoming_events[] | REAL Seoul API | culturalEventInfo | ok |
| population_trend | REAL Seoul API | SPOP_LOCAL_RESD_DONG, T-1..T-7 walk | ok |
| **social_proof** | k≥10 게이트 OK, but cold-start HARDCODED | social_proof_service.py:48,54 | HIGH |
| coupon_stats / action_completion_rate | REAL DB | dashboard.py:60-76 | ok |

### Survival Score (`/insights/survival-score`)
- **GPT 0회**, 결정론적 룰 — 가장 깨끗한 카드
- closed_avg_months / survival_avg_months: REAL Seoul (`CLSBIZ_MT_AVRG`, `SU_BIZS_MT_AVRG` from VwsmTrdarIxQq)
- pattern_similarity_pct: DERIVED `triggered/total*100` — **명칭 오해 소지**
- **survival_action**: 5개 hardcoded dict (insights.py:1414-1426). AI 코칭으로 표시되지만 실제는 if-else

### `/insights/competition`
- ~95% REAL (Seoul + Kakao + 기상청 직출)
- **Caveat**: `sales_data.quarterly_change_percent` (seoul_api_service.py:148-150)는 실제로 분기 변화율이 아니라 intra-period dispersion `(avg − median)/median*100`. Risk Score 엔진의 "매출 트렌드" factor에 그대로 흘러감

### `/insights/deep-report`, `/insights/marketing`
- 입력 데이터는 REAL Seoul, 출력은 GPT prose
- `/marketing` 의 fit_score, expected_roi_pct, expected_uplift_won, expected_attach_rate_pct, monthly_uplift_potential_won, impact_score, effort_score, budget_scenarios[].expected_uplift_won — **전부 GPT 환각**, 공식 0, temperature 0.7

### `/subsidies/matches`
- 100% SEED. seed_subsidies.py:21-340 = 15 hand-typed entries
- ChromaDB 벡터 검색 코드는 존재하지만 active path에서 호출 안 됨. SQL `target_regions.any` 만 사용
- relevance_score = 1.0 literal

### `/coupons`
- 100% REAL DB (사용자 생성 콘텐츠)

## 2. 🔴 RED FLAGS

1. **하드코딩 47% 사회적 증거** — `social_proof_service.py:48,54` "2025년 {dong} 소상공인 47%가 디지털전환 지원금 수혜" 출처 없음. k<10일 때 노출
2. **모든 보조금 SEED** — 시드 author-curated. URL은 진짜이지만 deadline/amount/eligibility는 best-effort. 사용자는 권위 정보로 읽음
3. **survival_action 5개 hardcoded dict** — AI 코칭으로 표시되지만 if-else
4. **quarterly_change_percent 명칭 오류** — Risk Score "매출 트렌드" factor의 입력. 위험도 점수 자체가 misnamed metric 위에 서 있음
5. **/marketing GPT 환각 숫자 다수** — formula 없이 temperature 0.7로 산출
6. **today_action silent GPT fallback** — 실패 시 stub 반환하면서 `is_fallback` flag 없음. UI는 동일하게 "AI 액션" 표시
7. **loss_counter `/365` 단순 환산** — 측정값 아닌 행동경제학 장치
8. **relevance_score = 1.0 literal** — 모든 보조금. 의미 없음

## 3. 🟡 보안 이슈 (별도 발견)

`backend/.env` 가 시크릿 키와 함께 disk에 평문. 다음 키들 노출:
- `SEOUL_API_KEY=457761696b646c7737327269637776`
- `NTS_API_KEY=Y2Cfej9p…`
- `KAKAO_REST_API_KEY=e409d8160628…`
- `OPENAI_API_KEY=sk-svcacct-…`

`.gitignore` 확인 필요. 만약 commit됐다면 키 즉시 rotate.

## 4. 라이브 probe 권장 (사용자가 직접 실행)

샌드박스로 못 했으니 사용자가:
```bash
curl -m 30 "http://openapi.seoul.go.kr:8088/457761696b646c7737327269637776/json/VwsmTrdarSelngQq/1/3/"
curl -m 30 "http://openapi.seoul.go.kr:8088/457761696b646c7737327269637776/json/culturalEventInfo/1/3/"
curl -m 30 "http://openapi.seoul.go.kr:8088/457761696b646c7737327269637776/json/VwsmTrdarIxQq/1/3/"
```
기대: `RESULT.CODE=INFO-000`, `row[]` non-empty.
필드명(TRDAR_CD, SVC_INDUTY_CD_NM, THSMON_SELNG_AMT, STDR_YYQU_CD, GUNAME, TITLE, STRTDATE, ADSTRD_CODE_SE, TOT_LVPOP_CO, SU_BIZS_MT_AVRG, CLSBIZ_MT_AVRG)는 Seoul Open Data 문서와 코드 일치 확인됨.

## 5. 페이지별 종합

| 페이지 | 진위 비율 | 주요 위험 |
|---|---|---|
| Dashboard | ~70% | 보조금 SEED, 47% 하드코딩, today_action silent fallback |
| /competition | ~95% | quarterly_change_percent 명칭 오류 |
| /deep-report | 입력 REAL · 출력 GPT prose | SWOT/action_items/KPI 자유 서술 |
| /marketing | 입력 REAL · **숫자 GPT 환각** | fit/ROI/uplift/attach 무근거 |
| /menu-strategy | 동일 | 동일 |
| /survival-score | **가장 깨끗** | survival_action만 hardcoded dict |
| /subsidies | 100% SEED | 15 hand-typed |
| /coupons | 100% REAL DB | ok |

## 6. 우선순위 fix

1. **47% 하드코딩 제거 또는 재구성** (social_proof_service.py:48,54) — 가장 큰 단일 환각, 매번 노출
2. **today_action GPT fallback 시 `is_fallback: true` flag 추가** — UI에서 구분 표시
3. **`quarterly_change_percent` 명칭/의미 수정** — 진짜 QoQ로 다시 계산하거나 이름 변경 (`intra_period_dispersion_pct`)
4. **시드 보조금 라벨링** — `source_kind: "curated_2026Q1"` 필드 추가, UI에 "큐레이팅" 명시
5. **/marketing 숫자 grounding** — fit/ROI/uplift는 이미 fetch한 benchmark/avg_ticket 위에 공식. 최소 "추정치 (AI 산출)" 접두
6. **loss_counter UI에 "추정 환산" 명시** — 현재 카드 텍스트 "매칭된 지원사업 최대금액 합계"는 정직하나, ÷365 부분도 노출 권장
7. **relevance_score=1.0 literal 제거 또는 실제 ChromaDB similarity 사용**
8. **.env 시크릿 키 노출 점검** — `git check-ignore .env` 후 commit 이력 확인. 노출됐다면 키 rotate
