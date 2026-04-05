"""QR 쿠폰 생성 서비스."""
import base64
import io
from datetime import date, timedelta
from typing import Optional

import qrcode
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.coupon import CouponTemplate


class CouponService:
    async def create_coupon(
        self,
        db: AsyncSession,
        user: User,
        title: str,
        discount_type: str,
        discount_value: Optional[int],
        description: Optional[str],
        valid_days: int = 7,
    ) -> CouponTemplate:
        """QR 쿠폰 생성 + base64 이미지 반환."""
        import uuid

        coupon_id = uuid.uuid4()
        app_url = "https://ai-coach.vercel.app"  # TODO: 환경변수로
        qr_url = f"{app_url}/coupons/{coupon_id}"

        # QR 코드 생성
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # PNG → base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        qr_image_base64 = f"data:image/png;base64,{b64}"

        # 유효기간 계산
        valid_from = date.today()
        valid_until = valid_from + timedelta(days=valid_days)

        coupon = CouponTemplate(
            id=coupon_id,
            user_id=user.id,
            title=title,
            discount_type=discount_type,
            discount_value=discount_value,
            description=description,
            valid_days=valid_days,
            valid_from=valid_from,
            valid_until=valid_until,
            qr_data=qr_url,
            qr_image_base64=qr_image_base64,
        )
        db.add(coupon)
        await db.flush()
        return coupon
