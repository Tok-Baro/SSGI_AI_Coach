from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserResponse(BaseModel):
    id: UUID
    kakao_id: int
    email: Optional[str] = None
    nickname: str
    profile_image_url: Optional[str] = None
    business_number: Optional[str] = None
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    address: Optional[str] = None
    dong_name: Optional[str] = None
    gu_name: Optional[str] = None
    plan_tier: str
    onboarding_completed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
