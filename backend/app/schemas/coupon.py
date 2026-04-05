from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import date


class CreateCouponRequest(BaseModel):
    title: str
    discount_type: str  # percent | fixed | bogo | free_item
    discount_value: Optional[int] = None
    description: Optional[str] = None
    valid_days: int = 7


class CouponResponse(BaseModel):
    id: UUID
    title: str
    discount_type: str
    discount_value: Optional[int] = None
    description: Optional[str] = None
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    qr_data: str
    qr_image_base64: str
    download_count: int
    scan_count: int
    is_active: bool

    class Config:
        from_attributes = True
