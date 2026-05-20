"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-20
"""
from alembic import op


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The first Render deploy briefly created tables from SQLAlchemy before
    # Alembic was stamped. IF NOT EXISTS lets that database adopt migrations.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(30) NOT NULL,
            is_active BOOLEAN NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username ON users (username)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_id ON users (id)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(160) NOT NULL,
            image_url TEXT NOT NULL,
            weight VARCHAR(80) NOT NULL,
            price NUMERIC(10, 2) NOT NULL,
            features TEXT NOT NULL,
            is_active BOOLEAN NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_products_id ON products (id)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS locations (
            id SERIAL PRIMARY KEY,
            name VARCHAR(120) NOT NULL,
            is_active BOOLEAN NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_locations_id ON locations (id)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_locations_name ON locations (name)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS delivery_settings (
            id SERIAL PRIMARY KEY,
            mode VARCHAR(30) NOT NULL,
            allowed_weekdays VARCHAR(30) NOT NULL
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            full_name VARCHAR(160) NOT NULL,
            phone VARCHAR(40) NOT NULL,
            location_id INTEGER NOT NULL REFERENCES locations(id),
            delivery_date DATE NOT NULL,
            status VARCHAR(30) NOT NULL,
            admin_note TEXT NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_orders_id ON orders (id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_orders_phone ON orders (phone)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_orders_location_id ON orders (location_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_orders_delivery_date ON orders (delivery_date)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_orders_status ON orders (status)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS order_items (
            id SERIAL PRIMARY KEY,
            order_id INTEGER NOT NULL REFERENCES orders(id),
            product_id INTEGER NOT NULL REFERENCES products(id),
            quantity INTEGER NOT NULL,
            unit_price NUMERIC(10, 2) NOT NULL,
            product_name VARCHAR(160) NOT NULL,
            product_weight VARCHAR(80) NOT NULL
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_order_items_id ON order_items (id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_order_items_order_id ON order_items (order_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_order_items_product_id ON order_items (product_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS order_items")
    op.execute("DROP TABLE IF EXISTS orders")
    op.execute("DROP TABLE IF EXISTS delivery_settings")
    op.execute("DROP TABLE IF EXISTS locations")
    op.execute("DROP TABLE IF EXISTS products")
    op.execute("DROP TABLE IF EXISTS users")
