"""
경영 인사이트 라우터
- GET /insights/competition: 경쟁사 분석 (주간 캐시)
- GET /insights/deep-report: 집중분석 리포트 (주간 캐시)
- GET /insights/marketing: 맞춤 마케팅 전략 (주간 캐시)
"""
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from datetime import date, timedelta
from openai import AsyncOpenAI

from app.database import get_db
from app.config import settings
from app.utils.auth import get_current_user
from app.models import User, DailyAction, CouponTemplate, InsightCache
from app.services.seoul_api_service import SeoulAPIService
from app.services.kakao_service import KakaoService
from app.services.rag_service import RAGService
from app.services.risk_score_engine import RiskScoreEngine
from app.services.weather_service import WeatherService
from app.services.location_analyzer import analyze_location, format_location_analysis
from app.services import marketing_audit

logger = logging.getLogger(__name__)
router = APIRouter()


def _current_week_key() -> str:
    """현재 주차 키 (예: '2026-W15')."""
    return date.today().strftime("%G-W%V")


async def _get_cached(
    db: AsyncSession, user_id, insight_type: str
) -> dict | None:
    """주간 캐시 조회. 같은 주면 캐시 반환."""
    stmt = select(InsightCache).where(
        InsightCache.user_id == user_id,
        InsightCache.insight_type == insight_type,
        InsightCache.week_key == _current_week_key(),
    )
    result = await db.execute(stmt)
    cache = result.scalar_one_or_none()
    return cache.data if cache else None


async def _set_cache(
    db: AsyncSession, user_id, insight_type: str, data: dict
) -> None:
    """주간 캐시 저장 (upsert)."""
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    stmt = pg_insert(InsightCache).values(
        user_id=user_id,
        insight_type=insight_type,
        week_key=_current_week_key(),
        data=data,
    ).on_conflict_do_update(
        constraint="uq_insight_cache_user_type_week",
        set_={"data": data},
    )
    await db.execute(stmt)


@router.get("/competition")
async def get_competition_analysis(
    refresh: bool = Query(False, description="캐시 무시하고 새로 조회"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """경쟁사 분석: 개폐업 + 매출 상세 + 유동인구 + 주변 경쟁가게 (주간 캐시)."""
    if not current_user.onboarding_completed:
        raise HTTPException(status_code=400, detail="온보딩을 먼저 완료해주세요.")

    if not refresh:
        cached = await _get_cached(db, current_user.id, "competition")
        if cached:
            return cached

    seoul = SeoulAPIService()
    kakao = KakaoService()
    weather_svc = WeatherService()

    async def _safe(coro):
        try:
            return await coro
        except Exception:
            return None

    gu = current_user.gu_name or ""
    dong = current_user.dong_name or ""
    btype = current_user.business_type or ""
    search_query = f"{dong or gu} {btype}"

    has_coords = current_user.lat and current_user.lng

    (sales, competition, population, sales_detail,
     floating_pop, change_index, facilities, workplace_pop,
     benchmark, weather, nearby, radius_summary) = await asyncio.gather(
        _safe(seoul.get_commercial_sales(gu, dong, btype)),
        _safe(seoul.get_business_openclose(gu, btype)),
        _safe(seoul.get_living_population(dong, gu)),
        _safe(seoul.get_sales_detail(gu, dong, btype)),
        _safe(seoul.get_commercial_floating_pop(gu, dong, btype)),
        _safe(seoul.get_commercial_change_index(gu, dong)),
        _safe(seoul.get_anchor_facilities(gu, dong)),
        _safe(seoul.get_workplace_population(gu, dong)),
        _safe(seoul.get_benchmark(gu, dong, btype)),
        _safe(weather_svc.get_today_weather(gu)),
        _safe(kakao.search_local(search_query, size=10)),
        _safe(kakao.get_radius_competitor_summary(current_user.lat, current_user.lng)) if has_coords else asyncio.sleep(0),
    )
    if not has_coords:
        radius_summary = None

    # 주변 경쟁가게에서 내 가게 제외
    competitors = []
    if nearby:
        for place in nearby:
            if place.get("place_name") != current_user.business_name:
                competitors.append({
                    "name": place.get("place_name", ""),
                    "address": place.get("road_address_name") or place.get("address_name", ""),
                    "category": place.get("category_name", ""),
                    "phone": place.get("phone", ""),
                    "distance": place.get("distance", ""),
                })

    # 부동산학 입지 분석 산출
    loc_analysis = analyze_location(
        facilities=facilities,
        workplace_pop=workplace_pop,
        floating_pop=floating_pop,
        population_data=population,
        radius_summary=radius_summary,
        sales_data=sales,
        benchmark=benchmark,
        change_index=change_index,
    )

    result = {
        "sales_data": sales,
        "competition_data": competition,
        "population_data": population,
        "sales_detail": sales_detail,
        "floating_population": floating_pop,
        "change_index": change_index,
        "facilities": facilities,
        "workplace_population": workplace_pop,
        "benchmark": benchmark,
        "radius_summary": radius_summary,
        "location_analysis": loc_analysis,
        "weather": weather,
        "nearby_competitors": competitors[:8],
        "business_name": current_user.business_name,
        "business_type": current_user.business_type,
        "location": f"{gu} {dong}".strip(),
    }
    await _set_cache(db, current_user.id, "competition", result)
    return result


@router.get("/deep-report")
async def get_deep_report(
    refresh: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """GPT-4o 기반 집중분석 리포트 (주간 캐시)."""
    if not current_user.onboarding_completed:
        raise HTTPException(status_code=400, detail="온보딩을 먼저 완료해주세요.")

    if not refresh:
        cached = await _get_cached(db, current_user.id, "deep_report")
        if cached:
            return cached

    seoul = SeoulAPIService()
    kakao = KakaoService()
    rag = RAGService()
    weather_svc = WeatherService()

    async def _safe(coro):
        try:
            return await coro
        except Exception:
            return None

    gu = current_user.gu_name or ""
    dong = current_user.dong_name or ""
    btype = current_user.business_type or ""
    search_query = f"{dong or gu} {btype}"

    has_coords = current_user.lat and current_user.lng

    (sales, competition, population, sales_detail,
     floating_pop, change_index, facilities, workplace_pop,
     benchmark, weather, events, subsidies, nearby, radius_summary) = await asyncio.gather(
        _safe(seoul.get_commercial_sales(gu, dong, btype)),
        _safe(seoul.get_business_openclose(gu, btype)),
        _safe(seoul.get_living_population(dong, gu)),
        _safe(seoul.get_sales_detail(gu, dong, btype)),
        _safe(seoul.get_commercial_floating_pop(gu, dong, btype)),
        _safe(seoul.get_commercial_change_index(gu, dong)),
        _safe(seoul.get_anchor_facilities(gu, dong)),
        _safe(seoul.get_workplace_population(gu, dong)),
        _safe(seoul.get_benchmark(gu, dong, btype)),
        _safe(weather_svc.get_today_weather(gu)),
        _safe(seoul.get_cultural_events(gu)),
        _safe(rag.search_subsidies_filtered(
            db=db, gu_name=gu, business_type=btype, top_k=5, user_id=current_user.id,
        )),
        _safe(kakao.search_local(search_query, size=10)),
        _safe(kakao.get_radius_competitor_summary(current_user.lat, current_user.lng)) if has_coords else asyncio.sleep(0),
    )
    if not has_coords:
        radius_summary = None

    # 쿠폰 + 액션 통계
    stmt = select(
        func.count(CouponTemplate.id),
        func.coalesce(func.sum(CouponTemplate.scan_count), 0),
    ).where(CouponTemplate.user_id == current_user.id)
    result = await db.execute(stmt)
    coupon_row = result.one()

    stmt = select(
        func.count(DailyAction.id),
        func.sum(case((DailyAction.is_completed == True, 1), else_=0)),
    ).where(
        DailyAction.user_id == current_user.id,
        DailyAction.date >= date.today() - timedelta(days=30),
    )
    result = await db.execute(stmt)
    action_row = result.one()

    competitor_count = 0
    competitor_names = []
    if nearby:
        for p in nearby:
            if p.get("place_name") != current_user.business_name:
                competitor_count += 1
                competitor_names.append(p.get("place_name", ""))

    # 데이터 요약 텍스트 구성
    sections = []
    sections.append(f"상호: {current_user.business_name}")
    sections.append(f"업종: {current_user.business_type}")
    sections.append(f"위치: {current_user.gu_name or ''} {current_user.dong_name or ''}")

    if sales:
        sections.append(f"\n[매출 분석] {sales.get('area_name', '')} ({sales.get('note', '')})")
        sections.append(f"- 상권 내 동종업종 분기 총매출: {sales.get('area_total_sales', 0):,.0f}원")
        sections.append(f"- 분기 총 거래건수: {sales.get('area_total_count', 0):,.0f}건")
        sections.append(f"- 평균 객단가: {sales.get('avg_ticket_price', 0):,.0f}원")
        sections.append(f"- 전분기 대비 변화: {sales.get('quarterly_change_percent', 0):+.1f}%")
        sections.append(f"- 샘플: {sales.get('sample_count', 0)}개 상권")

    if sales_detail:
        sections.append(f"\n※ 아래 수치는 상권 내 동종업종 매출 비중(%)")

        dow = sales_detail.get("day_of_week", {})
        if dow:
            peak_day = max(dow, key=dow.get)
            low_day = min(dow, key=dow.get)
            sections.append(f"\n[요일별 매출 비중]")
            for d, v in dow.items():
                sections.append(f"- {d}: {v}%")
            sections.append(f"→ 최고: {peak_day}({dow[peak_day]}%), 최저: {low_day}({dow[low_day]}%)")

        tz = sales_detail.get("time_zone", {})
        if tz:
            peak_tz = max(tz, key=tz.get)
            sections.append(f"\n[시간대별 매출 비중]")
            for t, v in tz.items():
                sections.append(f"- {t}시: {v}%")
            sections.append(f"→ 피크: {peak_tz}({tz[peak_tz]}%)")

        gender = sales_detail.get("gender", {})
        if gender:
            sections.append(f"\n[성별 매출 비중]")
            sections.append(f"- 남성: 매출 {gender.get('남성_비중', 0)}%, 건수 {gender.get('남성_건수비중', 0)}%")
            sections.append(f"- 여성: 매출 {gender.get('여성_비중', 0)}%, 건수 {gender.get('여성_건수비중', 0)}%")

        age = sales_detail.get("age_group", {})
        if age:
            peak_age = max(age, key=age.get)
            sections.append(f"\n[연령대별 매출 비중]")
            for a, v in age.items():
                sections.append(f"- {a}: {v}%")
            sections.append(f"→ 핵심 고객층: {peak_age}({age[peak_age]}%)")

        ww = sales_detail.get("weekday_vs_weekend", {})
        if ww:
            sections.append(f"\n[주중/주말] 주중: {ww.get('주중', 0)}%, 주말: {ww.get('주말', 0)}%")

        ticket = sales_detail.get("avg_ticket_price", 0)
        if ticket:
            sections.append(f"[평균 객단가] {ticket:,.0f}원")

    if competition:
        sections.append(f"\n[경쟁 현황] {competition.get('area_name', '')}")
        sections.append(f"- 평균 점포 수: {competition.get('total_stores', 0)}개")
        sections.append(f"- 개업률: {competition.get('opening_rate', 0)}%, 폐업률: {competition.get('closing_rate', 0)}%")

    if competitor_names:
        sections.append(f"\n[주변 경쟁가게] {competitor_count}곳: {', '.join(competitor_names[:5])}")

    if population:
        sections.append(f"\n[유동인구] 전일 대비 {population.get('change_percent', 0):+.1f}%")

    if events:
        sections.append(f"\n[주변 문화행사] {len(events)}건: {', '.join(e.get('title', '')[:20] for e in events[:3])}")

    if subsidies:
        total_amt = sum(s.get("max_amount", 0) or 0 for s in subsidies)
        sections.append(f"\n[매칭 지원사업] {len(subsidies)}건 (최대 {total_amt}만원)")
        for s in subsidies[:3]:
            sections.append(f"- {s.get('title', '')}: 최대 {s.get('max_amount', 0)}만원, 마감 D-{s.get('days_until_deadline', '?')}")

    if change_index:
        sections.append(f"\n[상권변화지표] 판정: {change_index.get('dominant_status', '미분류')}")
        sections.append(f"- 변화지수: {change_index.get('avg_change_index', 0)}")
        sections.append(f"- 월평균 매출: {change_index.get('avg_monthly_sales', 0):,.0f}원")
        dist = change_index.get("status_distribution", {})
        if dist:
            sections.append(f"- 분포: {dist}")

    if floating_pop:
        sections.append(f"\n[상권 유동인구] 총 {floating_pop.get('total', 0):,.0f}명")
        fp_tz = floating_pop.get("time_zone", {})
        if fp_tz:
            peak_tz = max(fp_tz, key=fp_tz.get)
            sections.append(f"- 피크 시간: {peak_tz} ({fp_tz[peak_tz]:,.0f}명)")
        fp_age = floating_pop.get("age_group", {})
        if fp_age:
            peak_age = max(fp_age, key=fp_age.get)
            sections.append(f"- 핵심 연령대: {peak_age} ({fp_age[peak_age]:,.0f}명)")

    if workplace_pop:
        sections.append(f"\n[직장인구] 총 {workplace_pop.get('total', 0):,.0f}명")

    if facilities:
        fac_items = [f"{k} {v}개" for k, v in facilities.items() if k != "sample_count" and v > 0]
        if fac_items:
            sections.append(f"\n[집객시설] {', '.join(fac_items)}")

    if weather:
        sections.append(f"\n[오늘 날씨] {weather.get('sky', '')} {weather.get('temperature', '')}, 강수확률 {weather.get('rain_probability', '0%')}")
        insights = weather.get("insights", [])
        for ins in insights:
            sections.append(f"- {ins}")

    if benchmark:
        sections.append(f"\n[서울 평균 대비 벤치마킹] {benchmark.get('business_type', '')}")
        sections.append(f"- 평균 객단가: 내 지역 {benchmark.get('local_avg_ticket', 0):,.0f}원 vs 서울 평균 {benchmark.get('seoul_avg_ticket', 0):,.0f}원 ({benchmark.get('ticket_diff_pct', 0):+.1f}%)")
        sections.append(f"- 주말 매출 비중: 내 지역 {benchmark.get('local_weekend_ratio', 0):.1f}% vs 서울 {benchmark.get('seoul_weekend_ratio', 0):.1f}%")
        sections.append(f"- 여성 고객 비중: 내 지역 {benchmark.get('local_female_ratio', 0):.1f}% vs 서울 {benchmark.get('seoul_female_ratio', 0):.1f}%")

    if radius_summary:
        items = [f"{k} {v}개" for k, v in radius_summary.items() if v > 0]
        total_nearby = sum(v for v in radius_summary.values())
        sections.append(f"\n[반경 500m 업종 분포] 총 {total_nearby}개: {', '.join(items)}")

    sections.append(f"\n[서비스 활용] 쿠폰 {coupon_row[0]}건 발행/{coupon_row[1]}건 스캔, 액션 {action_row[1] or 0}/{action_row[0] or 0}건 완료")

    # 부동산학 입지 분석
    location_analysis = analyze_location(
        facilities=facilities,
        workplace_pop=workplace_pop,
        floating_pop=floating_pop,
        population_data=population,
        radius_summary=radius_summary,
        sales_data=sales,
        benchmark=benchmark,
        change_index=change_index,
    )
    sections.append(format_location_analysis(location_analysis))

    # 5-차원 자동 진단 + ICP 학습 프로필 → GPT 컨텍스트로 주입
    audit, icp = await _compute_audit_and_icp(
        db, current_user,
        sales_detail=sales_detail,
        competition=competition,
        floating_pop=floating_pop,
        radius_summary=radius_summary,
        nearby=nearby,
        matched_subsidies=subsidies,
    )
    sections.append(_format_audit_for_prompt(audit, icp))

    data_text = "\n".join(sections)

    # GPT-4o 집중분석 리포트
    openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    system_prompt = """당신은 서울시 빅데이터 기반 소상공인 전문 경영 컨설턴트입니다.
서울시 상권분석 알고리즘(상권변화지표, 창업위험도), 유동인구, 매출 트렌드, 경쟁 데이터, 부동산 환경을 종합하여 상세 경영 진단 리포트를 작성합니다.

## 분석 프레임워크
1. **상권 입지 분석**: 상권변화지표(정체/확장/축소/다이나믹), 집객시설, 반경 업체 밀도
2. **고객 분석**: 성별/연령대/시간대별 매출+유동인구 교차 분석, 직장인구 vs 상주인구 비율
3. **경쟁 분석**: 개폐업률, 서울 평균 대비 벤치마킹, 반경 500m 업종 분포
4. **외부 환경**: 날씨, 문화행사, 시즌 트렌드
5. **업종 트렌드**: 해당 업종의 성장/쇠퇴 방향, 소비 트렌드 변화
6. **5-차원 자동 진단** (page-cro 프레임워크): 포지셔닝/메시지/타이밍/사회적 증거/마찰
   → executive_summary와 SWOT, action_items는 진단의 weakest 차원을 우선 다루세요.
7. **사용자 학습 프로필 (ICP)**: 누적 신호로 학습된 선호 기관/금액대/키워드
   → 보조금/마케팅 추천 시 학습된 선호를 우선 반영하세요.

응답 형식 (JSON):
{
  "executive_summary": "3줄 경영 현황 요약 — 반드시 매출/유동인구/경쟁 수치를 인용. 손실 프레이밍 톤.",
  "location_analysis": "상권 입지 종합 분석 (300자) — 직주비율 {X}, 집객력 {X}점, HHI {X}, 상권 생애주기 '{X}'를 교차 분석. 이 입지가 해당 업종에 유리한지/불리한지 구체적으로.",
  "swot": {
    "strengths": ["[근거: 데이터X] 강점 설명 — 3~5개"],
    "weaknesses": ["[근거: 데이터X] 약점 설명 — 3~5개"],
    "opportunities": ["[근거: 데이터X] 기회 요인 — 3~5개"],
    "threats": ["[근거: 데이터X] 위협 요인 — 3~5개"]
  },
  "customer_insight": "핵심 고객 프로필 (300자) — 성별 비중(남X%/여X%), 핵심 연령대({X}대, 매출 {X}원), 피크 시간({X}시, 유동인구 {X}명)을 교차하여 '누가 언제 오는지' 구체적으로. 놓치고 있는 고객층도 분석.",
  "time_strategy": "시간 최적화 전략 (300자) — 요일별 매출 데이터(최고:{X}요일, 최저:{X}요일) + 시간대별 유동인구 피크({X}시)를 근거로. 주중/주말 차별화 전략 구체적으로.",
  "competition_analysis": "경쟁 분석 (300자) — 서울 평균 대비 매출 {X}%, 반경 500m 내 {X}개 업체, 개업률 {X}%/폐업률 {X}%. 차별화 포인트와 방어 전략.",
  "trend_analysis": "업종+상권 트렌드 분석 (300자) — 상권변화지표 '{X}' + 개폐업 데이터 근거. 이 업종이 이 지역에서 성장/쇠퇴 중인지 데이터 기반 판단.",
  "action_items": [
    {"priority": "high|medium|low", "action": "즉시 실행 가능한 행동 (구체적)", "expected_impact": "[근거: 데이터X] 정량적 기대 효과", "timeline": "실행 기간", "cost": "예상 비용"},
    "...최대 7개, 우선순위 순"
  ],
  "risk_alert": "가장 시급한 위험 1가지 — [근거: 수치] + 방치 시 예상 손실",
  "monthly_goal": "이번 달 KPI 3개 (매출 목표, 고객 수 목표, 마케팅 실행 목표 — 모두 정량)"
}

## 할루시네이션 방지 규칙 (절대 준수)
1. 제공된 데이터에 있는 수치만 인용하세요. 없는 데이터를 만들어내면 안 됩니다.
2. "약 ~", "추정 ~"이 아니라 정확한 수치를 쓰세요 (예: "매출 1,050,118,062원", "유동인구 12,345명").
3. 데이터가 없는 항목은 "해당 데이터 미제공"이라고 명시하세요.
4. 업종 트렌드는 제공된 개폐업률/상권변화지표에서만 도출하세요. 인터넷 검색 결과를 쓰지 마세요.
5. 모든 전략은 반드시 "[데이터 근거]" 태그를 붙여주세요.

## 기타 원칙
- 손실 프레이밍: "놓치고 있습니다" 톤
- 업종 특성을 고려한 맞춤 분석
- 한국어, 존댓말"""

    user_prompt = f"""아래는 서울시 빅데이터 플랫폼에서 수집한 소상공인의 실제 경영 데이터입니다.
이 데이터를 전문 경영 컨설턴트 관점에서 종합 분석하여 5만원 가치의 리포트를 JSON으로 작성하세요.

주의사항:
- 아래 데이터에 있는 수치만 인용하세요. 데이터에 없는 내용을 절대 만들어내지 마세요.
- 각 분석에 반드시 [근거: 데이터 항목명과 수치]를 명시하세요.
- "일반적으로~", "보통~" 같은 일반론은 쓰지 마세요. 이 가게의 데이터만 분석하세요.
- 부동산학 입지 분석(직주비율, HHI, 집객력, 상권 생애주기)을 반드시 location_analysis에 반영하세요.

{data_text}"""

    try:
        response = await openai_client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=2048,
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        import json
        report = json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Deep report generation failed: {e}")
        report = {
            "executive_summary": "리포트 생성에 실패했습니다. 다시 시도해주세요.",
            "swot": {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []},
            "customer_insight": "",
            "time_strategy": "",
            "competition_analysis": "",
            "action_items": [],
            "risk_alert": "",
            "monthly_goal": "",
        }

    result = {
        "report": report,
        "data_summary": {
            "sales": sales,
            "competition": competition,
            "population": population,
            "competitor_count": competitor_count,
            "subsidy_count": len(subsidies) if subsidies else 0,
        },
    }
    await _set_cache(db, current_user.id, "deep_report", result)
    return result


async def _compute_audit_and_icp(
    db: AsyncSession,
    user: User,
    *,
    sales_detail: dict | None,
    competition: dict | None,
    floating_pop: dict | None,
    radius_summary: dict | None,
    nearby: list | None,
    matched_subsidies: list | None,
) -> tuple[dict, dict]:
    """집중분석/마케팅에서 공통으로 쓰는 audit + ICP 프로필 계산.

    반환: (audit_dict, icp_profile_dict)
    """
    from app.services.icp_learner import learn_user_profile

    dong = user.dong_name or ""
    btype = user.business_type or ""
    today = date.today()

    # 동네 동종 가입자 수 (k-anonymity)
    stmt = select(func.count(User.id)).where(
        User.dong_name == dong,
        User.business_type == btype,
        User.onboarding_completed == True,
    )
    result = await db.execute(stmt)
    same_dong_count = result.scalar() or 0

    # 쿠폰 (제목 + 스캔)
    stmt = select(CouponTemplate).where(CouponTemplate.user_id == user.id)
    result = await db.execute(stmt)
    coupon_rows = result.scalars().all()
    coupons = [
        {"title": c.title or "", "scan_count": c.scan_count or 0}
        for c in coupon_rows
    ]
    coupon_created = len(coupons)
    coupon_scanned = sum(c["scan_count"] for c in coupons)

    # 액션 30일 통계
    stmt = select(
        func.count(DailyAction.id),
        func.sum(case((DailyAction.is_completed == True, 1), else_=0)),
    ).where(
        DailyAction.user_id == user.id,
        DailyAction.date >= today - timedelta(days=30),
    )
    result = await db.execute(stmt)
    action_row = result.one()
    total_actions = action_row[0] or 0
    completed = action_row[1] or 0
    completion_rate = completed / total_actions if total_actions > 0 else 0.0

    # 미신청 보조금 누적
    pending_amount = sum(
        s.get("max_amount", 0) for s in (matched_subsidies or [])
        if s.get("max_amount")
    )

    # 주변 경쟁 가게 (자기 자신 제외)
    nearby_count = 0
    if nearby:
        nearby_count = sum(
            1 for p in nearby
            if p.get("place_name") != user.business_name
        )

    audit = await marketing_audit.evaluate(
        business_type=btype,
        sales_detail=sales_detail,
        competition_data=competition,
        floating_population=floating_pop,
        radius_summary=radius_summary,
        coupons=coupons,
        coupon_created=coupon_created,
        coupon_scanned=coupon_scanned,
        same_dong_count=same_dong_count,
        nearby_competitors_count=nearby_count,
        action_completion_rate=completion_rate,
        total_actions_30d=total_actions,
        pending_subsidy_amount=pending_amount,
    )

    profile = await learn_user_profile(db, user.id)
    return audit, profile.to_dict()


def _format_audit_for_prompt(audit: dict, icp: dict | None = None) -> str:
    """audit + ICP 결과를 GPT 프롬프트용 텍스트로 포맷."""
    lines = ["\n## 5-차원 자동 진단 (page-cro 프레임워크 적용)"]
    lines.append(
        f"종합 {audit.get('overall_score', 0)}점 / 가장 시급: {audit.get('weakest_label', '')} — {audit.get('weakest_headline', '')}"
    )
    for d in audit.get("dimensions", []):
        lines.append(
            f"- {d['label']} {d['score']}점 [{d['severity']}]: {d.get('insight', '')}"
        )
    lines.append("→ executive_summary, SWOT, action_items 작성 시 이 진단의 weakest 차원을 우선 다루세요.")

    if icp and icp.get("has_signals"):
        lines.append(f"\n## 사용자 학습 프로필 (ICP, 신호 {icp.get('signal_count', 0)}건)")
        orgs = icp.get("preferred_organizations") or []
        if orgs:
            lines.append("- 선호 기관: " + ", ".join(o["name"] for o in orgs[:3]))
        ar = icp.get("amount_range")
        if ar and ar.get("median"):
            lines.append(
                f"- 선호 지원금 규모: 중앙값 {ar['median']:.0f}만원 (범위 {ar.get('min', 0):.0f}~{ar.get('max', 0):.0f})"
            )
        kws = icp.get("top_keywords") or []
        if kws:
            lines.append("- 자주 나타난 키워드: " + ", ".join(k["word"] for k in kws[:6]))
        lines.append("→ 보조금/마케팅 추천 시 이 학습된 선호를 우선 반영하세요.")

    return "\n".join(lines)


@router.get("/marketing")
async def get_marketing_strategy(
    refresh: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """GPT-4o 기반 맞춤 마케팅 전략 (주간 캐시)."""
    if not current_user.onboarding_completed:
        raise HTTPException(status_code=400, detail="온보딩을 먼저 완료해주세요.")

    if not refresh:
        cached = await _get_cached(db, current_user.id, "marketing")
        if cached:
            return cached

    seoul = SeoulAPIService()
    rag = RAGService()
    weather_svc = WeatherService()

    async def _safe(coro):
        try:
            return await coro
        except Exception:
            return None

    gu = current_user.gu_name or ""
    dong = current_user.dong_name or ""
    btype = current_user.business_type or ""

    (sales, competition, population, events, subsidies,
     floating_pop, change_index, weather) = await asyncio.gather(
        _safe(seoul.get_commercial_sales(gu, dong, btype)),
        _safe(seoul.get_business_openclose(gu, btype)),
        _safe(seoul.get_living_population(dong, gu)),
        _safe(seoul.get_cultural_events(gu)),
        _safe(rag.search_subsidies_filtered(
            db=db, gu_name=gu, business_type=btype, top_k=3, user_id=current_user.id,
        )),
        _safe(seoul.get_commercial_floating_pop(gu, dong, btype)),
        _safe(seoul.get_commercial_change_index(gu, dong)),
        _safe(weather_svc.get_today_weather(gu)),
    )

    # 쿠폰 성과
    stmt = select(
        func.count(CouponTemplate.id),
        func.coalesce(func.sum(CouponTemplate.scan_count), 0),
    ).where(CouponTemplate.user_id == current_user.id)
    result = await db.execute(stmt)
    coupon_row = result.one()

    # 데이터 요약
    sales_summary = "데이터 없음"
    if sales:
        change = sales.get("quarterly_change_percent", 0)
        sales_summary = f"전분기 대비 매출 {change:+.1f}% ({sales.get('area_name', '')})"

    competition_summary = "데이터 없음"
    if competition:
        competition_summary = f"같은 업종 점포 {competition.get('total_stores', 0)}개, 개업률 {competition.get('opening_rate', 0)}%, 폐업률 {competition.get('closing_rate', 0)}%"

    pop_summary = "데이터 없음"
    if population:
        pop_summary = f"유동인구 전일 대비 {population.get('change_percent', 0):+.1f}%"

    events_summary = "없음"
    if events:
        events_summary = ", ".join(e.get("title", "")[:30] for e in events[:5])

    subsidy_summary = "없음"
    if subsidies:
        total = sum(s.get("max_amount", 0) or 0 for s in subsidies)
        subsidy_summary = f"{len(subsidies)}건 매칭 (최대 {total}만원)"

    # GPT-4o 마케팅 전략 생성
    openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    # 상세 매출 데이터도 가져오기
    sales_detail = await _safe(seoul.get_sales_detail(
        current_user.gu_name or "", current_user.dong_name or "", current_user.business_type or "",
    ))

    # 상세 데이터 요약
    detail_summary = ""
    if sales_detail:
        dow = sales_detail.get("day_of_week", {})
        tz = sales_detail.get("time_zone", {})
        gender = sales_detail.get("gender", {})
        age = sales_detail.get("age_group", {})
        if dow:
            peak_day = max(dow, key=dow.get)
            low_day = min(dow, key=dow.get)
            detail_summary += f"\n요일별 피크: {peak_day} (최저: {low_day})"
        if tz:
            peak_tz = max(tz, key=tz.get)
            detail_summary += f"\n시간대 피크: {peak_tz}"
        if gender:
            m = gender.get("남성_매출", 0)
            f = gender.get("여성_매출", 0)
            total = m + f or 1
            detail_summary += f"\n성별: 남성 {m/total*100:.0f}% / 여성 {f/total*100:.0f}%"
        if age:
            peak_age = max(age, key=age.get)
            detail_summary += f"\n핵심 고객층: {peak_age}"
        ww = sales_detail.get("weekday_vs_weekend", {})
        if ww:
            detail_summary += f"\n주중/주말: {ww.get('주중', 0):,.0f}원 / {ww.get('주말', 0):,.0f}원"

    # 새 데이터 요약 추가
    if floating_pop:
        fp_tz = floating_pop.get("time_zone", {})
        if fp_tz:
            peak = max(fp_tz, key=fp_tz.get)
            detail_summary += f"\n상권 유동인구 피크: {peak} ({fp_tz[peak]:,.0f}명)"
    if change_index:
        detail_summary += f"\n상권 판정: {change_index.get('dominant_status', '미분류')}"
    if weather:
        detail_summary += f"\n오늘 날씨: {weather.get('sky', '')} {weather.get('temperature', '')}, 강수확률 {weather.get('rain_probability', '0%')}"
        for ins in weather.get("insights", []):
            detail_summary += f"\n- {ins}"

    # 부동산학 입지 분석 (마케팅용)
    mkt_location = analyze_location(
        facilities=None,  # 마케팅에서는 별도 fetch 안 했으므로
        workplace_pop=None,
        floating_pop=floating_pop,
        population_data=population,
        radius_summary=None,
        sales_data=sales,
        benchmark=None,
        change_index=change_index,
    )
    if mkt_location:
        loc_text = format_location_analysis(mkt_location)
        detail_summary += loc_text

    # 5-차원 자동 진단 + ICP 학습 프로필
    audit, icp = await _compute_audit_and_icp(
        db, current_user,
        sales_detail=sales_detail,
        competition=competition,
        floating_pop=floating_pop,
        radius_summary=None,
        nearby=None,
        matched_subsidies=subsidies,
    )
    detail_summary += "\n" + _format_audit_for_prompt(audit, icp)

    system_prompt = """당신은 대한민국 최고의 소상공인 마케팅 + 부동산 입지 컨설턴트입니다.
서울시 빅데이터(상권매출, 유동인구, 개폐업, 부동산 입지 분석) + 자동 5-차원 진단(page-cro 프레임워크) + 사용자 ICP 학습 프로필을 종합하여 실전 마케팅 전략을 수립합니다.

## 전문 분야
- 부동산학 기반 상권 입지 분석 (직주비율, 집객력, 상권 생애주기)
- 상권 데이터 기반 타겟 마케팅
- 소상공인 디지털 전환 (SNS, 배달앱, QR 쿠폰)
- 행동경제학 기반 고객 유치 (손실 프레이밍, 앵커링, 사회적 증거)
- 시간대/요일별 프로모션 최적화
- 업종 트렌드 분석 + 경쟁 차별화 포지셔닝

## 응답 원칙
1. **손실 프레이밍**: "추천합니다"가 아니라 "놓치고 있습니다"
2. **데이터 기반**: 제공된 상권 데이터의 구체적 수치를 인용
3. **즉시 실행 가능**: 사장님이 오늘 바로 할 수 있는 것
4. **ROI 제시**: 기대 효과를 정량적으로 (매출 증가율, 고객 수 등)
5. **업종 특화**: 해당 업종의 특성에 맞는 전략
6. **5-차원 진단 weakest 우선**: 자동 진단의 약점 차원(포지셔닝/메시지/타이밍/사회적 증거/마찰)을 strategies 상위 2~3개에서 반드시 다루세요.
7. **ICP 학습 반영**: 학습된 선호 기관/금액대/키워드가 있으면 보조금/마케팅 추천에 우선 반영하세요.

## 응답 형식 (JSON):
{
  "summary": "현재 마케팅 진단 (80자) — 핵심 수치 인용 + 놓치고 있는 것 강조",
  "strategies": [
    {
      "title": "전략명",
      "description": "구체적 실행 방법 (200자) — [근거: 데이터X] 언제, 어디서, 어떻게, 누구에게. 입지 특성(직주비율/상권 생애주기)을 반영.",
      "priority": "high|medium|low",
      "category": "online|offline|event|subsidy|sns|delivery",
      "expected_effect": "[근거: 데이터X] 정량적 기대 효과",
      "budget": "예상 비용",
      "timeline": "실행 기간"
    },
    "...5~7개, 우선순위 순"
  ],
  "weekly_plan": "이번 주 월~일 구체적 실행 계획 (400자) — 요일별 매출 패턴(최고:{X}요일)에 맞춰 배치. 피크 시간({X}시) 활용.",
  "quick_win": "오늘 당장 30분 내에 할 수 있는 1가지 — 구체적 행동 + [근거]",

  "revenue_uplift_plan": {
    "current_avg_ticket": <현재 객단가 정수>,
    "target_avg_ticket": <목표 객단가 정수 — 서울 평균 또는 그 80~90%>,
    "gap_per_order": <차이 정수, 양수면 더 올려야 함>,
    "monthly_orders_estimate": <월 예상 거래 건수 — 분기 데이터 ÷ 3>,
    "monthly_uplift_potential_won": <gap × monthly_orders 추정치>,
    "rationale": "왜 이 갭이 발생했는지 데이터 기반 80자 분석",
    "uplift_options": [
      {
        "name": "구체적인 사이드/세트/추가 옵션 이름",
        "add_price_won": <추가 가격 정수>,
        "expected_attach_rate_pct": <도입 시 부착률 0~100>,
        "expected_avg_uplift_won": <add_price × attach_rate / 100 정수>,
        "how": "사장님이 오늘 매장/배달앱에서 적용하는 방법 100자",
        "ease": "easy|medium|hard"
      },
      "...3개 — 핵심 고객 연령대/객단가 갭/업종 특성에 맞춰. 가장 쉬운 옵션부터 정렬."
    ]
  },

  "ready_to_use_copies": {
    "sms_to_regulars": "단골 50명에게 보낼 SMS 1종 (140자 이내, 핵심 고객 연령대 톤, 피크 시간/요일 활용, 즉시 발송 가능)",
    "store_pop": "매장 카운터/입구에 붙일 POP 카피 (50자, 큰 글씨용, 핵심 차별화 1개 강조)",
    "sns_caption": "인스타그램/네이버 블로그 게시물 캡션 (250자, 핵심 고객 톤, 해시태그 5개 포함, 사진 1장 가정)",
    "delivery_intro": "배달앱(배민/요기요) 가게 소개란 한 줄 (80자, 신규 진입 고객 후킹용)"
  }
}

## 산출물 작성 규칙 (사장님이 오늘 복붙해서 쓸 수준)
- revenue_uplift_plan은 반드시 데이터의 평균 객단가/서울 평균/거래건수를 기반으로 계산. 임의 추정 금지.
- uplift_options 3개는 서로 다른 카테고리(사이드/세트/추가서비스 등)로 다양화.
- ready_to_use_copies는 "공백 채우기 템플릿"이 아니라 사장님이 그대로 발송/인쇄/등록 가능한 완성본.
- SMS는 발송 비용을 의식해 140자 엄수. POP는 50자 엄수.
- 핵심 고객 연령대(데이터 기반)에 맞는 어휘 선택 (예: 50대 → "단골/사장님께서/맛집/푸짐", 20대 → "맛도 가성비도/인생/꿀조합").
- 절대 "[가게명]", "[메뉴명]" 같은 placeholder 쓰지 말고 데이터의 실제 상호/업종으로 채울 것."""

    user_prompt = f"""## 사장님 정보
상호: {current_user.business_name}
업종: {current_user.business_type}
위치: {current_user.gu_name or ''} {current_user.dong_name or ''}

## 상권 데이터 분석 결과
매출 동향: {sales_summary}
경쟁 현황: {competition_summary}
유동인구: {pop_summary}
주변 문화행사: {events_summary}
매칭 지원사업: {subsidy_summary}
{detail_summary}

## 현재 마케팅 활동
쿠폰: 발행 {coupon_row[0]}건, 스캔(사용) {coupon_row[1]}건

## 분석 요청
위 데이터를 종합하여 5만원 가치의 맞춤 마케팅 전략 5~7개를 수립하세요.
필수 분석:
1. 입지 특성(직주비율/상권 생애주기/집객력)에 맞는 마케팅 채널 선택
2. 피크 시간대/요일 데이터에 맞춘 프로모션 타이밍
3. 핵심 고객층(연령/성별) 데이터에 맞는 타겟 메시지
4. 서울 평균 대비 약점을 보완하는 전략
5. 경쟁 업체 밀도를 고려한 차별화 포인트
주의: 데이터에 있는 수치만 인용. 각 전략에 [근거: 데이터와 수치] 필수.

## 할루시네이션 방지 (절대 준수)
1. 제공된 데이터 수치만 인용. 없는 데이터를 만들어내지 마세요.
2. "약 ~", "추정 ~" 대신 정확한 숫자를 쓰세요.
3. 데이터 없는 항목은 "해당 데이터 미제공"으로 명시.
4. 모든 전략에 [데이터 근거] 태그 필수.
5. 인터넷 검색 결과나 일반 상식이 아닌, 제공된 상권 데이터에서만 인사이트를 도출하세요."""

    try:
        response = await openai_client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=2400,
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        import json
        strategy_data = json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Marketing strategy generation failed: {e}")
        strategy_data = {
            "summary": "마케팅 전략 생성에 실패했습니다",
            "strategies": [
                {
                    "title": "QR 쿠폰 이벤트 시작",
                    "description": "할인 쿠폰을 만들어 주변 고객을 유치하세요. 1분이면 만들 수 있습니다.",
                    "priority": "high",
                    "category": "offline",
                    "expected_effect": "신규 고객 유입 기대",
                }
            ],
            "weekly_plan": "이번 주 쿠폰 1개를 만들어 매장에 비치하세요.",
        }

    result = {
        "strategy": strategy_data,
        "data_context": {
            "sales": sales,
            "competition": competition,
            "population": population,
            "events_count": len(events) if events else 0,
            "subsidies_count": len(subsidies) if subsidies else 0,
            "coupon_stats": {
                "total_created": coupon_row[0],
                "total_scanned": coupon_row[1],
            },
        },
    }
    await _set_cache(db, current_user.id, "marketing", result)
    return result
