# QA Round 1 — Part D: Subsidies + Coupons + Offline

## 1. Subsidies 페이지 (가장 중요 — 손실 프레이밍 핵심)

### 1.1 페르소나 매트릭스

| 클러스터 | 시나리오 | 판정 | 근거 |
|---|---|:---:|---|
| C01 디지털절벽 노포 | "사업계획서 초안" 버튼 누른다 | **FAIL** | 모달에 "GPT-4o가 사업계획서 작성 중" — 60대 노포 사장 모름. 모달 닫기 12pt × | 단일 (44pt 미만) |
| C03 1년차 카페 | 가입 직후 매칭 | **부분통과** | 시드 "마포구 로컬크리에이터", "청년 창업 지원금" 노출. ICP 신호 없어 마감 오름차순만. INV2 탈락 트리거 |
| C05 노원 동네상권 | 매출감소 호소 | **FAIL** | 노원 매칭 시드 1건뿐. target은 ["교육","돌봄","먹거리","재활용"] — 노원 분식·편의점·치킨과 zero-overlap. 19/20명이 빈 화면 |
| C06 가족경영 마이크로 | 4대보험 미가입 사장 자격 확인 | **FAIL** | `eligibility_summary` 1줄 ("서울시 소재 소상공인, 매출 10억 이하"). 4대보험·고용보험·등록기간 등 실제 자격 없음. 외부 이동 후 거절당해 신뢰 붕괴 |
| C08 폐업 임박 | 즉시 도움 | **부분통과** | "소상공인 폐업 재기 지원" 2,000만원 + "재기 특별자금" 5,000만원 매칭. loss_message는 단일 톤 — "재기 자금" 컨텍스트 라벨 부재 |
| C10 학원 인구절벽 | 학원 업종 매칭 | **부분통과** | 시드 "학원업 특화 경영개선" 1건. ICP 재순위 보정 가능 |
| C16 데이터 능숙 | 자격조건 상세 검색 | **FAIL** | UI에 필터 0개, 정렬 0개, 페이지네이션 없음 (top_k=10 고정) |

**🔴 CRITICAL: business_type taxonomy 불일치**

사용자 `business_type`은 onboarding에서 카카오 카테고리 두 번째 토큰을 raw 저장 ("음식점 > 한식" → "한식"). 시드 보조금의 `target_business_types`는 ["음식점","카페","소매업"...] — **canonical taxonomy 없음**.

RAG 필터 `Subsidy.target_business_types.any(business_type)`가 정확 일치 요구 → 사용자 "한식"은 어떤 시드와도 매치 안 됨 (모두 "음식점"). **시드 22건 중 한식·치킨·분식·호프 매칭 = 0건**. "전 업종" fallback 9건만 통과.

**클러스터 매칭률 정량 추정**: 시드 15건이 강남/마포/종로/노원 일부 + 비대상 서초/성동 등 커버. 관악구 직접 매칭 0건 — 관악 페르소나 ~70명이 "전국/서울시 전체"만 봄. **매칭 다양성 < 50%**.

### 1.2 투자자 verdict

- **INV1 (Series A)**: apply-draft GPT 비용 약 $0.04~0.05/회. 단가 9,900원 기준 OK이지만 **abuse 가드 0**. plan_tier 검사가 쿠폰엔 있고 사업계획서엔 없음 (`coupons.py:64` vs `subsidies.py:79`). 탈락 trigger.
- **INV2 (카페 운영자)**: loss_message 단순 합산, social proof 부재. `application_url` 도메인 단위 (강남구청 홈) — 사장이 신청 페이지 못 찾음. 탈락.
- **INV3 (서울시 평가관)**: **결정적 탈락**. 시드 22건 hand-typed. `deadline=date(2026,4,30)` 강남구 임차료 보조는 오늘 기준 마감. `source` 필드가 DB에 있지만 응답 누락 (subsidies.py:52-64). UI에 출처 표시 0%. "정부 지원사업 정보가 오래되거나 잘못됨" 탈락 기준 직격.
- **INV4 (AC PM)**: apply-draft 30~60초 GPT — 첫 가치 체감 3분 초과. SNS 공유 카드 없음.
- **INV5 (CVC)**: 카카오싱크와 무관 — 무난.

### 1.3 기술전문가

**TECH1**:
- N+1: `subsidies.py:48-66` for-loop 안 `social.get_subsidy_proof` await — 10건이면 10× DB roundtrip. 30~50× 가능
- `target_business_types.any('전국')` GIN index 미적용 시 full scan. 1000건 시 폭발
- ICP rerank가 같은 트랜잭션 → DB 세션 점유 길어짐

**TECH3**:
- **`search_subsidies_filtered`는 RAG가 아님**. SQL 필터만. ChromaDB 인덱싱은 시드에서만 호출, 활성 경로 호출 0회. `relevance_score=1.0` literal. Vector embedding은 dead code.
- legacy `search_subsidies` (L171)은 진짜 ChromaDB 검색이지만 어디서도 호출 안 됨
- `apply-draft` JSON mode 미사용 — 마크다운 prose. `whitespace-pre-wrap`로 렌더 (page.tsx:175) → `**bold**` 별표 그대로 노출

**TECH4**:
- **PII 평문 LLM 주입**: `action_generator.py:280-285` business_name + business_type + address 평문. 사업자번호는 마스킹 OK.
- subsidies/apply-draft rate limit 0
- `subsidies/{id}/signal` query string POST — CSRF 가능성, OAuth state 패턴 위반

**TECH5**:
- D-day 임박 단일 톤 (D-1과 D-30 동일 색)
- 신청 버튼 카피 "신청 페이지" — 동사 약함
- **매칭 사유 칩 0개** — composite_score/icp_boost가 응답에 없음
- 시니어 모드 폰트 토글 없음, D-day 칩 12pt 미만

### 1.4 데이터 진위 결함

| 항목 | 결함 | 영향 |
|---|---|---|
| relevance_score=1.0 literal | 모든 보조금 동일 점수 | HIGH |
| total_potential_amount 산술합 | 한 사업자가 다 받을 수 없음에도 손실액 표기 | HIGH |
| application_url 도메인 단위 | 신청 메뉴 못 찾음 | HIGH |
| eligibility_summary 1줄 | 자격 누락 | HIGH |
| deadline 시드 만료 | author-curated, 갱신 시점 미정 | MEDIUM |
| target_business_types taxonomy | 사용자 "한식" vs 시드 "음식점" → 매칭 실패 다수 | **CRITICAL** |
| source DB 있지만 응답 누락 | INV3 출처 평가 직격 | HIGH |
| business_type Kakao raw 저장 | 정규화 없음, D1 10개 페르소나와 불일치 | **CRITICAL** |

## 2. Coupons 페이지

### 2.1 페르소나
- **C01 시니어**: QR 개념 자체 낯섦. "QR이란?" 도움말 0개. placeholder 없음. 시각적 미리보기 없음. QR 다운로드 버튼 없음 — 인쇄/POS 부착 동선 부재
- **C02 배달앱 함정**: QR 쿠폰은 매장 손님에만 도달 — 배달 마진 회복 무력. UI에서 한계 설명 없음
- **C09 마케팅 실험족**: A/B 테스트 없음. "30%" vs "5,000원" 비교 분석 화면 없음

### 2.2 투자자
- **INV1**: free tier 월 3개 OK. 단가 9,900원 → 프로 전환 leverage 약함. 결제 모듈 부재 → INV4 탈락
- **INV2**: 카톡 채널 공유 → 매장 QR 보여줌이 정상 흐름. **카톡 공유 버튼·이미지 다운로드 0개**

### 2.3 기술전문가

**TECH1**:
- `coupons.py:65-71` `func.extract("month")` 비효율 → full scan. `created_at >= today.replace(day=1)` 권장
- `_BoundedRateTracker`는 단일 인스턴스 메모리 — uvicorn workers > 1 환경에서 워커별 별도 카운터. Redis 권장
- `await db.flush()` 후 명시적 commit 없음

**TECH4 (가장 큼)**:
- **`scan_coupon`(L119) 인증 불필요** — IP rotation으로 `scan_count` 무한 증가 → **vanity 메트릭 변조 가능**
- 쿠폰 ID UUID v4 OK
- **CreateCouponRequest 검증 부재** (`schemas/coupon.py:7-12`):
  - `discount_value: Optional[int]` — 음수, 0, 1000% 통과
  - `valid_days: int = 7` — 99999 통과 (50년)
  - `title`, `description` `max_length` 없음 — XSS payload 1MB 통과
  - `discount_type` enum 검증 없음 — 임의 문자열
- `app_url = "https://ai-coach.vercel.app"` (`coupon_service.py:29`) **하드코딩** — CLAUDE.md 3.2 위반

**TECH5**:
- QR 80×80px (page.tsx:103) — 매장 손님 폰 카메라 인식하기 작음. "큰 QR 보기" 모달 없음
- 미리보기 0개

### 2.4 데이터 진위
100% REAL DB. 다만 **`scan_count`는 인증 없는 IP rate-limited POST에 의존 → 변조 가능**.

## 3. Offline 페이지 + sw.js

### 3.1 페이지 존재
- `frontend/src/app/offline/` 디렉토리 **존재 X**. Next.js 라우트 부재
- `frontend/public/offline.html` 33줄 정적 ("인터넷 연결이 필요합니다", 다시 시도)

### 3.2 페르소나
- 시나리오 현실적 — C12 (지하상가), C14 (지하 호프), C05 (시장 안)
- 그러나 generic — 직전 캐시 데이터 활용 0%. graceful degradation 부재

### 3.3 TECH2 — 🔴 CRITICAL

**`sw 2.js` / `sw 3.js` 즉시 삭제 대상**:
- TECH2 1초 안에 지적
- macOS Finder가 동일 파일명 충돌 시 자동 생성한 중복본
- **더 심각**: 현재 `sw.js`(L1)의 precache 목록에 `{url:"/sw 2.js"}`, `{url:"/sw 3.js"}`가 **그대로 등재** → **사용자 브라우저가 다운로드하고 캐시**. 보안 유출 + 캐시 낭비

**API 캐시 정책**:
- `apis` 캐시 (`/api/`, NetworkFirst, timeout 10s) — `/api/auth/`만 제외
- `/subsidies/matches`, `/dashboard`, `/insights/*` 모두 공유 캐시 — **사용자 A 응답이 캐시 → 사용자 B가 같은 디바이스 로그인 시 노출** OWASP A01

**iOS Safari PWA 제약**:
- `manifest.json` `start_url=/dashboard` — 미인증 시 redirect 후 PWA splash 폭망
- `apple-touch-icon` manifest에 없고 layout.tsx도 미설정 — generic 아이콘

**🔴 Icon 부재**:
- manifest는 `/icons/icon-192x192.png`, `/icons/icon-512x512.png` 참조
- `frontend/public/icons/` **디렉토리 자체 없음**
- 안드로이드 PWA 설치 시 manifest validation 실패
- iOS는 generic Safari 아이콘 fallback
- **데모데이 INV5 시연 시 첫인상 폭망**

**navigation fallback 부재**:
- next-pwa `fallbacks.document` 미설정
- 오프라인 navigation 시 generic 브라우저 오프라인 페이지 (Chrome dino)

## 4. 종합 P0 우선순위

| 순위 | 영역 | 이슈 | 영향 | 수정 |
|---|---|---|---|---|
| **P0-1** | Subsidies | business_type taxonomy 불일치 (Kakao raw vs seed "음식점") | 페르소나 ~140명 매칭 실패 | onboarding canonical taxonomy 매핑 (D1 10종) + seed 정규화 |
| **P0-2** | Subsidies | relevance_score=1.0 literal + ChromaDB dead code | 모든 매칭 무차별 | active path를 search_subsidies로 전환 또는 SQL+의미 부여 |
| **P0-3** | Subsidies | total_potential_amount 산술합 손실 과대표시 | INV2/INV3 신뢰 붕괴 | top-3 매칭만 + UI "추정 합계 (중복 신청 시 일부 제한)" |
| **P0-4** | sw.js | sw 2.js/sw 3.js 사용자 브라우저로 배포 중 | 보안 유출 + TECH2 즉시 탈락 | `git rm` + .gitignore 패턴 + 다음 빌드 |
| **P0-5** | PWA | /icons/icon-*.png 파일 부재 | PWA 설치 실패, 데모 첫인상 폭망 | 192/512 PNG 생성 + frontend/public/icons/ |
| **P0-6** | apply-draft | rate limit + plan_tier 검사 0 → GPT 비용 폭주 | INV1 LTV/CAC 탈락 | coupons 패턴 차용 |
| **P0-7** | Subsidies | application_url 도메인 단위, 신청 직링크 아님 | INV3 탈락 + 사장 헤맴 | 시드 22건 신청 URL 검증 + source 필드 응답·UI 노출 |
| **P0-8** | Subsidies | eligibility_summary 1줄, 자격 누락 | C06 신뢰 붕괴 | eligibility_detail 5~7개 bullet |
| **P1-9** | Coupons | CreateCouponRequest 검증 0 (음수, 50년, 1MB) | TECH4 즉시 지적 | Pydantic Field 검증 |
| **P1-10** | Coupons | scan_count 인증 없이 변조 가능 | INV1 retention 메트릭 신뢰성 0 | 디바이스 fingerprint dedup 또는 hCaptcha |
| **P1-11** | Subsidies | for-loop social_proof N+1 | top-10 시 RTT 10× | 단일 GROUP BY |
| **P1-12** | Subsidies UI | 카피, 매칭사유 칩, D-day 차등 색상, ARIA, 시니어 모드 | TECH5 종합 | composite_score + eligibility_match_reasons[] 응답 추가 |
| **P1-13** | sw.js | apis 캐시 user 분리 0 → 디바이스 공유 시 응답 노출 | OWASP A01 | NetworkFirst 캐시 키에 user_id |
| **P1-14** | Offline | offline.html generic, 직전 캐시 활용 0 | C12/C14 무력 | next-pwa fallbacks.document + SWR fallback |
| P2-15 | Subsidies | UI 필터·정렬·페이지네이션 0 | C16 즉시 이탈 | 다음 라운드 |
| P2-16 | Subsidies | 사업계획서 모달 close 12pt, GPT-4o 노출 | TECH5 톤 | "AI가 작성 중" + 44pt close |

## 핵심 메시지

이 3개 페이지 중 **Subsidies가 가장 위험**. 손실 프레이밍 핵심 카드인데 시드 22건이 hand-typed이고 taxonomy 불일치로 페르소나의 절반 이상이 매칭 0건 또는 부정확. INV3는 출처 표기 부재 + 정보 오래됨 두 축에서 탈락. **RAG라고 부르고 있지만 active path는 dead code** (DATA-AUTHENTICITY 재확인). ChromaDB 인덱싱은 시드 시간만 잡아먹는 의식 행위.

Coupons는 코드는 깔끔하지만 **CreateCouponRequest 검증 부재** TECH4 즉시 지적. **scan_count 변조 가능성**으로 retention 측정 신뢰성 손상.

Offline은 정적 HTML 1개 minimal — graceful degradation 0%. **sw 2.js/sw 3.js가 실제 배포 중** 가장 시급. macOS Finder 부산물이 사용자에게 노출.

**가장 시급한 단일 픽스**: business_type taxonomy 정규화. 다른 모든 매칭·ICP·apply-draft 정확도가 이 위에 서 있다.
