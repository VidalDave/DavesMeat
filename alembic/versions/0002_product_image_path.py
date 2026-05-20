"""add product uploaded image path

Revision ID: 0002_product_image_path
Revises: 0001_initial
Create Date: 2026-05-20
"""
from alembic import op


revision = "0002_product_image_path"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS image_path TEXT")


def downgrade() -> None:
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS image_path")
