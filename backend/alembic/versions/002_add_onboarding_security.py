"""사업자 등록 보안 강화: 시도 횟수 + 검증 시각 + unique 제약

Revision ID: 002_security
Revises: 001_initial
Create Date: 2026-04-07
"""
from alembic import op
import sqlalchemy as sa

revision = "002_security"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 온보딩 시도 횟수 (브루트포스 방지)
    op.add_column("users", sa.Column("onboarding_attempts", sa.Integer(), nullable=False, server_default="0"))
    # 사업자 검증 시각
    op.add_column("users", sa.Column("business_verified_at", sa.DateTime(timezone=True), nullable=True))
    # 사업자번호 unique + index (중복 등록 방지)
    op.create_index("ix_users_business_number", "users", ["business_number"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_business_number", table_name="users")
    op.drop_column("users", "business_verified_at")
    op.drop_column("users", "onboarding_attempts")
