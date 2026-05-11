"""사장님 Pro 구독 모델 — 카카오페이 결제 (테스트/실 운영 공용)."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Subscription(Base):
    """Pro 구독 — 1 user : N subscriptions (재구독 이력 추적)."""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # 카카오페이 식별자
    tid = Column(String(40), nullable=True, index=True)  # 카카오 결제 고유번호
    cid = Column(String(20), nullable=False, default="TC0ONETIME")  # 가맹점 코드 (테스트=TC0ONETIME)
    partner_order_id = Column(String(64), nullable=False, unique=True)  # 우리 주문번호
    partner_user_id = Column(String(64), nullable=False)  # 카카오 사용자 식별

    # 결제 상태
    status = Column(String(20), nullable=False, default="ready", index=True)
    # ready / approved / canceled / failed / refunded

    # 금액
    item_name = Column(String(100), nullable=False, default="SSGI Pro 1개월")
    quantity = Column(Integer, nullable=False, default=1)
    total_amount = Column(BigInteger, nullable=False, default=9900)  # 원

    # 결제 시점
    ready_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    canceled_at = Column(DateTime, nullable=True)
    refunded_at = Column(DateTime, nullable=True)

    # 구독 기간
    started_at = Column(DateTime, nullable=True)
    expired_at = Column(DateTime, nullable=True)

    # 환경 (test vs production)
    environment = Column(String(20), nullable=False, default="test", index=True)

    # 카카오 raw response (디버그용)
    raw_response = Column(String(2000), nullable=True)

    user = relationship("User", back_populates="subscriptions")

    __table_args__ = (
        Index("ix_subscriptions_user_status", "user_id", "status"),
    )
