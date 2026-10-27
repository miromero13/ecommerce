"""Phase 0: stock checks, tenant branding and payout bank account, platform
collection ledger, daily settlements, QR payments, reservation deposits and
CU20 delivery (branch coordinates, delivery orders, platform-level drivers).

Revision ID: 0041
Revises: 0040
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0041"
down_revision = "0040"
branch_labels = None
depends_on = None

STOCK_CHECKS = (
    ("ck_inventory_quantity_non_negative", "quantity >= 0"),
    ("ck_inventory_reserved_non_negative", "reserved_quantity >= 0"),
    ("ck_inventory_reserved_within_quantity", "reserved_quantity <= quantity"),
)
REPAIR_CART_COMPANY = """
    UPDATE carts SET tenant_id = lines.tenant_id
    FROM (SELECT DISTINCT ON (cart_items.cart_id) cart_items.cart_id, product_variants.tenant_id
          FROM cart_items JOIN product_variants ON product_variants.id = cart_items.variant_id) AS lines
    WHERE carts.id = lines.cart_id AND carts.tenant_id IS NULL
"""
ORDER_DELIVERY_COLUMNS = (
    ("delivery_address", sa.String(255)),
    ("delivery_reference", sa.String(255)),
    ("delivery_latitude", sa.Numeric(9, 6)),
    ("delivery_longitude", sa.Numeric(9, 6)),
    ("delivery_distance_km", sa.Numeric(6, 2)),
    ("delivery_pin", sa.String(4)),
    ("delivered_at", sa.DateTime(timezone=True)),
)
TENANT_COLUMNS = (
    ("logo_url", sa.String(500)),
    ("logo_public_id", sa.String(255)),
    ("primary_color", sa.String(7)),
    ("bank_name", sa.String(120)),
    ("bank_account_number", sa.String(40)),
    ("bank_account_holder", sa.String(160)),
)


def _money(name):
    return sa.Column(name, sa.Numeric(10, 2), nullable=False)


def _tenant_fk():
    return sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"),
                     nullable=False, index=True)


def _created_at():
    return sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())


def upgrade() -> None:
    for name, column_type in TENANT_COLUMNS:
        op.add_column("tenants", sa.Column(name, column_type, nullable=True))
    op.add_column("tenants", sa.Column("platform_fee_percent", sa.Numeric(5, 2), nullable=False, server_default="0"))

    # Clamp rows left impossible by past bugs so the checks can be enforced.
    op.execute("UPDATE inventory SET quantity = GREATEST(quantity, 0)")
    op.execute("UPDATE inventory SET reserved_quantity = LEAST(GREATEST(reserved_quantity, 0), quantity)")
    for name, condition in STOCK_CHECKS:
        op.create_check_constraint(name, "inventory", condition)

    # Repair carts emptied of their company by the autoflush bug while still holding lines.
    op.execute(REPAIR_CART_COMPANY)

    # New values cannot be used inside this same transaction; nothing below does.
    op.execute("ALTER TYPE paymentmethodenum ADD VALUE IF NOT EXISTS 'qr'")
    op.execute("ALTER TYPE reservationstatusenum ADD VALUE IF NOT EXISTS 'pending_payment'")
    op.execute("ALTER TYPE fulfillmentstatusenum ADD VALUE IF NOT EXISTS 'in_transit'")
    op.execute("ALTER TYPE fulfillmentstatusenum ADD VALUE IF NOT EXISTS 'delivered'")

    # CU20: drivers work for every company, so they keep no company or branch.
    op.execute("UPDATE users SET tenant_id = NULL, branch_id = NULL WHERE rol = 'delivery'")
    op.add_column("branches", sa.Column("latitude", sa.Numeric(9, 6), nullable=True))
    op.add_column("branches", sa.Column("longitude", sa.Numeric(9, 6), nullable=True))
    for name, column_type in ORDER_DELIVERY_COLUMNS:
        op.add_column("orders", sa.Column(name, column_type, nullable=True))
    op.add_column("orders", sa.Column("fulfillment_type", sa.String(10), nullable=False, server_default="pickup"))
    op.add_column("orders", sa.Column("shipping_cost", sa.Numeric(10, 2), nullable=False, server_default="0"))
    op.add_column("orders", sa.Column("deposit_applied", sa.Numeric(10, 2), nullable=False, server_default="0"))
    op.add_column("orders", sa.Column("delivery_driver_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True))
    op.create_index("ix_orders_delivery_driver_id", "orders", ["delivery_driver_id"])
    # CU15 in-store coupon: the identified customer and the coupon used in a cash/QR sale.
    op.add_column("sales", sa.Column("customer_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True))
    op.add_column("sales", sa.Column("promotion_code_id", UUID(as_uuid=True), sa.ForeignKey("promotion_codes.id"), nullable=True))
    op.create_index("ix_sales_customer_id", "sales", ["customer_id"])
    op.create_index("ix_sales_promotion_code_id", "sales", ["promotion_code_id"])

    op.create_table(
        "settlements",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        _tenant_fk(),
        sa.Column("period_date", sa.Date(), nullable=False),
        _money("gross_amount"), _money("fee_amount"), _money("net_amount"),
        sa.Column("transactions_count", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="pending"),
        sa.Column("bank_name", sa.String(120), nullable=True),
        sa.Column("bank_account_number", sa.String(40), nullable=True),
        sa.Column("bank_account_holder", sa.String(160), nullable=True),
        sa.Column("transfer_reference", sa.String(120), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        _created_at(),
        sa.UniqueConstraint("tenant_id", "period_date", name="uq_settlements_tenant_period"),
    )
    op.create_table(
        "payment_transactions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        _tenant_fk(),
        sa.Column("source_type", sa.String(30), nullable=False),
        sa.Column("source_id", UUID(as_uuid=True), nullable=False),
        sa.Column("method", sa.String(10), nullable=False),
        _money("gross_amount"), _money("fee_amount"), _money("net_amount"),
        sa.Column("currency", sa.String(10), nullable=False),
        sa.Column("provider_reference", sa.String(120), nullable=True),
        sa.Column("settlement_id", UUID(as_uuid=True), sa.ForeignKey("settlements.id"), nullable=True, index=True),
        _created_at(),
        sa.UniqueConstraint("source_type", "source_id", name="uq_payment_transactions_source"),
    )
    op.create_table(
        "qr_payments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        _tenant_fk(),
        sa.Column("reference", sa.String(40), nullable=False, unique=True),
        sa.Column("purpose", sa.String(30), nullable=False),
        sa.Column("source_id", UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("branch_id", UUID(as_uuid=True), sa.ForeignKey("branches.id"), nullable=True),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        _money("amount"),
        sa.Column("currency", sa.String(10), nullable=False),
        sa.Column("status", sa.String(10), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        _created_at(),
    )

    op.add_column("reservations", sa.Column("deposit_amount", sa.Numeric(10, 2), nullable=False, server_default="0"))
    op.add_column("reservations", sa.Column("deposit_status", sa.String(12), nullable=False, server_default="none"))
    op.add_column("reservations", sa.Column("payment_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("reservations", sa.Column("stripe_payment_intent_id", sa.String(), nullable=True, unique=True))


def downgrade() -> None:
    op.drop_index("ix_sales_promotion_code_id", table_name="sales")
    op.drop_index("ix_sales_customer_id", table_name="sales")
    op.drop_column("sales", "promotion_code_id")
    op.drop_column("sales", "customer_id")
    op.drop_index("ix_orders_delivery_driver_id", table_name="orders")
    for name in ("delivery_driver_id", "deposit_applied", "shipping_cost", "fulfillment_type", *(n for n, _ in ORDER_DELIVERY_COLUMNS)):
        op.drop_column("orders", name)
    op.drop_column("branches", "longitude")
    op.drop_column("branches", "latitude")
    # Drivers stay platform-level; their old company/branch assignment is not restored.
    for column in ("stripe_payment_intent_id", "payment_expires_at", "deposit_status", "deposit_amount"):
        op.drop_column("reservations", column)
    op.drop_table("qr_payments")
    op.drop_table("payment_transactions")
    op.drop_table("settlements")
    # PostgreSQL cannot drop enum values; 'qr' and 'pending_payment' stay unused.
    for name, _ in STOCK_CHECKS:
        op.drop_constraint(name, "inventory", type_="check")
    op.drop_column("tenants", "platform_fee_percent")
    for name, _ in reversed(TENANT_COLUMNS):
        op.drop_column("tenants", name)
