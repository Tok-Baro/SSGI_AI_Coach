import uuid
from datetime import datetime

from sqlalchemy import Column, String, BigInteger, Float, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kakao_id = Column(BigInteger, unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=True)
    nickname = Column(String(100), nullable=False)
    profile_image_url = Column(String(500), nullable=True)
    business_number = Column(String(10), nullable=True)
    business_name = Column(String(200), nullable=True)
    business_type = Column(String(100), nullable=True)
    business_category = Column(String(100), nullable=True)
    address = Column(String(500), nullable=True)
    dong_name = Column(String(50), nullable=True, index=True)
    gu_name = Column(String(50), nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    plan_tier = Column(String(10), default="free", nullable=False)
    onboarding_completed = Column(Boolean, default=False)
    fcm_token = Column(String(500), nullable=True)
    kakao_access_token = Column(String(500), nullable=True)
    kakao_refresh_token = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    daily_actions = relationship("DailyAction", back_populates="user", cascade="all, delete-orphan")
    coupon_templates = relationship("CouponTemplate", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("NotificationLog", back_populates="user", cascade="all, delete-orphan")
