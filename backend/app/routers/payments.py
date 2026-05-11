"""카카오페이 결제 라우터.

흐름:
1. POST /payments/kakao/ready
   → 카카오페이 ready API 호출 → tid + redirect URL 받음
   → DB에 Subscription 생성 (status=ready)
   → 프론트로 next_redirect_pc_url + tid 반환

2. 사용자가 카카오페이 결제 화면에서 승인
   → 카카오가 approval_url로 redirect (with pg_token)

3. POST /payments/kakao/approve
   → tid + pg_token으로 카카오페이 approve API 호출
   → 결제 확정 → Subscription status=approved
   → 사용자 Pro 등급 활성화

4. (옵션) POST /payments/kakao/cancel — 환불

테스트 환경: cid=TC0ONETIME (sandbox). 실 정산 X.
"""
from datetime import datetime, timedelta
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, Subscription
from app.services.kakao_pay_service import (
    ready_payment,
    approve_payment,
    cancel_payment,
    KakaoPayError,
)
from app.utils.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


# ============== Schemas ==============

class ReadyResponse(BaseModel):
    tid: str
    next_redirect_pc_url: str
    next_redirect_mobile_url: str
    partner_order_id: str


class ApproveRequest(BaseModel):
    tid: str
    partner_order_id: str
    pg_token: str


class ApproveResponse(BaseModel):
    status: str
    item_name: str
    total_amount: int
    approved_at: datetime
    expired_at: Optional[datetime]


class SubscriptionStatusResponse(BaseModel):
    is_pro: bool
    status: str  # ready / approved / expired / none
    started_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None


# ============== Endpoints ==============

@router.post("/payments/kakao/ready", response_model=ReadyResponse)
async def ready(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReadyResponse:
    """결제 준비 — 사용자가 /upgrade 페이지에서 '카카오페이로 결제' 클릭 시."""
    try:
        kakao_data = await ready_payment(
            user_id=str(current_user.id),
            item_name="SSGI Pro 1개월 (테스트 결제)",
            total_amount=9900,
        )
    except KakaoPayError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    # DB에 Subscription 생성
    sub = Subscription(
        user_id=current_user.id,
        tid=kakao_data["tid"],
        partner_order_id=kakao_data["partner_order_id"],
        partner_user_id=kakao_data["partner_user_id"],
        item_name="SSGI Pro 1개월 (테스트 결제)",
        total_amount=9900,
        status="ready",
        environment="test",
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)

    return ReadyResponse(
        tid=kakao_data["tid"],
        next_redirect_pc_url=kakao_data["next_redirect_pc_url"],
        next_redirect_mobile_url=kakao_data["next_redirect_mobile_url"],
        partner_order_id=kakao_data["partner_order_id"],
    )


@router.post("/payments/kakao/approve", response_model=ApproveResponse)
async def approve(
    body: ApproveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApproveResponse:
    """결제 승인 — 사용자 카카오페이 결제 후 callback에서 호출."""
    # DB에서 Subscription 조회
    result = await db.execute(
        select(Subscription).where(
            Subscription.partner_order_id == body.partner_order_id,
            Subscription.user_id == current_user.id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="결제 내역을 찾을 수 없어요. 다시 시도해 주세요.")
    if sub.status == "approved":
        # 중복 호출 보호 (idempotency)
        return ApproveResponse(
            status="approved",
            item_name=sub.item_name,
            total_amount=sub.total_amount,
            approved_at=sub.approved_at or datetime.utcnow(),
            expired_at=sub.expired_at,
        )

    try:
        kakao_data = await approve_payment(
            tid=body.tid,
            partner_order_id=body.partner_order_id,
            partner_user_id=str(current_user.id),
            pg_token=body.pg_token,
        )
    except KakaoPayError as exc:
        sub.status = "failed"
        await db.commit()
        raise HTTPException(status_code=503, detail=str(exc))

    # 구독 활성화 (1개월)
    now = datetime.utcnow()
    sub.status = "approved"
    sub.approved_at = now
    sub.started_at = now
    sub.expired_at = now + timedelta(days=30)
    sub.raw_response = str(kakao_data)[:2000]
    await db.commit()
    await db.refresh(sub)

    return ApproveResponse(
        status="approved",
        item_name=sub.item_name,
        total_amount=sub.total_amount,
        approved_at=sub.approved_at,
        expired_at=sub.expired_at,
    )


@router.get("/payments/subscription", response_model=SubscriptionStatusResponse)
async def subscription_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionStatusResponse:
    """현재 사용자 Pro 상태 — 활성 구독 1건 조회."""
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .where(Subscription.status == "approved")
        .order_by(Subscription.approved_at.desc())
    )
    sub = result.scalars().first()
    if not sub:
        return SubscriptionStatusResponse(is_pro=False, status="none")

    is_active = sub.expired_at and sub.expired_at > datetime.utcnow()
    return SubscriptionStatusResponse(
        is_pro=is_active,
        status="approved" if is_active else "expired",
        started_at=sub.started_at,
        expired_at=sub.expired_at,
    )


@router.post("/payments/kakao/cancel")
async def cancel(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """환불 — 활성 구독 취소."""
    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .where(Subscription.status == "approved")
    )
    sub = result.scalars().first()
    if not sub:
        raise HTTPException(status_code=404, detail="환불할 구독이 없어요.")

    try:
        await cancel_payment(tid=sub.tid, cancel_amount=sub.total_amount)
    except KakaoPayError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    sub.status = "refunded"
    sub.refunded_at = datetime.utcnow()
    await db.commit()
    return {"status": "refunded"}
