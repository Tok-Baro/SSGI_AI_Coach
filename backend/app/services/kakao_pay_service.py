"""카카오페이 결제 서비스 — Ready / Approve / Cancel.

테스트 환경:
- cid: TC0ONETIME (일회성 / 정기는 TCSUBSCRIP)
- Admin Key 필요 (카카오 디벨로퍼스 → 앱 설정 → 일반)
- 실 정산 X — 테스트 결제 화면만 띄움

API:
- POST https://kapi.kakao.com/v1/payment/ready    → 결제 준비 (tid 발급)
- POST https://kapi.kakao.com/v1/payment/approve  → 사용자 승인 후 결제 확정
- POST https://kapi.kakao.com/v1/payment/cancel   → 환불

레퍼런스: https://developers.kakao.com/docs/latest/ko/kakaopay/single-payment
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

KAKAO_PAY_BASE = "https://kapi.kakao.com/v1/payment"


class KakaoPayError(Exception):
    """카카오페이 API 오류 (사장님 친화 메시지로 변환)."""


def _headers() -> dict[str, str]:
    """공식 카카오페이 인증 헤더."""
    if not settings.kakao_admin_key:
        raise KakaoPayError("카카오페이 결제 준비 중이에요. 잠시 후 다시 시도해 주세요.")
    return {
        "Authorization": f"KakaoAK {settings.kakao_admin_key}",
        "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
    }


async def ready_payment(
    *,
    user_id: str,
    item_name: str = "SSGI Pro 1개월",
    quantity: int = 1,
    total_amount: int = 9900,
    tax_free_amount: int = 0,
) -> dict[str, Any]:
    """결제 준비 — 카카오페이에 tid 요청.

    Returns:
        {
            "tid": "T1234567890",
            "next_redirect_pc_url": "https://...",
            "next_redirect_mobile_url": "https://...",
            "next_redirect_app_url": "...",
            "android_app_scheme": "...",
            "ios_app_scheme": "...",
            "created_at": "2026-05-11T10:00:00",
            "partner_order_id": "ssgi-...",
            "partner_user_id": "user-uuid",
        }
    """
    partner_order_id = f"ssgi-{uuid.uuid4().hex[:12]}"
    partner_user_id = str(user_id)

    payload = {
        "cid": settings.kakao_pay_cid,
        "partner_order_id": partner_order_id,
        "partner_user_id": partner_user_id,
        "item_name": item_name,
        "quantity": quantity,
        "total_amount": total_amount,
        "tax_free_amount": tax_free_amount,
        "approval_url": f"{settings.kakao_pay_approval_url}?order={partner_order_id}",
        "cancel_url": settings.kakao_pay_cancel_url,
        "fail_url": settings.kakao_pay_fail_url,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            res = await client.post(
                f"{KAKAO_PAY_BASE}/ready",
                headers=_headers(),
                data=payload,
            )
        except httpx.HTTPError as exc:
            logger.warning("카카오페이 ready 통신 오류: %s", exc)
            raise KakaoPayError("카카오페이 통신이 잠시 불안정해요. 다시 시도해 주세요.")

    if res.status_code != 200:
        logger.warning("카카오페이 ready 실패: %s %s", res.status_code, res.text)
        raise KakaoPayError("결제 준비가 막혔어요. 다시 시도해 주세요.")

    data = res.json()
    data["partner_order_id"] = partner_order_id
    data["partner_user_id"] = partner_user_id
    return data


async def approve_payment(
    *,
    tid: str,
    partner_order_id: str,
    partner_user_id: str,
    pg_token: str,
) -> dict[str, Any]:
    """사용자 결제 승인 후 확정.

    Returns:
        {
            "aid": "A1234...",
            "tid": "T1234...",
            "cid": "TC0ONETIME",
            "partner_order_id": "ssgi-...",
            "partner_user_id": "user-uuid",
            "payment_method_type": "MONEY" | "CARD",
            "amount": {"total": 9900, ...},
            "approved_at": "2026-05-11T10:01:00",
            ...
        }
    """
    payload = {
        "cid": settings.kakao_pay_cid,
        "tid": tid,
        "partner_order_id": partner_order_id,
        "partner_user_id": partner_user_id,
        "pg_token": pg_token,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            res = await client.post(
                f"{KAKAO_PAY_BASE}/approve",
                headers=_headers(),
                data=payload,
            )
        except httpx.HTTPError as exc:
            logger.warning("카카오페이 approve 통신 오류: %s", exc)
            raise KakaoPayError("승인 통신이 잠시 불안정해요.")

    if res.status_code != 200:
        logger.warning("카카오페이 approve 실패: %s %s", res.status_code, res.text)
        raise KakaoPayError("결제 승인이 막혔어요. 다시 시도해 주세요.")

    return res.json()


async def cancel_payment(
    *,
    tid: str,
    cancel_amount: int,
    cancel_tax_free_amount: int = 0,
) -> dict[str, Any]:
    """환불."""
    payload = {
        "cid": settings.kakao_pay_cid,
        "tid": tid,
        "cancel_amount": cancel_amount,
        "cancel_tax_free_amount": cancel_tax_free_amount,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.post(
            f"{KAKAO_PAY_BASE}/cancel",
            headers=_headers(),
            data=payload,
        )
    if res.status_code != 200:
        logger.warning("카카오페이 cancel 실패: %s %s", res.status_code, res.text)
        raise KakaoPayError("환불 처리가 막혔어요. 잠시 후 다시 시도해 주세요.")
    return res.json()
