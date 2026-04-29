"""
대시보드 라우터
- GET /dashboard: 메인 대시보드 데이터 (집계 + 복합 위험도)
"""
import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from datetime import date, timedelta

from app.database import get_db
from app.utils.auth import get_current_user
from app.models import User, DailyAction, CouponTemplate
from app.services.rag_service import RAGService
from app.services.seoul_api_service import SeoulAPIService
from app.services.social_proof_service import SocialProofService
from app.services.risk_score_engine import RiskScoreEngine
from app.utils.loss_framing import generate_loss_message

router = APIRouter()


@router.get("")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """메인 대시보드 집계 데이터 + 복합 위험도 분석."""
    if not current_user.onboarding_completed:
        raise HTTPException(status_code=400, detail="온보딩을 먼저 완료해주세요.")

    today = date.today()

    # 오늘의 액션
    stmt = select(DailyAction).where(
        DailyAction.user_id == current_user.id,
        DailyAction.date == today,
    )
    result = await db.execute(stmt)
    today_action = result.scalar_one_or_none()

    # 외부 API 병렬 호출
    rag = RAGService()
    seoul = SeoulAPIService()
    social = SocialProofService(db)

    async def _safe(coro):
        try:
            return await coro
        except Exception:
            return None

    (matched, sales_data, events, pop_data, social_proof,
     competition_data, change_index_data) = await asyncio.gather(
        _safe(rag.search_subsidies_filtered(
            db=db,
            gu_name=current_user.gu_name or "",
            business_type=current_user.business_type or "",
            top_k=3,
            user_id=current_user.id,
        )),
        _safe(seoul.get_commercial_sales(
            current_user.gu_name or "",
            current_user.dong_name or "",
            current_user.business_type or "",
        )),
        _safe(seoul.get_cultural_events(current_user.gu_name or "")),
        _safe(seoul.get_living_population(current_user.dong_name or "", current_user.gu_name or "")),
        _safe(social.get_message(current_user.dong_name or "", current_user.business_type or "")),
        _safe(seoul.get_business_openclose(
            current_user.gu_name or "",
            current_user.business_type or "",
        )),
        _safe(seoul.get_commercial_change_index(
            current_user.gu_name or "",
            current_user.dong_name or "",
        )),
    )

    matched = matched or []
    total_amount = sum(s.get("max_amount", 0) for s in matched if s.get("max_amount"))
    upcoming_events = (events or [])[:3]
    population_trend = pop_data

    # 쿠폰 통계
    stmt = select(
        func.count(CouponTemplate.id),
        func.coalesce(func.sum(CouponTemplate.scan_count), 0),
    ).where(CouponTemplate.user_id == current_user.id)
    result = await db.execute(stmt)
    coupon_row = result.one()

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

    # 위험도 추이 (최근 30일)
    stmt = select(
        DailyAction.date, DailyAction.risk_score
    ).where(
        DailyAction.user_id == current_user.id,
        DailyAction.date >= today - timedelta(days=30),
    ).order_by(DailyAction.date.asc())
    result = await db.execute(stmt)
    risk_history = result.all()
    risk_trend = [{"date": str(r.date), "score": r.risk_score} for r in risk_history]
    previous_scores = [r.risk_score for r in risk_history if r.risk_score is not None]

    # 복합 위험도 산출
    engine = RiskScoreEngine()
    risk_result = engine.compute(
        sales_data=sales_data,
        population_data=pop_data,
        competition_data=competition_data,
        change_index_data=change_index_data,
        subsidy_matches=matched,
        action_completion_rate=completion_rate,
        user_created_at=current_user.created_at.date() if current_user.created_at else None,
        previous_scores=previous_scores,
    )

    return {
        "user": {
            "nickname": current_user.nickname,
            "business_name": current_user.business_name,
            "plan_tier": current_user.plan_tier,
        },
        "risk_score": risk_result.composite_score,
        "risk_factors": [f.to_dict() for f in risk_result.factors],
        "risk_trend": risk_trend,
        "trend_direction": risk_result.trend_direction,
        "today_action": today_action,
        "subsidy_matches": matched,
        "total_potential_amount": total_amount,
        "loss_message": generate_loss_message(total_amount),
        "upcoming_events": upcoming_events,
        "population_trend": population_trend,
        "social_proof": social_proof,
        "coupon_stats": {
            "total_created": coupon_row[0],
            "total_scanned": coupon_row[1],
        },
        "action_completion_rate": round(completion_rate, 2),
    }
