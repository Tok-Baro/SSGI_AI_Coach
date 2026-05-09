"""users.business_start_date 추가 (가게 개점일, 영업기간 정확화)

Revision ID: 006_business_start_date
Revises: 005_subsidy_interactions
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa


revision = "006_business_start_date"
down_revision = "005_subsidy_interactions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("business_start_date", sa.Date(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "business_start_date")
