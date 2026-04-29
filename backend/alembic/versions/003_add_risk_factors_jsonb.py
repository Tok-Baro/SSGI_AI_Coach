"""daily_actions에 risk_factors JSONB 컬럼 추가

Revision ID: 003_risk_factors
Revises: 002_security
Create Date: 2026-04-07
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "003_risk_factors"
down_revision = "002_security"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("daily_actions", sa.Column("risk_factors", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("daily_actions", "risk_factors")
