"""subsidies.category_tags 추가 (지원사업 카테고리 태그, P2c — 업종팩 매칭 부스트용)

Revision ID: 009_subsidy_category_tags
Revises: 008_industry_slug
Create Date: 2026-05-11

업그레이드 후 시드 재적재 시 태그가 채워짐:  python -m scripts.seed_subsidies  (backend/ 에서)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "009_subsidy_category_tags"
down_revision = "008_industry_slug"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("subsidies", sa.Column("category_tags", postgresql.ARRAY(sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column("subsidies", "category_tags")
