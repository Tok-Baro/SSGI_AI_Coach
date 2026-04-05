import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Date, Boolean, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from app.database import Base


class Subsidy(Base):
    __tablename__ = "subsidies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    organization = Column(String(200), nullable=False)
    deadline = Column(Date, nullable=True)
    max_amount = Column(Integer, nullable=True)  # 만원 단위
    target_business_types = Column(ARRAY(Text), nullable=True)
    target_regions = Column(ARRAY(Text), nullable=True)
    eligibility_summary = Column(Text, nullable=True)
    description = Column(Text, nullable=False)
    application_url = Column(String(500), nullable=True)
    embedding_id = Column(String(100), nullable=True)
    source = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
