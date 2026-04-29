import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, Boolean, Date, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class DailyAction(Base):
    __tablename__ = "daily_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    action_type = Column(String(50), nullable=False)  # subsidy | event | coupon | competitor | population
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=False)
    risk_score = Column(Float, default=0.0)
    data_source = Column(String(100), nullable=True)
    cta_type = Column(String(50), nullable=True)  # create_coupon | apply_subsidy | view_detail
    cta_payload = Column(JSONB, nullable=True)
    risk_factors = Column(JSONB, nullable=True)  # 위험도 요인 분석 결과
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="daily_actions")

    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_daily_actions_user_date"),
    )
