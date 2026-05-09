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

from app.database import get_db, async_session_factory
from app.config import settings
from app.utils.auth import get_current_user
from app.utils.rate_limit import insights_rate
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


async def _get_previous_cached(
    db: AsyncSession, user_id, insight_type: str
) -> dict | None:
    """이전 주차 캐시 1건 조회 (시계열 diff용). created_at 주입하여 반환."""
    stmt = (
        select(InsightCache)
        .where(
            InsightCache.user_id == user_id,
            InsightCache.insight_type == insight_type,
            InsightCache.week_key != _current_week_key(),
        )
        .order_by(InsightCache.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    cache = result.scalar_one_or_none()
    if not cache:
        return None
    payload = dict(cache.data) if cache.data else {}
    payload["_cached_at"] = cache.created_at.isoformat() if cache.created_at else None
    return payload


@router.get("/competition")
async def get_competition_analysis(
    refresh: bool = Query(False, description="캐시 무시하고 새로 조회"),
    current_user: User = Depends(get_current_user),
):
    """경쟁사 분석: 개폐업 + 매출 상세 + 유동인구 + 주변 경쟁가게 (주간 캐시).

    DB 세션 패턴:
    - Phase A1: 캐시 조회 (짧은 로컬 세션)
    - Phase B: 외부 API gather (DB 점유 없음)
    - Phase A2: 캐시 저장 (짧은 로컬 세션)
    """
    if not current_user.onboarding_completed:
        raise HTTPException(status_code=400, detail="온보딩을 먼저 완료해주세요.")
    if refresh:
        insights_rate.check(f"competition:{current_user.id}")

    # Phase A1: 캐시 조회
    if not refresh:
        async with async_session_factory() as db:
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

    # Phase B: 외부 API 병렬 호출 (DB 점유 없음)
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

    # Phase A2: 캐시 저장
    async with async_session_factory() as db:
        await _set_cache(db, current_user.id, "competition", result)
        await db.commit()
    return result


@router.get("/deep-report")
async def get_deep_report(
    refresh: bool = Query(False),
    current_user: User = Depends(get_current_user),
):
    """GPT-4o 기반 집중분석 리포트 (주간 캐시).

    Phased pattern:
    - A1: cache check
    - A2: RAG + coupon stats + action stats (DB short session)
    - B: Seoul API gather + Kakao + weather (no DB)
    - A3: audit + ICP (DB after Seoul data)
    - B2: GPT call
    - A4: previous cache + cache write
    """
    if not current_user.onboarding_completed:
        raise HTTPException(status_code=400, detail="온보딩을 먼저 완료해주세요.")
    if refresh:
        insights_rate.check(f"deep_report:{current_user.id}")

    # Phase A1: cache check
    if not refresh:
        async with async_session_factory() as db:
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

    # Phase A2: RAG + DB stats (short session)
    async with async_session_factory() as db:
        subsidies = await _safe(rag.search_subsidies_filtered(
            db=db, gu_name=gu, business_type=btype, top_k=5, user_id=current_user.id,
        ))
        coupon_row = (await db.execute(
            select(
                func.count(CouponTemplate.id),
                func.coalesce(func.sum(CouponTemplate.scan_count), 0),
            ).where(CouponTemplate.user_id == current_user.id)
        )).one()
        action_row = (await db.execute(
            select(
                func.count(DailyAction.id),
                func.sum(case((DailyAction.is_completed == True, 1), else_=0)),
            ).where(
                DailyAction.user_id == current_user.id,
                DailyAction.date >= date.today() - timedelta(days=30),
            )
        )).one()
    # === DB session closed ===

    # Phase B: Seoul + Kakao + weather gather (no DB)
    (sales, competition, population, sales_detail,
     floating_pop, change_index, facilities, workplace_pop,
     benchmark, weather, events, nearby, radius_summary) = await asyncio.gather(
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
        _safe(kakao.search_local(search_query, size=10)),
        _safe(kakao.get_radius_competitor_summary(current_user.lat, current_user.lng)) if has_coords else asyncio.sleep(0),
    )
    if not has_coords:
        radius_summary = None

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
        qoq = sales.get("quarterly_change_percent")
        if qoq is not None:
            sections.append(f"- 전분기 대비 변화: {qoq:+.1f}% (출처: 서울 VwsmTrdarSelngQq, {sales.get('current_quarter','')} vs {sales.get('prev_quarter','')})")
        else:
            sections.append(f"- 전분기 대비 변화: 데이터 없음 (이전 분기 데이터 미확보)")
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

    # Phase A3: audit + ICP (DB short session, Seoul 데이터 모인 후)
    async with async_session_factory() as db:
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
  "executive_summary": {
    "current": "현황 진단 1단락 (200자) — 매출/유동인구/경쟁 핵심 수치 인용 + 종합 평가. 차분한 컨설턴트 어조.",
    "risk": "핵심 위험 1단락 (150자) — 수치 근거 + 방치 시 손실 추정. 손실 프레이밍.",
    "recommendation": "권고 1단락 (150자) — 가장 임팩트 큰 1~2개 액션 + 실행 시 기대효과."
  },
  "location_analysis": "상권 입지 종합 분석 (300자) — 직주비율 {X}, 집객력 {X}점, HHI {X}, 상권 생애주기 '{X}'를 교차 분석. 이 입지가 해당 업종에 유리한지/불리한지 구체적으로.",
  "swot": {
    "strengths": ["[근거: 데이터X] 강점 설명 — 3~5개"],
    "weaknesses": ["[근거: 데이터X] 약점 설명 — 3~5개"],
    "opportunities": ["[근거: 데이터X] 기회 요인 — 3~5개"],
    "threats": ["[근거: 데이터X] 위협 요인 — 3~5개"]
  },
  "tows_matrix": {
    "so_strategy": "SO 전략 (강점-기회 결합, 80자) — 어떤 강점으로 어떤 기회를 잡을지 1줄",
    "st_strategy": "ST 전략 (강점-위협 방어, 80자) — 강점으로 위협을 어떻게 방어할지 1줄",
    "wo_strategy": "WO 전략 (약점-기회 보완, 80자) — 기회를 활용해 약점을 어떻게 보완할지 1줄",
    "wt_strategy": "WT 전략 (약점-위협 회피, 80자) — 최소화 또는 회피 전략 1줄"
  },
  "positioning_map": {
    "x_label": "가격대 (낮음→높음)",
    "y_label": "품질·서비스 (낮음→높음)",
    "us": {"x": <0~100>, "y": <0~100>, "label": "우리 가게"},
    "competitors": [
      {"x": <0~100>, "y": <0~100>, "label": "경쟁사 또는 평균 라벨 (10자)"}
    ],
    "interpretation": "이 포지셔닝의 빈 공간(blue ocean)과 충돌 영역(red ocean) 1줄 설명 (80자)"
  },
  "customer_insight": "핵심 고객 프로필 (300자) — 성별 비중(남X%/여X%), 핵심 연령대({X}대, 매출 {X}원), 피크 시간({X}시, 유동인구 {X}명)을 교차하여 '누가 언제 오는지' 구체적으로. 놓치고 있는 고객층도 분석.",
  "time_strategy": "시간 최적화 전략 (300자) — 요일별 매출 데이터(최고:{X}요일, 최저:{X}요일) + 시간대별 유동인구 피크({X}시)를 근거로. 주중/주말 차별화 전략 구체적으로.",
  "competition_analysis": "경쟁 분석 (300자) — 서울 평균 대비 매출 {X}%, 반경 500m 내 {X}개 업체, 개업률 {X}%/폐업률 {X}%. 차별화 포인트와 방어 전략.",
  "trend_analysis": "업종+상권 트렌드 분석 (300자) — 상권변화지표 '{X}' + 개폐업 데이터 근거. 이 업종이 이 지역에서 성장/쇠퇴 중인지 데이터 기반 판단.",
  "action_items": [
    {
      "priority": "high|medium|low",
      "action": "즉시 실행 가능한 행동 (구체적, 60자)",
      "expected_impact": "[근거: 데이터X] 정량적 기대 효과",
      "timeline": "실행 기간",
      "cost": "예상 비용",
      "impact_score": <1~10 매출/고객 임팩트 점수>,
      "effort_score": <1~10 실행 난이도/비용/시간 점수>,
      "category": "online|offline|event|subsidy|sns|delivery|operations"
    },
    "...최대 7개, 우선순위 순. impact_score/effort_score는 의사결정자가 2x2 매트릭스에 배치할 수 있도록 정확히 산정."
  ],
  "risk_alert": "가장 시급한 위험 1가지 — [근거: 수치] + 방치 시 예상 손실",
  "monthly_goal": {
    "summary": "이번 달 한 줄 목표 (40자)",
    "kpis": [
      {
        "name": "매출",
        "target_value": <목표 정수>,
        "current_value": <현재 추정 정수>,
        "unit": "원|건|%|개",
        "rationale": "이 목표를 잡은 이유 50자"
      },
      "...3개 (매출 / 신규 고객 또는 객단가 / 마케팅 실행건수)"
    ]
  }
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
            max_tokens=3500,
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        import json
        report = json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Deep report generation failed: {e}")
        report = {
            "executive_summary": {"current": "리포트 생성에 실패했습니다.", "risk": "", "recommendation": ""},
            "swot": {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []},
            "tows_matrix": None,
            "positioning_map": None,
            "customer_insight": "",
            "time_strategy": "",
            "competition_analysis": "",
            "action_items": [],
            "risk_alert": "",
            "monthly_goal": None,
        }

    # Phase A4: previous diff + cache write (DB short session)
    async with async_session_factory() as db:
        previous = await _get_previous_cached(db, current_user.id, "deep_report")
        previous_snapshot = None
        if previous:
            prev_report = previous.get("report", {})
            prev_es = prev_report.get("executive_summary")
            prev_risk = prev_report.get("risk_alert", "")
            if isinstance(prev_es, dict):
                prev_summary_text = prev_es.get("current") or prev_es.get("summary") or ""
            else:
                prev_summary_text = prev_es or ""
            previous_snapshot = {
                "summary": prev_summary_text,
                "risk_alert": prev_risk,
                "generated_at": previous.get("_cached_at"),
            }

        result = {
            "report": report,
            "previous": previous_snapshot,
            "data_summary": {
                "sales": sales,
                "competition": competition,
                "population": population,
                "competitor_count": competitor_count,
                "subsidy_count": len(subsidies) if subsidies else 0,
            },
            "_disclosure": {
                "ai_estimated_fields": [
                    "report.positioning_map.us.x", "report.positioning_map.us.y",
                    "report.positioning_map.competitors[].x", "report.positioning_map.competitors[].y",
                    "report.action_items[].impact_score", "report.action_items[].effort_score",
                    "report.monthly_goal.kpis[].target_value", "report.monthly_goal.kpis[].current_value",
                ],
                "grounding_method": "gpt_estimate",
                "note": "AI가 산출한 추정치이며 공식 미적용. 의사결정 시 실데이터로 검증 필요.",
            },
        }
        await _set_cache(db, current_user.id, "deep_report", result)
        await db.commit()
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
):
    """GPT-4o 기반 맞춤 마케팅 전략 (주간 캐시).

    Phased pattern (PRIORITY-VERIFY P1):
    - A1: cache check (short DB session)
    - A2: RAG + coupon stats (short DB session)
    - B: Seoul API gather + sales_detail (no DB)
    - A3: audit + ICP (short DB session, after Seoul data ready)
    - B2: GPT call (no DB)
    - A4: cache write (short DB session)
    """
    if not current_user.onboarding_completed:
        raise HTTPException(status_code=400, detail="온보딩을 먼저 완료해주세요.")
    if refresh:
        insights_rate.check(f"marketing:{current_user.id}")

    # Phase A1: cache check
    if not refresh:
        async with async_session_factory() as db:
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

    # Phase A2: RAG + coupon stats (DB short session)
    async with async_session_factory() as db:
        subsidies = await _safe(rag.search_subsidies_filtered(
            db=db, gu_name=gu, business_type=btype, top_k=3, user_id=current_user.id,
        ))
        coupon_row = (await db.execute(
            select(
                func.count(CouponTemplate.id),
                func.coalesce(func.sum(CouponTemplate.scan_count), 0),
            ).where(CouponTemplate.user_id == current_user.id)
        )).one()
    # === DB session closed ===

    # Phase B: Seoul API gather (no DB held)
    (sales, competition, population, events,
     floating_pop, change_index, weather) = await asyncio.gather(
        _safe(seoul.get_commercial_sales(gu, dong, btype)),
        _safe(seoul.get_business_openclose(gu, btype)),
        _safe(seoul.get_living_population(dong, gu)),
        _safe(seoul.get_cultural_events(gu)),
        _safe(seoul.get_commercial_floating_pop(gu, dong, btype)),
        _safe(seoul.get_commercial_change_index(gu, dong)),
        _safe(weather_svc.get_today_weather(gu)),
    )

    # 데이터 요약
    sales_summary = "데이터 없음"
    if sales:
        change = sales.get("quarterly_change_percent")
        if change is None:
            sales_summary = f"전분기 데이터 없음 ({sales.get('area_name', '')}) — 이전 분기 매출 데이터 미확보"
        else:
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
            # PRIORITY-VERIFY P0-F: 키 mismatch 수정 (응답은 _비중 키 사용)
            m_pct = gender.get("남성_비중", gender.get("남성_매출", 0))
            f_pct = gender.get("여성_비중", gender.get("여성_매출", 0))
            detail_summary += f"\n성별: 남성 {m_pct:.0f}% / 여성 {f_pct:.0f}%"
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

    # Phase A3: audit + ICP (DB short session, Seoul 데이터 모인 후)
    async with async_session_factory() as db:
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
      "description": "구체적 실행 방법 (200자) — 언제, 어디서, 어떻게, 누구에게. 입지 특성(직주비율/상권 생애주기)을 반영.",
      "evidence": "이 전략을 추천한 데이터 근거 1줄 (60자, 예: '여성 30대 매출 47% — 서울 평균 +8%p')",
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

  "budget_scenarios": [
    {
      "budget_label": "0원",
      "budget_won": 0,
      "headline": "비용 0으로 가능한 핵심 한 수 (40자)",
      "actions": ["구체적 액션 3가지 (각 30자)"],
      "expected_uplift_won": <월 예상 추가 매출 정수>,
      "expected_orders": <월 예상 추가 주문 정수>
    },
    {
      "budget_label": "5만원",
      "budget_won": 50000,
      "headline": "...",
      "actions": ["..."],
      "expected_uplift_won": <int>,
      "expected_orders": <int>
    },
    {
      "budget_label": "30만원",
      "budget_won": 300000,
      "headline": "...",
      "actions": ["..."],
      "expected_uplift_won": <int>,
      "expected_orders": <int>
    }
  ],

  "channel_priority": [
    {
      "channel": "instagram|naver_blog|baemin|yogiyo|sms|flyer|kakao_ch",
      "label": "한국어 채널명 (예: '인스타그램')",
      "fit_score": <0~100 적합도, 입지/고객층/업종 고려>,
      "expected_roi_pct": <투자 대비 예상 수익률, 100=손익분기>,
      "rationale": "왜 이 점수인지 1줄 (60자, 데이터 인용)",
      "first_step": "이 채널 첫 진입 액션 1줄 (40자)"
    },
    "...4~5개, fit_score 내림차순"
  ],

  "copy_variants": {
    "trust": {
      "tone_label": "신뢰형",
      "tone_desc": "전문성·안정감 강조 (50대 단골/회사원 타겟)",
      "sms_to_regulars": "단골 SMS (140자) — 신뢰형 톤",
      "store_pop": "매장 POP (50자) — 신뢰형 톤",
      "sns_caption": "SNS 캡션 (250자, 해시태그 5) — 신뢰형 톤",
      "delivery_intro": "배달앱 소개 한 줄 (80자) — 신뢰형 톤"
    },
    "friendly": {
      "tone_label": "친근형",
      "tone_desc": "정·따뜻함 강조 (동네 주민/가족 타겟)",
      "sms_to_regulars": "...",
      "store_pop": "...",
      "sns_caption": "...",
      "delivery_intro": "..."
    },
    "urgent": {
      "tone_label": "긴급형",
      "tone_desc": "한정·마감 강조 (즉시 전환·신규 후킹)",
      "sms_to_regulars": "...",
      "store_pop": "...",
      "sns_caption": "...",
      "delivery_intro": "..."
    }
  },

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
- 절대 "[가게명]", "[메뉴명]" 같은 placeholder 쓰지 말고 데이터의 실제 상호/업종으로 채울 것.
- budget_scenarios: 각 예산은 "추가 한 달 매출 X원"이 명확해야 함. 0원 시나리오는 무료 채널(SNS/매장POP/단골SMS)만 사용.
- channel_priority: 입지(직주비율/유동인구) + 핵심 고객층 + 업종 데이터 모두 반영. 배달 비중이 낮은 업종에 배달앱을 1위로 두지 말 것.
- copy_variants: 동일 메시지 톤만 바꾸지 말고 **각 톤의 호소 전략 자체를 바꿀 것** (신뢰=수치+경력, 친근=인사+이야기, 긴급=한정+카운트다운)."""

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
            max_tokens=4000,
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
        # 정직성 라벨: GPT 산출 숫자(공식 미적용) 필드 명시.
        # 프론트엔드는 이 목록의 필드에 "추정치 (AI 산출)" tooltip 노출.
        "_disclosure": {
            "ai_estimated_fields": [
                "strategy.budget_scenarios[].expected_uplift_won",
                "strategy.budget_scenarios[].expected_orders",
                "strategy.channel_priority[].fit_score",
                "strategy.channel_priority[].expected_roi_pct",
                "strategy.revenue_uplift_plan.monthly_uplift_potential_won",
                "strategy.revenue_uplift_plan.uplift_options[].expected_attach_rate_pct",
                "strategy.revenue_uplift_plan.uplift_options[].expected_avg_uplift_won",
            ],
            "grounding_method": "gpt_estimate",
            "note": "AI가 산출한 추정치이며 공식 미적용. 의사결정 시 실제 캠페인 결과로 검증 필요.",
        },
    }
    # Phase A4: cache write
    async with async_session_factory() as db:
        await _set_cache(db, current_user.id, "marketing", result)
        await db.commit()
    return result


@router.get("/menu-strategy")
async def get_menu_strategy(
    refresh: bool = Query(False),
    current_user: User = Depends(get_current_user),
):
    """업종 + 주변 경쟁사 + 핵심 고객층 데이터 기반 메뉴 전략 (주간 캐시).

    Phased pattern: cache check / 외부 gather / cache write.
    """
    if not current_user.onboarding_completed:
        raise HTTPException(status_code=400, detail="온보딩을 먼저 완료해주세요.")
    if refresh:
        insights_rate.check(f"menu_strategy:{current_user.id}")

    # Phase A1: cache check
    if not refresh:
        async with async_session_factory() as db:
            cached = await _get_cached(db, current_user.id, "menu_strategy")
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

    (sales_detail, benchmark, nearby, events, weather) = await asyncio.gather(
        _safe(seoul.get_sales_detail(gu, dong, btype)),
        _safe(seoul.get_benchmark(gu, dong, btype)),
        _safe(kakao.search_local(search_query, size=10)),
        _safe(seoul.get_cultural_events(gu)),
        _safe(weather_svc.get_today_weather(gu)),
    )

    # 컨텍스트 요약
    customer_summary = "데이터 미제공"
    if sales_detail:
        gender = sales_detail.get("gender", {})
        age = sales_detail.get("age_group", {})
        tz = sales_detail.get("time_zone", {})
        peak_age = max(age, key=age.get) if age else ""
        peak_tz = max(tz, key=tz.get) if tz else ""
        m_pct = gender.get("남성_비중", 0)
        f_pct = gender.get("여성_비중", 0)
        customer_summary = (
            f"성별 남{m_pct}%/여{f_pct}%, 핵심연령 {peak_age}, 피크시간 {peak_tz}시"
        )

    benchmark_summary = "데이터 미제공"
    if benchmark:
        benchmark_summary = (
            f"평균 객단가 {benchmark.get('local_avg_ticket', 0):,.0f}원 "
            f"(서울 평균 {benchmark.get('seoul_avg_ticket', 0):,.0f}원, "
            f"{benchmark.get('ticket_diff_pct', 0):+.1f}%)"
        )

    nearby_summary = "주변 경쟁사 데이터 미제공"
    nearby_names = []
    if nearby:
        for p in nearby:
            if p.get("place_name") != current_user.business_name:
                nearby_names.append(f"{p.get('place_name', '')}({p.get('category_name', '').split(' > ')[-1]})")
        if nearby_names:
            nearby_summary = f"주변 {len(nearby_names)}곳: {', '.join(nearby_names[:8])}"

    events_summary = "주변 행사 없음"
    if events:
        events_summary = ", ".join(e.get("title", "")[:25] for e in events[:3])

    weather_summary = ""
    if weather:
        weather_summary = (
            f"오늘 {weather.get('sky', '')} {weather.get('temperature', '')} / "
            f"강수 {weather.get('rain_probability', '0%')}"
        )

    today = date.today()

    openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    system_prompt = """당신은 소상공인 외식·서비스업 메뉴/상품 전략 컨설턴트입니다.
업종, 주변 경쟁사 분포, 핵심 고객층(성별/연령/시간대), 객단가 갭, 시즌 컨텍스트를 종합해
**메뉴 추천이 아니라 메뉴 '전략'**을 도출합니다.

## 핵심 원칙
1. **갭 분석 우선**: 주변 경쟁사가 모두 가진 카테고리인데 우리만 없음 = 강한 도입 후보. 반대로 모두 가진 카테고리에 따라가는 me-too는 약한 신호.
2. **고객 적합도**: 핵심 고객층(연령/성별)에 자연스러운 메뉴인지 검증. 50대 여성 비중 높은 가게에 20대 남성 시그니처 메뉴 추천 금지.
3. **객단가 갭 활용**: 서울 평균보다 객단가 낮으면 → 프리미엄 라인 / 높으면 → 가성비 라인.
4. **시즌 캘린더**: 현재 날짜 기준 다음 4주를 절기/공휴일/날씨와 매핑. 실제 한국 5월이면 어버이날(5/8), 가정의 달 등 구체적으로.
5. **할루시네이션 금지**: 데이터에 없는 매출/순위 수치 만들지 마세요. 추정 시 "추정" 명시.
6. **운영 비용 명시**: 모든 메뉴 도입 후보에 implementation_cost (low/medium/high) 정확히 산정.

## 응답 형식 (JSON)
{
  "summary": "메뉴 전략 한 줄 진단 (50자) — 가장 큰 기회 또는 위험",
  "gap_analysis": {
    "headline": "갭 분석 핵심 (60자)",
    "missing_categories": [
      {
        "category": "구체적 메뉴 카테고리 (예: '비빔밥 / 단품 면 / 디저트')",
        "competitor_coverage_pct": <주변 경쟁사 보유 추정 % 0~100>,
        "fit_score": <우리 가게 적합도 0~100>,
        "rationale": "왜 우리 가게에 적합한지 1줄 (60자, 핵심 고객층/객단가 인용)",
        "expected_avg_ticket_change_pct": <예상 객단가 변화 % 부호 포함>,
        "implementation_cost": "low|medium|high"
      },
      "...3개 — fit_score 내림차순"
    ]
  },
  "seasonal_calendar": [
    {
      "week_label": "5월 N주차 (M/D~M/D)",
      "theme": "이 주의 테마 (절기/공휴일/시즌)",
      "menu_idea": "구체적 메뉴 아이디어 (40자)",
      "rationale": "왜 이 시기에 적합한지 1줄 (60자)",
      "channel_action": "단골 SMS|매장 POP|SNS|배달앱 배너 중 1~2개"
    },
    "...4주 — 오늘 기준 다음 4주"
  ],
  "differentiation_pick": {
    "menu_name": "차별화 메뉴 1개 (구체적, 30자)",
    "why_us": "왜 우리 가게에 맞는지 1줄 (80자, 핵심 고객층 + 객단가 갭 인용)",
    "why_not_competitors": "주변 경쟁사가 못 하는 또는 안 하는 이유 1줄 (60자)",
    "first_step": "오늘 30분 안에 시작할 액션 1줄 (60자)"
  }
}"""

    user_prompt = f"""## 사장님 정보
상호: {current_user.business_name}
업종: {current_user.business_type}
위치: {gu} {dong}
오늘 날짜: {today.isoformat()} ({today.strftime('%Y년 %m월 %d일')})

## 데이터 컨텍스트
[핵심 고객층] {customer_summary}
[객단가 갭] {benchmark_summary}
[주변 경쟁사] {nearby_summary}
[주변 문화행사] {events_summary}
[오늘 날씨] {weather_summary}

## 요청
위 데이터만 사용하여 메뉴 전략을 JSON으로 작성하세요.
- gap_analysis는 주변 경쟁사 카테고리 분포에서 도출.
- seasonal_calendar는 오늘 날짜({today.isoformat()}) 기준 4주, 한국의 5월 컨텍스트(어버이날/스승의날/가정의 달) 반영.
- 메뉴명은 placeholder 금지. 업종({btype}) 맥락에 맞는 실제 메뉴명으로."""

    try:
        response = await openai_client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=1800,
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        import json
        strategy = json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"Menu strategy generation failed: {e}")
        strategy = {
            "summary": "메뉴 전략 생성에 실패했습니다",
            "gap_analysis": {"headline": "데이터 부족", "missing_categories": []},
            "seasonal_calendar": [],
            "differentiation_pick": None,
        }

    result = {
        "strategy": strategy,
        "generated_at": today.isoformat(),
        "_disclosure": {
            "ai_estimated_fields": [
                "strategy.gap_analysis.missing_categories[].competitor_coverage_pct",
                "strategy.gap_analysis.missing_categories[].fit_score",
                "strategy.gap_analysis.missing_categories[].expected_avg_ticket_change_pct",
            ],
            "grounding_method": "gpt_estimate",
            "note": "AI가 산출한 추정치이며 공식 미적용. 실제 도입 전 검증 필요.",
        },
    }
    # Phase A2: cache write
    async with async_session_factory() as db:
        await _set_cache(db, current_user.id, "menu_strategy", result)
        await db.commit()
    return result


@router.get("/survival-score")
async def get_survival_score(
    refresh: bool = Query(False),
    current_user: User = Depends(get_current_user),
):
    """폐업 위험 진단 (Survival Matrix).

    GPT 호출 없음 — 같은 동/업종의 폐업 가게 패턴 vs 우리 가게 위험 신호를 결정론적으로 매칭.
    'AI 코치만 알 수 있는 손실' 정체성의 핵심 카드.

    DB 패턴: 캐시 조회 / Seoul API gather / 캐시 저장 — 각 phase 짧은 로컬 세션.
    """
    if not current_user.onboarding_completed:
        raise HTTPException(status_code=400, detail="온보딩을 먼저 완료해주세요.")

    if not refresh:
        async with async_session_factory() as db:
            cached = await _get_cached(db, current_user.id, "survival_score")
        if cached:
            return cached

    seoul = SeoulAPIService()

    async def _safe(coro):
        try:
            return await coro
        except Exception:
            return None

    gu = current_user.gu_name or ""
    dong = current_user.dong_name or ""
    btype = current_user.business_type or ""

    (sales, openclose, change_index, population) = await asyncio.gather(
        _safe(seoul.get_commercial_sales(gu, dong, btype)),
        _safe(seoul.get_business_openclose(gu, btype)),
        _safe(seoul.get_commercial_change_index(gu, dong)),
        _safe(seoul.get_living_population(dong, gu)),
    )

    today = date.today()

    # 우리 가게 영업 개월수 (개점일 우선, 없으면 가입일 추정)
    operating_months = None
    op_start = current_user.business_start_date
    if not op_start and current_user.created_at:
        op_start = current_user.created_at.date()
    if op_start:
        operating_months = max(0, (today - op_start).days // 30)

    # === 위험 신호 5종 (결정론적 룰) ===
    signals: list[dict] = []

    # Signal 1: 매출 감소 (분기 변화율 -5% 이하)
    sales_change = (sales.get("quarterly_change_percent") if sales else None) or 0
    signals.append({
        "name": "매출 감소",
        "current": f"전분기 {sales_change:+.1f}%" if sales else "데이터 없음",
        "threshold": "-5% 이하",
        "severity": "high" if sales_change <= -10 else "medium" if sales_change <= -5 else "low",
        "triggered": bool(sales and sales_change <= -5),
    })

    # Signal 2: 동네 폐업률 (서울 평균 ~5% 기준)
    closing_rate = openclose.get("closing_rate", 0) if openclose else 0
    signals.append({
        "name": "동네 폐업률 상승",
        "current": f"{closing_rate}%" if openclose else "데이터 없음",
        "threshold": "5% 초과",
        "severity": "high" if closing_rate > 8 else "medium" if closing_rate > 5 else "low",
        "triggered": bool(openclose and closing_rate > 5),
    })

    # Signal 3: 상권변화지표가 축소/정체
    change_status = change_index.get("dominant_status", "") if change_index else ""
    is_declining = any(kw in change_status for kw in ("쇠퇴", "축소", "정체"))
    signals.append({
        "name": "상권 정체/축소",
        "current": change_status or "데이터 없음",
        "threshold": "확장/다이나믹 외",
        "severity": "high" if "쇠퇴" in change_status or "축소" in change_status else "medium" if is_declining else "low",
        "triggered": is_declining,
    })

    # Signal 4: 유동인구 감소
    pop_change = population.get("change_percent", 0) if population else 0
    signals.append({
        "name": "유동인구 감소",
        "current": f"전일 대비 {pop_change:+.1f}%" if population else "데이터 없음",
        "threshold": "-3% 이하",
        "severity": "medium" if pop_change <= -3 else "low",
        "triggered": bool(population and pop_change <= -3),
    })

    # Signal 5: 우리 가게 영업기간이 폐업 평균에 근접
    closed_avg = change_index.get("closed_avg_months", 0) if change_index else 0
    survival_avg = change_index.get("survival_avg_months", 0) if change_index else 0
    near_closing_zone = False
    operating_pct = None
    if operating_months is not None and closed_avg > 0:
        operating_pct = round((operating_months / closed_avg) * 100)
        # 영업기간이 폐업 평균의 70% 이상이면 위험 구간
        near_closing_zone = operating_pct >= 70 and operating_pct <= 130
    signals.append({
        "name": "폐업 평균 영업기간 근접",
        "current": f"우리 {operating_months}개월 / 폐업 평균 {closed_avg}개월" if operating_months and closed_avg else "데이터 없음",
        "threshold": "폐업 평균의 70~130%",
        "severity": "high" if near_closing_zone else "low",
        "triggered": near_closing_zone,
    })

    # === 종합 점수 계산 ===
    triggered = [s for s in signals if s["triggered"]]
    triggered_count = len(triggered)
    high_count = sum(1 for s in triggered if s["severity"] == "high")
    medium_count = sum(1 for s in triggered if s["severity"] == "medium")

    # 100점에서 차감 (high=20, medium=10, low=5)
    deduction = high_count * 20 + medium_count * 10 + (triggered_count - high_count - medium_count) * 5
    survival_score = max(0, 100 - deduction)

    if survival_score >= 80:
        risk_level = "safe"
        risk_label = "안정"
    elif survival_score >= 60:
        risk_level = "watch"
        risk_label = "관찰"
    elif survival_score >= 40:
        risk_level = "warning"
        risk_label = "경고"
    else:
        risk_level = "critical"
        risk_label = "위험"

    # 패턴 유사도 (트리거된 high signal 비중)
    pattern_similarity_pct = round((triggered_count / len(signals)) * 100) if signals else 0

    # 헤드라인 생성
    closing_count_area = change_index.get("closing_area_count", 0) if change_index else 0
    sample_n = change_index.get("sample_count", 0) if change_index else 0
    if sample_n >= 3 and closed_avg > 0:
        headline = f"같은 동네 같은 업종 {closing_count_area}곳이 평균 {closed_avg}개월에 폐업"
    elif openclose:
        headline = f"이 동네 {btype} 폐업률 {closing_rate}% (개업 {openclose.get('opening_rate', 0)}%)"
    else:
        headline = "폐업 데이터 수집 중"

    # 생존 액션 (가장 큰 위험 신호 기반) — 결정론적 룰 매핑 (AI 산출 아님)
    high_signals = [s for s in triggered if s["severity"] == "high"]
    survival_action_source = "deterministic_rule"  # vs "gpt" — 정직성 라벨
    if high_signals:
        action_map = {
            "매출 감소": "이번 주 단골 SMS 발송 + 재방문 쿠폰 1종 즉시 배포",
            "동네 폐업률 상승": "주변 폐업 가게 카테고리 확인 후 차별화 메뉴 1개 도입",
            "상권 정체/축소": "오프라인 의존도 줄이고 배달앱/SNS 채널 확대",
            "유동인구 감소": "기존 고객 데이터로 단골 마케팅 강화 (신규 의존 줄이기)",
            "폐업 평균 영업기간 근접": "고정비 재점검 + 임대료 재계약 시 협상 자료 준비",
        }
        survival_action = action_map.get(high_signals[0]["name"], "위험 신호 재진단 필요")
    elif triggered:
        survival_action = "지금은 안정권. 단골 관리 + 객단가 옵션 1개 추가로 격차 더 벌리기"
    else:
        survival_action = "현재 위험 신호 없음. 월 1회 재진단으로 변화 모니터링"

    result = {
        "survival_score": survival_score,
        "risk_level": risk_level,
        "risk_label": risk_label,
        "headline": headline,
        "your_position": {
            "operating_months": operating_months,
            "closed_avg_months": closed_avg,
            "survival_avg_months": survival_avg,
            "operating_percentile": operating_pct,
        },
        "risk_signals": signals,
        "triggered_count": triggered_count,
        "total_signals": len(signals),
        "pattern_similarity_pct": pattern_similarity_pct,
        "survival_action": survival_action,
        "survival_action_source": survival_action_source,  # "deterministic_rule" — UI에 "기본 가이드" 라벨
        "data_sources": {
            "sales": sales is not None,
            "openclose": openclose is not None,
            "change_index": change_index is not None,
            "population": population is not None,
        },
    }
    async with async_session_factory() as db:
        await _set_cache(db, current_user.id, "survival_score", result)
        await db.commit()
    return result
