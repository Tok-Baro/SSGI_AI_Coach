# QA Round 1 — Part C: Insights

**중요**: `/survival-score`는 dashboard에서 소비됨, insights 페이지엔 없음.

## 1. 탭별 페르소나 통과 매트릭스

| Cluster | A 경쟁분석 | B 마케팅 | C 집중분석 | M 메뉴전략 | 종합 |
|---|:---:|:---:|:---:|:---:|---|
| C01 디지털절벽 노포 | FAIL | FAIL | FAIL | FAIL | "경영 인사이트" 헤더부터 외래어. SVG 포지셔닝맵·SWOT 50-60+ 한식 사장 1초도 응시 안 함. 60s 로딩 텍스트로 거리감 |
| C03 1년차 카페 | PASS | PARTIAL | PARTIAL | PARTIAL | A탭 BarChart 유익. budget_scenarios 3-Tier 의사결정 도구 적합. 다만 ROI 230% 곧이곧대로 받으면 거짓 약속 |
| C04 강남 고매출 | PASS | FAIL | PARTIAL | FAIL | A탭 벤치마크 만족. B탭 revenue_uplift_plan은 이미 객단가 높은 가게에 "더 올리세요" → 핵심 고민 (고비용)과 어긋남 |
| C06 가족경영 | PASS | PARTIAL | FAIL | FAIL | A탭 "주변 28곳 경쟁" 작동. SMS 카피 actionable. 그러나 deep-report에 "내 인건비" 환기 부재 |
| C08 폐업 임박 | FAIL | FAIL | FAIL | FAIL | survival-score는 dashboard에 격리. 폐업 임박이 "경영 인사이트" 누르면 "더 매출 내세요" 톤만 |
| C09 마케팅 실험족 | PASS | **DANGEROUS PASS** | PARTIAL | PASS | **타겟 사용자**. ROI 230%·fit_score 92에 흥분 → **30분 안에 환각 발견** → 이탈. 가장 먼저 이탈할 클러스터 |
| C12 종로 관광·전통 | PARTIAL | FAIL | PARTIAL | PARTIAL | 외국인 vs 내국인 분리 데이터 없음. SMS는 외국인에 무용 |
| C16 데이터 능숙 | PASS | FAIL | PARTIAL | PASS | A탭 raw 좋아함. **즉시 캐물음**: 출처 미표시, ticket_diff_pct 기간 불명, **CSV/JSON export 없음**, quarterly_change_percent 직접 식별 |

**구조적 모순**: insights 페이지는 C09·C16 타겟인데, **그 두 클러스터가 GPT 환각을 가장 빠르게 발견**.

## 2. 투자자 평결

- **INV1 김도윤 (Series A)**: **REJECT** — "fit_score 92, ROI 230%, expected_uplift_won 1,250,000원 어떻게 산출됐나 prompt 보여달라." marketing system prompt L862-1004 분석: response_format=json_object OK, 그러나 **모든 숫자 출력에 공식 0건**. T=0.7. "LLM이 그럴듯한 숫자 지어내는 전형."
- **INV2 박순자 (Solo Angel)**: **REJECT** — "내가 카페 사장 시절 이 페이지 받았으면 첫 화면에서 닫았다." 60초 로딩 + TOWS·SWOT·HHI·포지셔닝맵 MBA 단어. "현장에서 카페 운영해본 사람이 만든 페이지가 아니다." 부분 합격: B탭 ready_to_use_copies (SMS 140자, POP 50자) actionable.
- **INV3 정희경 (서울시 평가관)**: **CONDITIONAL PASS** — "서울시 API 8종+ 호출 확인. 합격선." 그러나 **데이터 출처 표기 미흡**. UI 어디에도 "VwsmTrdarSelngQq · 2024 4분기" 같은 명시 없음. quarterly_change_percent 명칭 오류 즉시 시정 요구. 재발표 전 출처 명시 + 명칭 수정 필수.
- **INV4 이재훈 (AC PM)**: **REJECT** — "60초 deep-report 로딩은 drop-off 직선." 카카오 알림톡으로 마케팅 카피 직접 발송하는 통합 없음.
- **INV5 한지원 (CVC)**: **PARTIAL PASS** — channel_priority enum에 kakao_ch 있지만 first_step GPT 자유 텍스트. 카카오싱크/카카오페이/카카오모먼트 광고 ID 발급 가이드 없음.

## 3. 기술전문가 8x5

### TECH1 백엔드
- async/await: PASS
- DB 세션: **FAIL P1** — `/marketing`, `/menu-strategy`, `/deep-report` 모두 `Depends(get_db)` + 14-coroutine gather + GPT 10-30s 동안 PG 점유
- 외부 API timeout: PARTIAL — `_safe()` 있으나 timeout 강제 없음, circuit breaker 0
- Pydantic v2: **FAIL** — 모든 5 엔드포인트가 plain dict 반환, response_model 없음
- N+1: WARN — `_compute_audit_and_icp` 내부 ICP 신호 fetch 의심

### TECH2 프론트
- 1715줄 **monolith** — 컴포넌트 6개 분리 필요
- TS any: **FAIL** — `deepReport: any`, `summary: any`, `tows: any`, `map: any`, `goal: any`, `items: any[]`
- 탭 lazy load: 데이터만 lazy, 컴포넌트 코드는 모두 번들 → first paint에 SVG 코드까지 로드
- Zustand persist: tab 상태 미persist → 새로고침 시 항상 "competition" 리셋

### TECH3 AI/ML — **CRITICAL** (섹션 4 참조)

### TECH4 보안
- rate limit: **FAIL** — `?refresh=true`로 GPT-4o 호출 분당 60회 가능. **악의적 토큰 소진 공격**
- PII: WARN — system prompt에 business_name/gu_name/dong_name 평문 → OpenAI 외부 송신

### TECH5 UI/UX
- 한글 가독성: **FAIL** — `text-[10px]`, `text-[11px]`, `text-[8px]` (SVG 라벨) 다수. SwotCard·BarChart 라벨 8-10px 50대 못 봄
- 터치 타겟: PARTIAL — UpliftCard 옵션 28-32pt 추정
- 손실 빨강 남발: PARTIAL — "주변 28곳", "유동인구 -3%", "1건당 1,200원 부족" 모두 빨강
- 한국어 자연성: PARTIAL — TOWS 매트릭스, Impact-Effort 2x2, Blue Ocean, fit_score 외래어
- 접근성: **FAIL** — SVG positioning_map, action_impact_matrix, 30일 차트 aria-label 0건

## 4. **GPT 환각 위험 분석 (TECH3 핵심 섹션)**

### 4.1 system prompt 구조 (insights.py:862-1004)
- 응답 원칙 7개 + JSON 스키마 + User prompt에 "할루시네이션 방지 (절대 준수)" 5개
- `response_format={"type":"json_object"}` ✅
- Temperature **0.7** (창작 모드, 환각 친화)
- max_tokens **4000** (출력 큼, 환각 표면적 큼)
- few-shot 예시 **0건** ❌
- Grounding score / 검증 단계 **0건** ❌

### 4.2 출력 필드별 grounding (CRITICAL 표시 = 공식 부재 GPT 환각)

| 필드 | grounding | 위험도 |
|---|---|---|
| `summary` 80자 | partial | LOW |
| `strategies[].title/description` | partial — `[근거]` 태그 강제 | MEDIUM |
| `strategies[].evidence` | partial | MEDIUM |
| `strategies[].expected_effect [근거: 데이터X]` | **WEAK — 형식만, 내용은 GPT** | **HIGH** |
| **`budget_scenarios[].expected_uplift_won`** | **NONE** | **CRITICAL** |
| **`budget_scenarios[].expected_orders`** | NONE | **CRITICAL** |
| **`channel_priority[].fit_score`** (0~100) | NONE | **CRITICAL** |
| **`channel_priority[].expected_roi_pct`** | NONE | **CRITICAL** |
| `revenue_uplift_plan.current_avg_ticket` | grounded | LOW |
| `target_avg_ticket` | partial | MEDIUM |
| `monthly_uplift_potential_won` | partial 공식 | MEDIUM |
| **`uplift_options[].add_price_won/expected_attach_rate_pct`** | **NONE** | **CRITICAL** |

### 4.3 menu-strategy 환각
- `gap_analysis.missing_categories[].competitor_coverage_pct` — NONE — HIGH
- `missing_categories[].fit_score` — NONE — HIGH
- `missing_categories[].expected_avg_ticket_change_pct` — NONE — HIGH

### 4.4 deep-report 환각
- **`positioning_map.us.{x,y}`** (0~100) — **NONE — 공식 0** — HIGH. x_label="가격대", y_label="품질·서비스"인데 가게의 실제 수치 없이 GPT 임의 좌표
- **`positioning_map.competitors[]`** — NONE — HIGH. 경쟁사 가격대/품질 데이터 prompt에 없음 → 완전 환각
- **`action_items[].impact_score/effort_score`** (1~10) — NONE — HIGH. ActionImpactMatrix SVG 좌표가 환각 위에 그려짐
- **`monthly_goal.kpis[].target_value/current_value`** — NONE — HIGH. 게이지 80%/50%/30%로 시각화 → **거짓 진척도**

### 4.5 임가람 평결
> "system prompt 설계는 평균 이상이다. 그러나 **세 가지 결정적 결함**: (1) 숫자 출력 필드에 공식 0, (2) few-shot 0건, (3) 사후 검증 0건. impact_score 11, attach_rate 200% outlier 통과 가능. 비용은 캐시 7일이라 1주 1회 OK이지만 ?refresh=true rate limit 시급."
> "ADR 001 손실 프레이밍 시스템 prompt 명시 OK. 평가 회귀 테스트 0건이라 톤 새어나오는지 모니터링 불가."
- 추가: PRIORITY-VERIFY의 `남성_매출`/`여성_매출` 키 mismatch (insights.py:811-814)가 prompt에 흘러 들어가면서 GPT가 항상 "남성 0%/여성 0%" 컨텍스트로 받음 → **환각 더 심해짐**

### 4.6 GPT 응답 파싱
- response_format=json_object + json.loads → 안전. 정규식 파싱 0
- fallback 발동 시 strategies 1개만, 나머지 missing → 프론트 null 핸들링 OK이지만 **UI에 "fallback 발동" 표기 없음** (DATA-AUTHENTICITY today_action silent fallback과 동형)

## 5. 발견 이슈 우선순위

### P0
- **P0-1**: `insights.py:811-814` 키 mismatch — 프론트는 fallback 있으나 백엔드만 수정하면 됨
- **P0-2**: GPT 환각 숫자 — UI에 "추정치 (AI 산출)" 명시 + tooltip "공식 미적용"
- **P0-3**: `/marketing`, `/menu-strategy`, `/deep-report` DB 세션 phased 분리 (PRIORITY-VERIFY P3)
- **P0-4**: rate limit 부재 — `slowapi` user당 분당 5회 제한

### P1
- P1-1: 데이터 출처 표기 (INV3) — "출처: VwsmTrdarSelngQq · 2024 4분기" fine-print
- P1-2: quarterly_change_percent 명칭 오류
- P1-3: 1715줄 monolith 분리 → `components/insights/`
- P1-4: 시니어 모드 폰트 8-10px → 14-16px
- P1-5: 카카오 알림톡 통합 (INV5)

### P2
- CSV/JSON export (C16, INV3)
- few-shot 예시 + golden set
- GPT 응답 사후 검증 (impact_score 1-10, attach_rate 0-100, target_value > 0)
- TS any 제거
- survival-score insights에 통합 (C08)
- SVG aria-label
- 외래어 한국화

## 한 줄 진단

insights는 **C09·C16 타겟인데 그 두 클러스터가 GPT 환각을 가장 빠르게 발견**. /marketing의 fit_score·ROI·uplift_won·attach_rate, /deep-report positioning_map 좌표·impact/effort_score·KPI target, /menu-strategy fit_score 모두 **공식 없이 GPT-4o T=0.7 즉흥**. INV1·INV4 REJECT, INV2 REJECT (50대 톤), INV3 CONDITIONAL, INV5 PARTIAL.
