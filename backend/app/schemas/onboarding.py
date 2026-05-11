from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


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
    verification_token: Optional[str] = None  # 검증 성공 시 발급되는 토큰


class KakaoLocalSearchResult(BaseModel):
    place_name: str
    address_name: str
    road_address_name: Optional[str] = None
    category_name: str
    x: str  # 경도 (lng)
    y: str  # 위도 (lat)
    phone: Optional[str] = None


class CompleteOnboardingRequest(BaseModel):
    business_number: str = Field(..., min_length=10, max_length=10, pattern=r"^\d{10}$")
    verification_token: str = Field(..., description="사업자 검증 시 발급받은 토큰")
    business_name: str = Field(..., min_length=1, max_length=200)
    business_type: str = Field(..., min_length=1, max_length=100)
    industry_slug: Optional[str] = Field(None, max_length=64, description="업종 지식팩 pack id (피커에서 선택, 없으면 서버가 분류)")
    address: str = Field(..., min_length=1, max_length=500)
    dong_name: str = Field("", max_length=50)
    gu_name: str = Field("", max_length=50)
    lat: float = Field(..., ge=33.0, le=39.0)  # 한국 위도 범위
    lng: float = Field(..., ge=124.0, le=132.0)  # 한국 경도 범위
    business_start_date: Optional[date] = Field(None, description="가게 개점일 (영업기간 산정)")


class CompleteOnboardingResponse(BaseModel):
    success: bool
    message: str
    subsidy_count: int = 0
    risk_score: float = 0.0


class UpdateProfileRequest(BaseModel):
    """온보딩 완료 후 가게 정보 일부 수정 (업종/개점일). 사업자번호 재검증 없음."""
    industry_slug: Optional[str] = Field(None, max_length=64, description="업종 지식팩 pack id (피커 선택)")
    business_type: Optional[str] = Field(None, min_length=1, max_length=100, description="업종명 (raw — 정규화는 서버가)")
    business_start_date: Optional[date] = Field(None, description="가게 개점일")


class UpdateProfileResponse(BaseModel):
    business_type: Optional[str] = None
    industry_slug: Optional[str] = None
    industry_name: Optional[str] = None
    business_start_date: Optional[date] = None
    message: str = "저장됐어요."
