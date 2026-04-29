"""subsidy_interactions 테이블 추가 (ICP Learner 학습 신호)

Revision ID: 005_subsidy_interactions
Revises: 004_insight_cache
Create Date: 2026-04-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "005_subsidy_interactions"
down_revision = "004_insight_cache"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "subsidy_interactions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subsidy_id", UUID(as_uuid=True), sa.ForeignKey("subsidies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("signal_type", sa.String(20), nullable=False),
        sa.Column("weight", sa.Float, nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "idx_subsidy_interactions_user_created",
        "subsidy_interactions",
        ["user_id", "created_at"],
    )
    op.create_index(
        "idx_subsidy_interactions_subsidy",
        "subsidy_interactions",
        ["subsidy_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_subsidy_interactions_subsidy", table_name="subsidy_interactions")
    op.drop_index("idx_subsidy_interactions_user_created", table_name="subsidy_interactions")
    op.drop_table("subsidy_interactions")
