"""
주간 리포트 라우터
- GET /reports/weekly: PDF 다운로드 (대시보드/인사이트 데이터를 6-카테고리 리포트로 합성)
"""
import asyncio
import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import CouponTemplate, DailyAction, User
from app.models.insight_cache import InsightCache
from app.services.rag_service import RAGService
from app.services.report_generator import assemble_report_data, generate_pdf
from app.services.risk_score_engine import RiskScoreEngine
from app.services.seoul_api_service import SeoulAPIService
from app.utils.auth import get_current_user
from io import BytesIO

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/weekly")
async def get_weekly_report(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """주간 마케팅 인사이트 PDF 리포트.

    대시보드/인사이트와 동일한 데이터 소스를 사용하되,
    6-카테고리 가중 점수 + 3-tier 액션 플랜으로 재구성하여 PDF로 출력.
    """
    if not current_user.onboarding_completed:
        raise HTTPException(status_code=400, detail="온보딩을 먼저 완료해주세요.")

    today = date.today()
    rag = RAGService()
    seoul = SeoulAPIService()

    async def _safe(coro):
        try:
            return await coro
        except Exception as e:
            logger.warning(f"Data source failed: {e}")
            return None

    gu = current_user.gu_name or ""
    dong = current_user.dong_name or ""
    btype = current_user.business_type or ""

    matched, sales_data, pop_data, competition_data, change_index_data = await asyncio.gather(
        _safe(rag.search_subsidies_filtered(db=db, gu_name=gu, business_type=btype, top_k=5, user_id=current_user.id)),
        _safe(seoul.get_commercial_sales(gu, dong, btype)),
        _safe(seoul.get_living_population(dong, gu)),
        _safe(seoul.get_business_openclose(gu, btype)),
        _safe(seoul.get_commercial_change_index(gu, dong)),
    )

    # 집중분석 캐시 조회 (있으면 PDF 뒷부분에 추가 섹션 렌더링)
    deep_report_data = None
    try:
        deep_stmt = (
            select(InsightCache.data)
            .where(
                InsightCache.user_id == current_user.id,
                InsightCache.insight_type == "deep_report",
            )
            .order_by(InsightCache.created_at.desc())
            .limit(1)
        )
        deep_row = (await db.execute(deep_stmt)).scalar_one_or_none()
        if deep_row and isinstance(deep_row, dict):
            # report 본문 + data_summary(차트용) 둘 다 살림
            report_body = deep_row.get("report") or deep_row
            if isinstance(report_body, dict):
                deep_report_data = {
                    **report_body,
                    "data_summary": deep_row.get("data_summary") or {},
                }
            else:
                deep_report_data = deep_row
    except Exception as e:
        logger.warning(f"deep_report cache fetch failed: {e}")

    matched = matched or []
    total_amount = sum(s.get("max_amount", 0) for s in matched if s.get("max_amount"))

    # 쿠폰 통계
    stmt = select(
        func.count(CouponTemplate.id),
        func.coalesce(func.sum(CouponTemplate.scan_count), 0),
    ).where(CouponTemplate.user_id == current_user.id)
    result = await db.execute(stmt)
    coupon_row = result.one()
    coupon_created = coupon_row[0] or 0
    coupon_scanned = coupon_row[1] or 0

    # 액션 완료율 (최근 30일)
    stmt = select(
        func.count(DailyAction.id),
        func.sum(case((DailyAction.is_completed == True, 1), else_=0)),
    ).where(
        DailyAction.user_id == current_user.id,
        DailyAction.date >= today - timedelta(days=30),
    )
    result = await db.execute(stmt)
    action_row = result.one()
    total_actions = action_row[0] or 0
    completed_actions = action_row[1] or 0
    completion_rate = completed_actions / total_actions if total_actions > 0 else 0.0

    # 위험도 추세
    stmt = select(DailyAction.risk_score).where(
        DailyAction.user_id == current_user.id,
        DailyAction.date >= today - timedelta(days=30),
    ).order_by(DailyAction.date.asc())
    result = await db.execute(stmt)
    previous_scores = [r[0] for r in result.all() if r[0] is not None]

    engine = RiskScoreEngine()
    risk_result = engine.compute(
        sales_data=sales_data,
        population_data=pop_data,
        competition_data=competition_data,
        change_index_data=change_index_data,
        subsidy_matches=matched,
        action_completion_rate=completion_rate,
        user_created_at=current_user.created_at.date() if current_user.created_at else None,
        business_start_date=current_user.business_start_date,
        previous_scores=previous_scores,
    )

    report = assemble_report_data(
        business_name=current_user.business_name or "사장님",
        business_type=current_user.business_type or "미등록",
        location=f"{gu} {dong}".strip() or "미등록",
        sales_data=sales_data,
        population_data=pop_data,
        competition_data=competition_data,
        subsidy_matches=matched,
        total_potential_amount=total_amount,
        coupon_created=coupon_created,
        coupon_scanned=coupon_scanned,
        action_completion_rate=completion_rate,
        risk_score=risk_result.composite_score,
        trend_direction=risk_result.trend_direction,
        deep_report=deep_report_data,
    )

    pdf_bytes = generate_pdf(report)
    filename = f"weekly-report-{today.isoformat()}.pdf"

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
