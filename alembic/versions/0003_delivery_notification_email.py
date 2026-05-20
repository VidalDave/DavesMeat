"""add delivery notification email setting

Revision ID: 0003_delivery_notification_email
Revises: 0002_product_image_path
Create Date: 2026-05-20
"""
from alembic import op


revision = "0003_delivery_notification_email"
down_revision = "0002_product_image_path"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE delivery_settings ADD COLUMN IF NOT EXISTS notification_email VARCHAR(255)")


def downgrade() -> None:
    op.execute("ALTER TABLE delivery_settings DROP COLUMN IF EXISTS notification_email")
