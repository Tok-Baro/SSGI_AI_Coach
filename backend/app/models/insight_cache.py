"""인사이트 캐시 모델 — GPT 생성 결과를 주 단위로 캐싱."""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class InsightCache(Base):
    __tablename__ = "insight_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    insight_type = Column(String(50), nullable=False)  # "marketing" | "deep_report"
    week_key = Column(String(10), nullable=False)  # "2026-W15" 형태
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "insight_type", "week_key", name="uq_insight_cache_user_type_week"),
    )
