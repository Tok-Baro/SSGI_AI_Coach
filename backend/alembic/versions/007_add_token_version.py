"""users.token_version 추가 (JWT refresh 회전 시 구 토큰 무효화)

Revision ID: 007_token_version
Revises: 006_business_start_date
Create Date: 2026-05-07
"""
from alembic import op
import sqlalchemy as sa


revision = "007_token_version"
down_revision = "006_business_start_date"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("users", "token_version")
