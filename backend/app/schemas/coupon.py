from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional
from uuid import UUID
from datetime import date


DiscountType = Literal["percent", "fixed", "bogo", "free_item"]


class CreateCouponRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=80)
    discount_type: DiscountType
    discount_value: Optional[int] = Field(None, ge=0, le=10_000_000)
    description: Optional[str] = Field(None, max_length=300)
    valid_days: int = Field(7, ge=1, le=365)

    @field_validator("discount_value")
    @classmethod
    def _validate_discount(cls, v, info):
        dtype = info.data.get("discount_type")
        if dtype == "percent" and v is not None and not (1 <= v <= 100):
            raise ValueError("percent 할인은 1~100 사이여야 합니다.")
        if dtype == "fixed" and v is not None and v < 100:
            raise ValueError("fixed 할인은 최소 100원 이상이어야 합니다.")
        return v


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
