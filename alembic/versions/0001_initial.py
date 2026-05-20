"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-20
"""
from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"])
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("weight", sa.String(length=80), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("features", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_products_id"), "products", ["id"])

    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
    )
    op.create_index(op.f("ix_locations_id"), "locations", ["id"])
    op.create_unique_constraint("uq_locations_name", "locations", ["name"])

    op.create_table(
        "delivery_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("mode", sa.String(length=30), nullable=False),
        sa.Column("allowed_weekdays", sa.String(length=30), nullable=False),
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("phone", sa.String(length=40), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("delivery_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("admin_note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
    )
    op.create_index(op.f("ix_orders_id"), "orders", ["id"])
    op.create_index(op.f("ix_orders_phone"), "orders", ["phone"])
    op.create_index(op.f("ix_orders_location_id"), "orders", ["location_id"])
    op.create_index(op.f("ix_orders_delivery_date"), "orders", ["delivery_date"])
    op.create_index(op.f("ix_orders_status"), "orders", ["status"])

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("product_name", sa.String(length=160), nullable=False),
        sa.Column("product_weight", sa.String(length=80), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"]),
    )
    op.create_index(op.f("ix_order_items_id"), "order_items", ["id"])
    op.create_index(op.f("ix_order_items_order_id"), "order_items", ["order_id"])
    op.create_index(op.f("ix_order_items_product_id"), "order_items", ["product_id"])


def downgrade() -> None:
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("delivery_settings")
    op.drop_table("locations")
    op.drop_table("products")
    op.drop_table("users")

