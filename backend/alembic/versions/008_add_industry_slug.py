"""users.industry_slug 추가 (업종 지식팩 매핑, P1)

Revision ID: 008_industry_slug
Revises: 7314edff5bc1
Create Date: 2026-05-11

업그레이드 후 기존 행 채우기:  python -m scripts.backfill_industry  (backend/ 에서)
"""
from alembic import op
import sqlalchemy as sa


revision = "008_industry_slug"
down_revision = "7314edff5bc1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("industry_slug", sa.String(length=64), nullable=True))
    op.create_index("ix_users_industry_slug", "users", ["industry_slug"])


def downgrade() -> None:
    op.drop_index("ix_users_industry_slug", table_name="users")
    op.drop_column("users", "industry_slug")
