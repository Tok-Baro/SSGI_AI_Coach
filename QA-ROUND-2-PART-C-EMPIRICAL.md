# QA Round 2 — Part C: 실증 재검증 (14 P0 코드 레벨)

검증일: 2026-05-07. 14건 모두 코드 grep으로 직접 확인. 결과: 13 진짜 / 1 P1 격하

## P0별 검증 결과 요약

| P0 # | 이슈 | 검증 | 영향도 | 난이도 | 즉시 픽스? |
|---|---|---|---|---|---|
| 1 | 47% 하드코딩 | ✅ 진짜 | High (모든 cold-start 노출) | S | YES |
| 2 | GPT 환각 숫자 (no formula) | ✅ 진짜 | Critical | M (구조 변경) | YES |
| 3 | business_type taxonomy 불일치 | ✅ 진짜 | High (보조금 매칭 손실) | M | YES (1 매핑) |
| 4 | ChromaDB dead code | ⚠️ 부분 | Medium → **P1 격하** | M | NO |
| 5 | /icons/icon-*.png 부재 | ✅ 진짜 | Medium (PWA UX) | S | YES |
| 6 | sw 2.js/sw 3.js precache 등재 | ✅ 진짜 | Medium (충돌 캐싱) | S | YES |
| 7 | /api/* 캐시 user 분리 0 | ✅ 진짜 | High (cross-user PII 노출) | S | YES (캐시 OFF) |
| 8 | scan_coupon 인증 없음 | ✅ 진짜 | High (스캔 통계 변조) | M (HMAC) | YES |
| 9 | 시니어 폰트 12pt 미만 다수 | ✅ 진짜 (192건) | High (시니어 핵심) | M (일괄 치환) | YES |
| 10 | OAuth state 부재 | ✅ 진짜 | High (CSRF) | S | YES |
| 11 | DB 세션 점유 (4 라우트) | ✅ 진짜 | Critical (DB 풀 고갈) | L (4 라우터) | YES |
| 12 | today_action silent fallback | ✅ 진짜 | Medium | S | YES |
| 13 | quarterly_change_percent 명칭 오류 | ✅ 진짜 | **Critical (잘못된 risk_score)** | L (시계열 fetch) | YES |
| 14 | CreateCouponRequest 검증 부재 | ✅ 진짜 | High (DoS/요금제 우회) | S | YES |

## P0-1: 47% 하드코딩 — 진짜 ✅

`backend/app/services/social_proof_service.py:48,54`:
```python
# L47-48 (subsidy_proof, cold-start branch)
if count < K_THRESHOLD:
    return f"2025년 {dong_name} 소상공인 47%가 디지털전환 지원금을 수혜했습니다."

# L52-54 (_cold_start_message)
def _cold_start_message(self, dong_name: str, business_type: str) -> str:
    return f"2025년 {dong_name} {business_type} 47%가 디지털전환 지원금을 수혜했습니다."
```
K_THRESHOLD=10이라 MVP/베타 시점 사실상 모든 사용자 노출. dashboard/page.tsx:511 렌더링 직접 확인.

**Patch**: `_cold_start_message`에서 None 반환, UI는 falsy 시 카드 숨김.

## P0-2: GPT 환각 숫자 — 진짜 ✅

`insights.py:933, 968-985`:
```python
"fit_score": <0~100 적합도>,
"expected_roi_pct": <100=손익분기>,
"expected_attach_rate_pct": <도입 시 부착률 0~100>,
"expected_avg_uplift_won": <add_price × attach_rate / 100 정수>,
```

공식 0건. "0~100" 제약만. GPT가 적당한 숫자 채움. L1032-1037 "할루시네이션 방지" 섹션과 모순.

**Patch**: 백엔드에서 결정론적 계산 → GPT는 prose만 작성:
```python
def _compute_revenue_uplift(sales_detail, benchmark) -> dict:
    cur = (sales_detail or {}).get("avg_ticket_price", 0)
    target = (benchmark or {}).get("seoul_avg_ticket", cur)
    gap = max(0, int(target * 0.85 - cur))
    monthly_orders = int((sales_detail or {}).get("monthly_orders_estimate", 0) or 0)
    return {
        "current_avg_ticket": cur,
        "target_avg_ticket": int(target * 0.85),
        "gap_per_order": gap,
        "monthly_orders_estimate": monthly_orders,
        "monthly_uplift_potential_won": gap * monthly_orders,
    }
```

## P0-3: business_type taxonomy — 진짜 ✅

시드 (`seed_subsidies.py`): 음식점, 카페, 소매업, 미용실 등.
프런트 (`onboarding/page.tsx:87-89`):
```ts
const categories = selectedBusiness.category_name.split(" > ");
const businessType = categories.length >= 2 ? categories[1] : categories[0];
```
카카오 응답: "음식점 > 한식 > 백반·정식" → categories[1]="한식". 시드의 어떤 target_business_types에도 없음.

매칭 (`rag_service.py:125-128`):
```python
or_(
    Subsidy.target_business_types.any("전 업종"),
    Subsidy.target_business_types.any(business_type) if business_type else False,
),
```
한식/치킨/분식 사용자는 "전 업종" 9건만 매칭. 13건 미스.

**Patch**: `TAXONOMY_MAP` 1 모듈:
```ts
const TAXONOMY_MAP: Record<string, string> = {
  "한식": "음식점", "양식": "음식점", "일식": "음식점", "중식": "음식점",
  "치킨": "음식점", "분식": "음식점",
  "카페": "카페", "디저트": "카페", "베이커리": "카페",
  "편의점": "소매업", "마트": "소매업", "의류": "소매업",
  "미용실": "미용실", "네일": "미용실",
};
const subType = categories[1] || categories[0];
const businessType = TAXONOMY_MAP[subType] || subType;
```

## P0-4: ChromaDB dead code — 부분 ⚠️ → P1 격하

active path (`search_subsidies_filtered`)는 ChromaDB 호출 0회. relevance_score=1.0 literal.

그러나 legacy `search_subsidies`는 여전히 호출됨:
- `voice.py:54: rag.search_subsidies(...)`
- `daily_action_batch.py:63: rag.search_subsidies(...)`

→ 완전 dead 아님, 메인 사용자 경로에서만 0회. 운영 비용 이슈.

**격하 사유**: 사용자 경험 직접 손실 없음, "RAG 매칭" 마케팅 메시지 vs 실제 동작 괴리만 — 데모 시 'RAG?' 질문 답 못함.

## P0-5: PWA 아이콘 부재 — 진짜 ✅

`frontend/public/icons/` 디렉토리 자체 부재. manifest.json 192/512 PNG 참조 — 모두 404.

**Patch**: 192/512 PNG 추가 또는 manifest 임시 svg fallback.

## P0-6: sw 2.js/3.js precache — 진짜 ✅

`frontend/public/sw.js:1` precacheAndRoute 배열 내부:
```js
{url:"/sw 2.js",revision:"724d5b60dc75fe0cb87a117a4d1decd1"},
{url:"/sw 3.js",revision:"3bcf010fa97910c334a7d6116122c0df"},
```
실제 파일 존재 (git status untracked). next-pwa 빌드가 public/ 전체를 스캔해 포함시킴.

**Patch**:
```bash
rm "frontend/public/sw 2.js" "frontend/public/sw 3.js"
echo 'public/sw [0-9]*.js' >> frontend/.gitignore
# next.config.js: withPWA({ buildExcludes: [/sw\s\d+\.js$/] })
```

## P0-7: /api/* 캐시 user 분리 0 — 진짜 ✅

`sw.js:1` registerRoute:
```js
new e.NetworkFirst({
  cacheName:"apis",
  networkTimeoutSeconds:10,
  plugins:[new e.ExpirationPlugin({maxEntries:16,maxAgeSeconds:86400})]
}),
```
캐시 키 URL만. user A 응답 캐시 → user B 같은 디바이스 로그인 시 노출. JWT를 캐시 키에 미포함.

**Patch (간단)**: /api/* 캐시 OFF
```js
e.registerRoute(({url}) => url.pathname.startsWith("/api/"), new e.NetworkOnly(), "GET");
```

## P0-8: scan_coupon 인증 없음 — 진짜 ✅

`coupons.py:119-140`: `Depends(get_current_user)` 부재. IP rate limit만 (`_BoundedRateTracker` IP+coupon_id당 1분 5회).

IPv6/proxy 사용 시 우회 쉬움. 사장님 대시보드 "스캔 누적" 통계 신뢰 불가.

**Patch**: HMAC 서명 토큰
```python
def _scan_signature(coupon_id: UUID) -> str:
    return hmac.new(settings.scan_secret.encode(), str(coupon_id).encode(), hashlib.sha256).hexdigest()[:16]

@router.post("/{coupon_id}/scan")
async def scan_coupon(coupon_id: UUID, sig: str, ...):
    if not hmac.compare_digest(sig, _scan_signature(coupon_id)):
        raise HTTPException(403, "유효하지 않은 스캔 토큰")
```

## P0-9: 시니어 폰트 12pt 미만 — 진짜 ✅ (192건)

| 파일 | text-xs/text-[8/10/11px] occurrence |
|---|---|
| dashboard/page.tsx | 49 |
| insights/page.tsx | 136 |
| subsidies/page.tsx | 7 |

샘플:
- L233 dashboard: `text-[10px] text-yellow-600` "매일 오전 7시 자동 생성"
- L267: "다음 후보"
- L536: 숫자 표시
- L651: 라벨

text-xs=12px (Tailwind), text-[10px]=10px. 50대 사장 사실상 판독 불가.

**Patch**: tailwind.config.ts text-xs 14px 재정의 + 시니어 모드 토글
```ts
fontSize: {
  'sr-xs': ['14px', '20px'],
  'sr-sm': ['16px', '24px'],
  'sr-base': ['18px', '28px'],
}
```
또는 globals.css `html { font-size: 18px; }`.

## P0-10: OAuth state 부재 — 진짜 ✅

`page.tsx:7`:
```ts
const KAKAO_AUTH_URL = `https://kauth.kakao.com/oauth/authorize?client_id=${...}&redirect_uri=${...}&response_type=code&scope=...`;
```
state 파라미터 누락. CSRF 방어 0.

`callback/page.tsx:18-23`: code만 검증, state 검증 없음. RFC 6749 Section 10.12 "SHOULD use" 위반.

**Patch**:
```ts
function buildKakaoUrl() {
  const state = crypto.randomUUID();
  sessionStorage.setItem("oauth_state", state);
  const params = new URLSearchParams({...all_existing, state});
  return `https://kauth.kakao.com/oauth/authorize?${params.toString()}`;
}
// callback:
const expected = sessionStorage.getItem("oauth_state");
if (state !== expected) { setError("CSRF 검증 실패"); return; }
```

## P0-11: DB 세션 점유 4 라우트 — 진짜 ✅

`/competition`만 phased 패턴 (L91-198). 나머지:
- `/deep-report` (L201-205): `Depends(get_db)` + 14개 외부 API gather + GPT
- `/marketing` (L716-755): `Depends(get_db)` + 8개 + sequential get_sales_detail + GPT
- `/menu-strategy` (L1086-1125): `Depends(get_db)` + 5개 + GPT
- `/onboarding/complete` (L184-224): `Depends(get_db)` + 3개 Seoul + RAG + ActionGenerator

PG 풀 한도 10~20 → 동시 사용자 N명에서 즉시 고갈.

**Patch**: dashboard.py phased 패턴 복붙
```python
@router.get("/marketing")
async def get_marketing_strategy(refresh, current_user):  # ← db 제거
    if not refresh:
        async with async_session_factory() as db:
            cached = await _get_cached(db, current_user.id, "marketing")
        if cached: return cached
    
    async with async_session_factory() as db:
        subsidies = await rag.search_subsidies_filtered(db=db, ...)
    
    # Phase B: 외부 API gather (DB 점유 없음)
    (sales, ...) = await asyncio.gather(...)
    
    # Phase A2: 캐시 + 통계
    async with async_session_factory() as db:
        await _set_cache(db, current_user.id, "marketing", result)
        await db.commit()
    return result
```

## P0-12: today_action silent fallback — 진짜 ✅

`action_generator.py:148-150`:
```python
except Exception as e:
    logger.error(f"GPT-4o daily action failed: {e}")
    return self._fallback_action(subsidy_data, population_data, events_data)
```

`_fallback_action` (L152-189): `risk_score=0.7` 임의 고정값. `is_fallback` 플래그 없음. UI에 GPT 결과와 동일 카드.

**Patch**:
```python
def _fallback_action(self, ...) -> dict:
    base = {"is_fallback": True, "fallback_reason": "GPT API unavailable"}
    if subsidy_data:
        return {**base, "action_type": "subsidy", ...}

# UI dashboard/page.tsx:
{data.today_action.is_fallback && (
  <span className="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded">
    AI 일시 미동작 — 기본 안내
  </span>
)}
```

## P0-13: quarterly_change_percent 명칭 오류 — 진짜 ✅ **Critical**

`seoul_api_service.py:147-156`:
```python
sales_list = sorted([float(r.get("THSMON_SELNG_AMT", 0)) for r in matched])
median = sales_list[len(sales_list) // 2] if sales_list else 0
change = ((avg_area_sales - median) / median * 100) if median > 0 else 0
return {
    ...
    "quarterly_change_percent": round(change, 1),
    ...
}
```

이 값은 **현재 분기 안의 (평균 - 중앙값) / 중앙값** = 분포 비대칭/dispersion 지표. **시계열 변화율 아님**.

소비처 `risk_score_engine.py:108-118`:
```python
if sales_data and sales_data.get("quarterly_change_percent") is not None:
    change = sales_data["quarterly_change_percent"]
    score = _clamp(0.5 - (change / 20.0 * 0.5))
    desc = f"전분기 대비 {change:+.1f}%"  # ← 거짓!
```

label "매출 트렌드", description "전분기 대비 X%" — 모두 시계열을 시사하지만 데이터는 dispersion. 부호 의미도 망가짐 (롱테일 분포에서 평균 > 중앙값은 흔함, 위험 신호 아님).

**Patch**: 진짜 QoQ를 위해 이전 분기 데이터 별도 fetch
```python
async def get_commercial_sales(self, gu, dong, btype):
    cur_q = await self._fetch_sales_for_period(gu, dong, btype, "current")
    prev_q = await self._fetch_sales_for_period(gu, dong, btype, "previous")
    cur_total = sum(...)
    prev_total = sum(...)
    qoq = ((cur_total - prev_total) / prev_total * 100) if prev_total > 0 else 0
    
    return {
        "quarterly_change_percent": round(qoq, 1),  # 진짜 QoQ
        "area_dispersion_percent": round(dispersion_pct, 1),  # 분포 정보 분리
        ...
    }
```

이전 분기 데이터 못 가져오면 None → risk_score_engine "데이터 없음" 분기.

## P0-14: CreateCouponRequest 검증 부재 — 진짜 ✅

`schemas/coupon.py:7-12`:
```python
class CreateCouponRequest(BaseModel):
    title: str
    discount_type: str
    discount_value: Optional[int] = None
    description: Optional[str] = None
    valid_days: int = 7
```

Field constraint 0건. 시뮬:
- `title="A" * 1_000_000` 통과 (PG TEXT 1GB)
- `discount_type="DROP TABLE coupons;"` 통과
- `discount_value=-99999999` 통과
- `valid_days=99999` 통과 → 273년 유효
- `valid_days=-1` 통과 → valid_until < valid_from

**Patch**:
```python
from typing import Literal
from pydantic import BaseModel, Field, field_validator

DiscountType = Literal["percent", "fixed", "bogo", "free_item"]

class CreateCouponRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=50)
    discount_type: DiscountType
    discount_value: Optional[int] = Field(None, ge=0, le=1_000_000)
    description: Optional[str] = Field(None, max_length=200)
    valid_days: int = Field(7, ge=1, le=365)

    @field_validator("discount_value")
    @classmethod
    def _validate_discount(cls, v, info):
        dtype = info.data.get("discount_type")
        if dtype == "percent" and v is not None and not (1 <= v <= 100):
            raise ValueError("percent 할인은 1~100")
        return v
```

## 종합 진단 — 우선순위

**즉시 (오늘)**: P0-14 (Pydantic 검증, S), P0-7 (sw 캐시 OFF, S), P0-10 (OAuth state, S), P0-1 (47% 메시지, S)

**금주**: P0-3 (taxonomy, M), P0-5 (icons, S), P0-6 (sw 충돌파일, S), P0-12 (fallback flag, S)

**다음 스프린트**: P0-2 (GPT 환각 grounding, M), P0-8 (HMAC 스캔, M), P0-9 (폰트 baseline, M), P0-11 (DB 세션 split, L), P0-13 (시계열 매출, L)

**가장 위험한 두 건**: 
- **P0-13**: 잘못된 risk_score를 모든 인사이트가 사용 중 — 데이터 신뢰성 핵심
- **P0-11**: 부하 테스트 즉시 fail — 데모 시점 critical path
