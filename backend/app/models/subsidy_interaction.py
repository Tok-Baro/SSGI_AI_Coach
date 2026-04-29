"""사용자 ↔ 지원사업 상호작용 신호 (ICP 학습용).

ericosiu/ai-marketing-skills의 ICP Learner 패턴 — 사용자가 어떤 보조금에 관심을 보였는지
누적 신호로 학습하여 매칭 정확도를 자동 개선.

signal_type:
- view  : 매칭 목록에 노출됨 (약한 신호, weight=0.2)
- click : 사용자가 카드를 탭/클릭함 (중간 신호, weight=1.0)
- draft : 사업계획서 초안을 생성함 (강한 신호, weight=3.0)
- apply : 외부 신청 페이지로 이동함 (가장 강한 신호, weight=5.0)
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class SubsidyInteraction(Base):
    __tablename__ = "subsidy_interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subsidy_id = Column(UUID(as_uuid=True), ForeignKey("subsidies.id", ondelete="CASCADE"), nullable=False)
    signal_type = Column(String(20), nullable=False)
    weight = Column(Float, nullable=False, default=1.0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_subsidy_interactions_user_created", "user_id", "created_at"),
        Index("idx_subsidy_interactions_subsidy", "subsidy_id"),
    )
