"""
쿠폰 라우터
- POST /coupons/create: QR 쿠폰 생성
- GET  /coupons: 내 쿠폰 목록
- GET  /coupons/{id}: 쿠폰 상세
- POST /coupons/{id}/scan: 스캔 카운트 증가
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from datetime import date
from typing import List
from collections import defaultdict
import time

from app.database import get_db
from app.schemas.coupon import CreateCouponRequest, CouponResponse
from app.services.coupon_service import CouponService
from app.utils.auth import get_current_user
from app.models import User, CouponTemplate

router = APIRouter()

# 스캔 rate limiting: IP당 쿠폰당 1분에 5회 제한
_scan_tracker: dict[str, list[float]] = defaultdict(list)
SCAN_RATE_LIMIT = 5
SCAN_RATE_WINDOW = 60  # seconds


@router.post("/create", response_model=CouponResponse)
async def create_coupon(
    req: CreateCouponRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """QR 쿠폰 생성. Free 플랜: 월 3개 제한."""
    if current_user.plan_tier == "free":
        stmt = select(func.count(CouponTemplate.id)).where(
            CouponTemplate.user_id == current_user.id,
            func.extract("month", CouponTemplate.created_at) == date.today().month,
            func.extract("year", CouponTemplate.created_at) == date.today().year,
        )
        result = await db.execute(stmt)
        count = result.scalar()
        if count >= 3:
            raise HTTPException(
                status_code=403,
                detail="무료 플랜은 월 3개까지 쿠폰을 만들 수 있습니다. 프로 플랜으로 업그레이드하세요.",
            )

    coupon_service = CouponService()
    coupon = await coupon_service.create_coupon(
        db=db,
        user=current_user,
        title=req.title,
        discount_type=req.discount_type,
        discount_value=req.discount_value,
        description=req.description,
        valid_days=req.valid_days,
    )

    return CouponResponse.model_validate(coupon)


@router.get("", response_model=List[CouponResponse])
async def list_coupons(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """내 쿠폰 목록."""
    stmt = (
        select(CouponTemplate)
        .where(CouponTemplate.user_id == current_user.id)
        .order_by(CouponTemplate.created_at.desc())
    )
    result = await db.execute(stmt)
    coupons = result.scalars().all()
    return [CouponResponse.model_validate(c) for c in coupons]


@router.get("/{coupon_id}", response_model=CouponResponse)
async def get_coupon(coupon_id: UUID, db: AsyncSession = Depends(get_db)):
    """쿠폰 상세 (QR 포함). 인증 불필요."""
    stmt = select(CouponTemplate).where(CouponTemplate.id == coupon_id)
    result = await db.execute(stmt)
    coupon = result.scalar_one_or_none()
    if not coupon:
        raise HTTPException(status_code=404, detail="쿠폰을 찾을 수 없습니다.")
    return CouponResponse.model_validate(coupon)


@router.post("/{coupon_id}/scan")
async def scan_coupon(coupon_id: UUID, request: Request, db: AsyncSession = Depends(get_db)):
    """쿠폰 스캔 카운트 증가. 인증 불필요. IP 기반 rate limit 적용."""
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"{client_ip}:{coupon_id}"
    now = time.time()

    # 오래된 기록 제거 + 현재 윈도우 내 요청 수 확인
    _scan_tracker[rate_key] = [t for t in _scan_tracker[rate_key] if now - t < SCAN_RATE_WINDOW]
    if len(_scan_tracker[rate_key]) >= SCAN_RATE_LIMIT:
        raise HTTPException(status_code=429, detail="너무 많은 스캔 요청입니다. 잠시 후 다시 시도하세요.")
    _scan_tracker[rate_key].append(now)

    stmt = select(CouponTemplate).where(CouponTemplate.id == coupon_id)
    result = await db.execute(stmt)
    coupon = result.scalar_one_or_none()
    if not coupon:
        raise HTTPException(status_code=404, detail="쿠폰을 찾을 수 없습니다.")
    coupon.scan_count += 1
    await db.flush()
    return {"success": True, "scan_count": coupon.scan_count}
