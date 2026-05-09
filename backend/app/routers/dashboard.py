"""
대시보드 라우터
- GET /dashboard: 메인 대시보드 데이터 (집계 + 복합 위험도)

성능 패턴:
- Phase A: DB 쿼리 (짧은 로컬 세션 → 즉시 close)
- Phase B: 외부 API 병렬 호출 (DB 커넥션 점유 없음)
- Phase C: 응답 조립
- 목적: Seoul API fanout 동안 pool 커넥션을 점유하지 않도록.
"""
import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, case
from datetime import date, timedelta

from app.database import async_session_factory
from app.utils.auth import get_current_user
from app.models import User, DailyAction, CouponTemplate
from app.services.rag_service import RAGService
from app.services.seoul_api_service import SeoulAPIService
from app.services.social_proof_service import SocialProofService
from app.services.risk_score_engine import RiskScoreEngine
from app.utils.loss_framing import generate_loss_message

router = APIRouter()


async def _safe(coro):
    try:
        return await coro
    except Exception:
        return None


@router.get("")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
):
    """메인 대시보드 집계 데이터 + 복합 위험도 분석."""
    if not current_user.onboarding_completed:
        raise HTTPException(status_code=400, detail="온보딩을 먼저 완료해주세요.")

    today = date.today()
    gu = current_user.gu_name or ""
    dong = current_user.dong_name or ""
    btype = current_user.business_type or ""

    # ============ Phase A: DB-bound queries (짧은 로컬 세션) ============
    async with async_session_factory() as db:
        # 오늘의 액션
        today_action = (await db.execute(
            select(DailyAction).where(
                DailyAction.user_id == current_user.id,
                DailyAction.date == today,
            )
        )).scalar_one_or_none()

        # 쿠폰 통계
        coupon_row = (await db.execute(
            select(
                func.count(CouponTemplate.id),
                func.coalesce(func.sum(CouponTemplate.scan_count), 0),
            ).where(CouponTemplate.user_id == current_user.id)
        )).one()

        # 액션 완료율 (최근 30일)
        action_row = (await db.execute(
            select(
                func.count(DailyAction.id),
                func.sum(case((DailyAction.is_completed == True, 1), else_=0)),
            ).where(
                DailyAction.user_id == current_user.id,
                DailyAction.date >= today - timedelta(days=30),
            )
        )).one()

        # 위험도 추이 (최근 30일)
        risk_history = (await db.execute(
            select(DailyAction.date, DailyAction.risk_score).where(
                DailyAction.user_id == current_user.id,
                DailyAction.date >= today - timedelta(days=30),
            ).order_by(DailyAction.date.asc())
        )).all()

        # 쿠폰 스캔 delta (최근 7일 vs 그 이전 7일)
        week_ago = today - timedelta(days=7)
        two_weeks_ago = today - timedelta(days=14)
        scan_recent = (await db.execute(
            select(func.coalesce(func.sum(CouponTemplate.scan_count), 0)).where(
                CouponTemplate.user_id == current_user.id,
                CouponTemplate.created_at >= week_ago,
            )
        )).scalar() or 0
        scan_prev = (await db.execute(
            select(func.coalesce(func.sum(CouponTemplate.scan_count), 0)).where(
                CouponTemplate.user_id == current_user.id,
                CouponTemplate.created_at >= two_weeks_ago,
                CouponTemplate.created_at < week_ago,
            )
        )).scalar() or 0

        # Peer percentile 입력 (k ≥ 10 ADR-002)
        peer_row = None
        if btype:
            peer_row = (await db.execute(
                select(
                    func.avg(DailyAction.risk_score).label("avg_score"),
                    func.count(func.distinct(DailyAction.user_id)).label("user_count"),
                )
                .join(User, User.id == DailyAction.user_id)
                .where(
                    User.business_type == btype,
                    User.id != current_user.id,
                    DailyAction.date >= today - timedelta(days=14),
                    DailyAction.risk_score.isnot(None),
                )
            )).one()

        # RAG 매칭 + Social proof (DB 사용)
        rag = RAGService()
        social = SocialProofService(db)

        matched, social_proof = await asyncio.gather(
            _safe(rag.search_subsidies_filtered(
                db=db,
                gu_name=gu,
                business_type=btype,
                top_k=3,
                user_id=current_user.id,
            )),
            _safe(social.get_message(dong, btype)),
        )
    # === DB 세션 close. 커넥션이 pool로 반납됨. ===

    # ============ Phase B: 외부 API 병렬 호출 (DB 점유 없음) ============
    seoul = SeoulAPIService()
    (sales_data, events, pop_data,
     competition_data, change_index_data) = await asyncio.gather(
        _safe(seoul.get_commercial_sales(gu, dong, btype)),
        _safe(seoul.get_cultural_events(gu)),
        _safe(seoul.get_living_population(dong, gu)),
        _safe(seoul.get_business_openclose(gu, btype)),
        _safe(seoul.get_commercial_change_index(gu, dong)),
    )

    # ============ Phase C: 응답 조립 ============
    matched = matched or []
    total_amount = sum(s.get("max_amount", 0) for s in matched if s.get("max_amount"))
    upcoming_events = (events or [])[:3]

    total_actions = action_row[0] or 0
    completed_actions = action_row[1] or 0
    completion_rate = completed_actions / total_actions if total_actions > 0 else 0.0

    risk_trend = [{"date": str(r.date), "score": r.risk_score} for r in risk_history]
    previous_scores = [r.risk_score for r in risk_history if r.risk_score is not None]

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

    # 누적 손실 카운터
    unclaimed_amount_won = (total_amount or 0) * 10_000
    daily_loss_won = unclaimed_amount_won // 365 if unclaimed_amount_won > 0 else 0
    op_start = current_user.business_start_date or (current_user.created_at.date() if current_user.created_at else today)
    days_since_signup = max(1, (today - op_start).days)
    accumulated_loss_won = daily_loss_won * days_since_signup

    # Risk delta
    risk_score_delta = None
    if len(previous_scores) >= 2:
        risk_score_delta = round(previous_scores[-1] - previous_scores[-2], 3)

    # Coupon scan delta
    if scan_prev > 0:
        coupon_scan_delta_pct = round((scan_recent - scan_prev) / scan_prev * 100, 1)
    elif scan_recent > 0:
        coupon_scan_delta_pct = 100.0
    else:
        coupon_scan_delta_pct = None

    # Peer percentile
    peer_percentile = None
    peer_sample = 0
    if peer_row and peer_row.user_count and peer_row.user_count >= 10:
        peer_avg = float(peer_row.avg_score)
        peer_sample = int(peer_row.user_count)
        diff = peer_avg - risk_result.composite_score
        raw = 50 - diff * 100
        peer_percentile = max(1, min(99, round(raw)))

    # 매칭 사유 칩
    def _match_reasons(item: dict) -> list[str]:
        chips: list[str] = []
        if btype:
            chips.append(f"업종 일치 · {btype}")
        if gu:
            chips.append(f"{gu} 신청 가능")
        days = item.get("days_until_deadline")
        if days is not None and days <= 14:
            chips.append(f"마감 D-{days} 임박")
        if (item.get("max_amount") or 0) >= 500:
            chips.append(f"고액 {item['max_amount']}만원")
        return chips

    enriched_matched = [{**m, "match_reasons": _match_reasons(m)} for m in matched]

    # 다음 액션 미리보기
    next_action_preview = None
    if len(enriched_matched) >= 2:
        nxt = enriched_matched[1]
        next_action_preview = {
            "title": f"내일 후보: {nxt['title']}",
            "subtitle": f"{nxt.get('organization', '')} · 최대 {nxt.get('max_amount') or 0}만원",
            "cta_type": "apply_subsidy",
        }

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
        "subsidy_matches": enriched_matched,
        "total_potential_amount": total_amount,
        "loss_message": generate_loss_message(total_amount),
        "loss_counter": {
            "unclaimed_amount_won": unclaimed_amount_won,
            "daily_loss_won": daily_loss_won,
            "accumulated_loss_won": accumulated_loss_won,
            "days_since_signup": days_since_signup,
        },
        "deltas": {
            "risk_score_delta": risk_score_delta,
            "coupon_scan_delta_pct": coupon_scan_delta_pct,
        },
        "peer_percentile": peer_percentile,
        "peer_sample": peer_sample,
        "next_action_preview": next_action_preview,
        "upcoming_events": upcoming_events,
        "population_trend": pop_data,
        "social_proof": social_proof,
        "coupon_stats": {
            "total_created": coupon_row[0],
            "total_scanned": coupon_row[1],
        },
        "action_completion_rate": round(completion_rate, 2),
    }
