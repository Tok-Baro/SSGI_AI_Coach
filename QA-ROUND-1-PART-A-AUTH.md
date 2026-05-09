# QA Round 1 — Part A: Auth Flow

## 1. Landing 페이지 (`frontend/src/app/page.tsx`)

### Lens A — 페르소나 클러스터

**C01 디지털절벽 노포 (P031–P055, P001/P010/P017/P020):** 기본 버튼 `py-4` + `font-semibold`로 충분히 큼. 그러나 `text-xs text-gray-400`(L75) "카카오 로그인 + 상호명 입력 = 15초" 안내는 50–60대 사장님이 못 읽음 (강유나 가이드라인: 본문 16px, 시니어 18px 위반). "AI 경영코치" 외래어 헤더는 P001 60대 백반집 사장 시야에 추상적. **통과는 되지만 가치 인지 약함.**

**C03 1년차 카페 (P081–P100, P002):** 30–40대 + SNS. "사장님이 모르고 놓치는 돈" 카피 즉각 작동. ValueCard 손실 프레이밍 ("놓치면 내년까지 없어요" 등) ADR 001 정신 부합. **통과.**

**C08 폐업 임박 (P171–P185, P007/P020):** 즉시 가치 보여주지 못하면 이탈. 로컬화된 숫자 (예: "관악구에서 평균 480만원 놓치고 있어요") 부재. **통과는 됨, 그러나 확신 부족.**

**C16 데이터 능숙 사장 (P291–P300):** 카드 직관, 카카오 1탭 OK. 그러나 데이터 출처 텍스트 0건 (정희경 평가관 기준). **부분 통과.**

### Lens B — 투자자 5명
- **INV1 김도윤 (Series A): 조건부 합격.** funnel 깔끔, but landing에 retention 신호 없음.
- **INV2 박순자 (엔젤+자영업): 합격.** 노란 카카오버튼 + "15초"는 50–60대 친화적.
- **INV3 정희경 (서울시 평가관): 조건부.** "유동인구 기반 이벤트" 시사하나 명시적 출처 0건.
- **INV4 이재훈 (AC PM): 합격.** 폼 0개, OAuth 1탭, 30초 가치 잠재력 높음.
- **INV5 한지원 (CVC): 합격.** Kakao 색상 #FEE500, 단일 OAuth.

### Lens C — 기술전문가
| 체크포인트 | 결과 |
|---|---|
| TECH2 Server vs Client | **F**: L1 `"use client"` 강제 — landing은 정적이므로 SSR 가능 (SEO 손실) |
| TECH2 sw.js 중복 | **F**: `sw 2.js`/`sw 3.js` macOS Finder duplicate. 즉시 삭제 |
| TECH4 **OAuth state CSRF** | **F (P0)**: L7 `KAKAO_AUTH_URL`에 `state` 파라미터 없음. OWASP A01 |
| TECH5 한글 가독성 | **F**: L75 `text-xs text-gray-400` 시니어 가독성 위반 |
| TECH5 터치 타겟 | **P** (`py-4` ≈ 56px) |

### 발견 이슈 (Landing)
- **P0**: OAuth `state` 파라미터 누락 (`page.tsx:7`)
- **P1**: `text-xs text-gray-400` (L75) 시니어 가독성
- **P2**: 중복 sw 파일
- **P2**: 가치 카드에 로컬화 숫자/근거 0건 (INV3 감점)

---

## 2. Kakao Callback (`frontend/src/app/auth/kakao/callback/page.tsx`)

### Lens A — 페르소나 클러스터

**C01 디지털절벽 노포:** 백엔드 0.25s end-to-end (PRIORITY-VERIFY.md 확인). spinner + "로그인 중..." (L52–55) 단순. 에러 시 `text-red-500` 빨강만 노출, 한국어 행동 가이드 부재. **부분 통과.**

**C03 1년차 카페:** 0.25s 통과. **통과.**

**C08 폐업 임박:** 인증 빈도 낮고 빠르게 통과. **통과.**

### Lens B — 투자자
- **INV1: 합격** — 24s → 0.25s는 retention 핵심. 단, 에러 시 alternative path (이메일/SMS fallback) 0건.
- **INV2: 합격** — 0.25s면 60대 사장 의심 안 함.
- **INV3, INV4, INV5: 합격.**

### Lens C — 기술전문가
| 체크포인트 | 결과 |
|---|---|
| TECH2 useSearchParams Suspense | **P**: L60–71 정확 적용 |
| TECH2 401 인터셉터 | **P**: `lib/api.ts:108-132` |
| TECH2 StrictMode 가드 | **P**: L14 `handledRef.current` |
| TECH4 **OAuth state CSRF** | **F (P0)**: L18 state 검증 없음 (랜딩과 일관, 둘 다 누락) |
| TECH4 **refresh token rotation** | **F (P1)**: `auth.py:117–135` 새 refresh 발급하나 **이전 무효화 없음**. 30일간 사용 가능 |
| TECH4 Rate limit | **P**: `auth.py:31–52` `_AuthRateTracker` IP당 1분 10회 |
| TECH4 PII 로깅 | **F (P2)**: `auth.py:64,72,78,86` INFO 로깅. DEBUG로 강등 권장 |
| TECH4 kakao token 평문 | **P**: `encrypt_token()` 적용 |
| TECH5 에러 상태 | **부분 P**: `err.message` 영문 그대로 노출 가능 |
| TECH5 접근성 | **F**: spinner `aria-label` 없음, 에러 `role="alert"` 없음 |

### 발견 이슈 (Callback)
- **P0**: OAuth state 미검증 (랜딩과 일관)
- **P1**: refresh token rotation 시 구 토큰 무효화 부재
- **P1**: 에러 화면에 SMS/이메일/문의 fallback 0건
- **P2**: 접근성 aria-label 누락
- **P2**: INFO 로그 → DEBUG 강등

---

## 3. Onboarding (`frontend/src/app/onboarding/page.tsx`)

### Lens A — 페르소나 클러스터

**C01 디지털절벽 노포 (P031–P055):** **심각한 막힘.**
1. Step1 사업자번호 10자리 — 60대 사장님이 사업자증 갖고 있다고 가정 어려움. 카메라 OCR 0건. P010 광장시장 한복점 60대 → 막힘.
2. Step2 카카오 검색 카테고리명 `text-xs text-gray-400` (L194) 시니어 비가독.
3. Step3 `<input type="date">` 캘린더 위젯 50–60대 조작 어려움. "선택"이라 회피 가능.
4. **Step indicator 0건** — 진행률 표시 없음. 강유나 (8) "온보딩 단계 ≤ 5, 진행률 표시" 위반. **25명 중 절반 이상 이탈 추정.**

**C03 1년차 카페 (P081–P100):** Step1~3 모두 통과. **통과.**

**C06 가족경영 마이크로:** 가족 운영 → 사업자번호 모르는 fallback path 없음. **부분 통과.**

**C08 폐업 임박 (P171–P185):** Step3 `loading` 화면 무한정 길어질 위험. PRIORITY-VERIFY.md `onboarding.py:124+` 여전히 anti-pattern: `Depends(get_db)` + Seoul gather + RAG + ActionGenerator → DB 세션 fanout 내내 점유. **취약.**

**C16 데이터 능숙:** OCR 부재, API 노출 없음, 데이터 출처 표기 0건. **부분 통과.**

### Lens B — 투자자
- **INV1: 조건부**. 단계 3개 + verification 1 = 4 — "5필드 미만" 만족. measurable conversion event(GA4) 0건.
- **INV2: 탈락 위험**. **60대 사장 3분 내 가입 가능?** 의심 — stepper 부재 + date picker + 행정 용어. "사업자 검증이 완료되지 않았거나 검증 유효시간(10분)이 초과되었습니다" 추상적.
- **INV3: 합격**. NTS + 카카오 로컬 + 서울시 3종 API gather. 단, 서울시 응답 `Exception` silent skip — fallback 표시 필요.
- **INV4: 합격**. funnel 단순.
- **INV5: 합격**. 카카오 로컬 검색 깊이.

### Lens C — 기술전문가
| 체크포인트 | 결과 |
|---|---|
| TECH1 async 일관성 | **P**: `asyncio.gather` 적용 |
| TECH1 DB 세션 anti-pattern | **F (P1)**: `/complete`가 fanout 내내 세션 점유 |
| TECH1 NTS retry+timeout | **P**: `@retry_async(max_retries=2, delay=1.0)` + `timeout=10.0` |
| TECH1 Pydantic v2 | **P**: 위경도 범위 검증 (33–39, 124–132) |
| TECH2 Zustand persist | **P**: `partialize: user만` |
| TECH4 **`/onboarding/*` IP rate limit** | **F (P1)**: user-level `MAX_ONBOARDING_ATTEMPTS=10`만. IP당 brute force 가능 |
| TECH4 검증 토큰 HMAC | **P**: HMAC-SHA256 + TTL 10분 + user_id 바인딩 |
| TECH5 한글 가독성 | **F**: L194 `text-xs text-gray-400` |
| TECH5 마이크로카피 | **부분 F**: "휴업자/계속사업자" 행정 용어 |
| TECH5 빈 상태 | **F**: 검색 결과 0건 시 메시지 부재 |
| TECH5 **stepper 진행률** | **F (P0)**: 시각적 진행률 표시 0건 |
| TECH5 접근성 | **F**: `<input type="date">` aria-label 없음 |

### 발견 이슈 (Onboarding)
- **P0**: 진행률(stepper) 표시 부재 (C01 + INV2 critical)
- **P1**: `/onboarding/*` IP rate limit 부재
- **P1**: `/complete` DB 세션 fanout 점유 (PRIORITY-VERIFY.md 1순위와 일치)
- **P2**: 검색 결과 빈 상태 UI 없음
- **P2**: 시니어 가독성 (L194)
- **P2**: NTS 사업자 상태 한국어 톤 다운

---

## Auth Flow 종합

### 가장 심각한 이슈 5건

1. **OAuth `state` 파라미터 부재 (CSRF)** — `page.tsx:7` + `callback/page.tsx:18`. 모든 페르소나 영향, INV3 OWASP 감점. **수정**: landing에서 `crypto.randomUUID()` state 발급 → `sessionStorage` 저장 → callback에서 일치 검증.

2. **온보딩 진행률 stepper 부재** — `onboarding/page.tsx:140-142` 헤더에 단계 표시 없음. C01·C05·C08 + INV2 박순자 직격. **수정**: `1/3 → 2/3 → 3/3` 시각 stepper.

3. **`/onboarding/complete` DB 세션 fanout 점유** — `onboarding.py:124-236` `Depends(get_db)` + Seoul gather + RAG + ActionGenerator 동일 세션. C08 spinner 이탈. PRIORITY-VERIFY.md "다음 픽스 1순위"와 일치. **수정**: `dashboard.py` Phase A/B/C 패턴 적용.

4. **`/onboarding/*` IP rate limit 없음** — `auth.py:_AuthRateTracker`가 onboarding엔 미적용. NTS API 비용/할당량 brute force 위험. **수정**: 동일 패턴을 onboarding 라우터 의존성으로 적용.

5. **Refresh token rotation 시 구 토큰 무효화 부재** — `auth.py:117-135`. blacklist/rotation 카운터 없음. 30일 유출 시 끝까지 유효. OWASP A02 위반. **수정**: `User` 모델에 `token_version` 컬럼, 회전마다 증가, 구 토큰 거부.

### 페이지별 verdict
| 페이지 | INV pass | TECH pass | 핵심 결함 |
|---|---|---|---|
| Landing | 4/5 (INV1 조건부) | 보안 1건 P0 | CSRF, 시니어 가독성 |
| Callback | 5/5 | Suspense OK, refresh rotation P1 | 에러 fallback 부족 |
| Onboarding | 4/5 (INV2 탈락 위험) | TECH5 다수 F | stepper 부재, fanout 점유 |
