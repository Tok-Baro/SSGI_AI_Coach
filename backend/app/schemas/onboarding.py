from pydantic import BaseModel, Field
from typing import Optional


class VerifyBusinessRequest(BaseModel):
    business_number: str = Field(
        ..., min_length=10, max_length=10, pattern=r"^\d{10}$",
        description="사업자등록번호 10자리 숫자",
    )


class VerifyBusinessResponse(BaseModel):
    is_valid: bool
    business_status: str  # "계속사업자" | "휴업자" | "폐업자" | "확인불가"
    business_name: Optional[str] = None
    tax_type: Optional[str] = None


class KakaoLocalSearchResult(BaseModel):
    place_name: str
    address_name: str
    road_address_name: Optional[str] = None
    category_name: str
    x: str  # 경도 (lng)
    y: str  # 위도 (lat)
    phone: Optional[str] = None


class CompleteOnboardingRequest(BaseModel):
    business_number: str = Field(..., min_length=10, max_length=10)
    business_name: str
    business_type: str
    address: str
    dong_name: str
    gu_name: str
    lat: float
    lng: float


class CompleteOnboardingResponse(BaseModel):
    success: bool
    message: str
    subsidy_count: int = 0
    risk_score: float = 0.0
