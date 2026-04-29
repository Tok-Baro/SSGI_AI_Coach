"""인사이트 캐시 테이블 추가

Revision ID: 004_insight_cache
Revises: 003_risk_factors
Create Date: 2026-04-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "004_insight_cache"
down_revision = "003_risk_factors"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "insight_cache",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("insight_type", sa.String(50), nullable=False),
        sa.Column("week_key", sa.String(10), nullable=False),
        sa.Column("data", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("user_id", "insight_type", "week_key", name="uq_insight_cache_user_type_week"),
    )


def downgrade() -> None:
    op.drop_table("insight_cache")
