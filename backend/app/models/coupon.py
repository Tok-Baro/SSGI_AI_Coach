import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Date, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class CouponTemplate(Base):
    __tablename__ = "coupon_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    discount_type = Column(String(20), nullable=False)  # percent | fixed | bogo | free_item
    discount_value = Column(Integer, nullable=True)
    description = Column(String(500), nullable=True)
    valid_days = Column(Integer, default=7)
    valid_from = Column(Date, nullable=True)
    valid_until = Column(Date, nullable=True)
    qr_data = Column(Text, nullable=False)
    qr_image_base64 = Column(Text, nullable=True)
    download_count = Column(Integer, default=0)
    scan_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="coupon_templates")
