"""Initial schema - all 5 tables

Revision ID: 001_initial
Revises:
Create Date: 2026-04-06
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("kakao_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("nickname", sa.String(100), nullable=False),
        sa.Column("profile_image_url", sa.String(500), nullable=True),
        sa.Column("business_number", sa.String(10), nullable=True),
        sa.Column("business_name", sa.String(200), nullable=True),
        sa.Column("business_type", sa.String(100), nullable=True),
        sa.Column("business_category", sa.String(100), nullable=True),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("dong_name", sa.String(50), nullable=True),
        sa.Column("gu_name", sa.String(50), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("plan_tier", sa.String(10), nullable=False, server_default="free"),
        sa.Column("onboarding_completed", sa.Boolean(), server_default="false"),
        sa.Column("fcm_token", sa.String(500), nullable=True),
        sa.Column("kakao_access_token", sa.String(500), nullable=True),
        sa.Column("kakao_refresh_token", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("idx_users_kakao_id", "users", ["kakao_id"])
    op.create_index("idx_users_dong_name", "users", ["dong_name"])

    # daily_actions
    op.create_table(
        "daily_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("risk_score", sa.Float(), server_default="0.0"),
        sa.Column("data_source", sa.String(100), nullable=True),
        sa.Column("cta_type", sa.String(50), nullable=True),
        sa.Column("cta_payload", postgresql.JSONB(), nullable=True),
        sa.Column("is_completed", sa.Boolean(), server_default="false"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "date", name="uq_daily_actions_user_date"),
    )
    op.create_index("idx_daily_actions_user_date", "daily_actions", ["user_id", "date"])

    # subsidies
    op.create_table(
        "subsidies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("organization", sa.String(200), nullable=False),
        sa.Column("deadline", sa.Date(), nullable=True),
        sa.Column("max_amount", sa.Integer(), nullable=True),
        sa.Column("target_business_types", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("target_regions", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("eligibility_summary", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("application_url", sa.String(500), nullable=True),
        sa.Column("embedding_id", sa.String(100), nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # coupon_templates
    op.create_table(
        "coupon_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("discount_type", sa.String(20), nullable=False),
        sa.Column("discount_value", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("valid_days", sa.Integer(), server_default="7"),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("qr_data", sa.Text(), nullable=False),
        sa.Column("qr_image_base64", sa.Text(), nullable=True),
        sa.Column("download_count", sa.Integer(), server_default="0"),
        sa.Column("scan_count", sa.Integer(), server_default="0"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # notification_log
    op.create_table(
        "notification_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("message_type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(300), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("notification_log")
    op.drop_table("coupon_templates")
    op.drop_table("subsidies")
    op.drop_table("daily_actions")
    op.drop_table("users")
