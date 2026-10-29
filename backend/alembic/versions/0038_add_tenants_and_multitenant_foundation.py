"""add tenants and multitenant foundation

Revision ID: 0038
Revises: 0037
Create Date: 2026-10-19 16:30:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0038"
down_revision = "0037"
branch_labels = None
depends_on = None

TENANT_1_ID = "11111111-1111-1111-1111-111111111111"
TENANT_2_ID = "22222222-2222-2222-2222-222222222222"
TENANT_3_ID = "33333333-3333-3333-3333-333333333333"
SUPERADMIN_ID = "00000000-0000-0000-0000-000000000001"
SUPERADMIN_PASSWORD_HASH = "$2b$12$nOdNZEt6MtpwcFEy3abOxejzC2bQtfe1hPVkBOd8SaI5nlqBF67Cq"  # SuperAdmin2026!


def upgrade() -> None:
    # 1. Add superadministrador to rolenum if not present
    op.execute("ALTER TYPE rolenum ADD VALUE IF NOT EXISTS 'superadministrador';")

    # 2. Create tenantstatusenum if not present
    op.execute("""
    DO $$
    BEGIN
        IF to_regtype('tenantstatusenum') IS NULL THEN  -- only the current schema (search_path), not other schemas
            CREATE TYPE tenantstatusenum AS ENUM ('active', 'trial', 'suspended');
        END IF;
    END$$;
    """)

    # 3. Create tenants table
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("contact_email", sa.String(length=255), nullable=False),
        sa.Column("currency", sa.String(length=10), server_default="BOB", nullable=False),
        sa.Column("country", sa.String(length=80), server_default="Bolivia", nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM("active", "trial", "suspended", name="tenantstatusenum", create_type=False),
            server_default="active",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("name", name="uq_tenants_name"),
        sa.UniqueConstraint("slug", name="uq_tenants_slug"),
    )
    op.create_index("ix_tenants_id", "tenants", ["id"])
    op.create_index("ix_tenants_slug", "tenants", ["slug"])

    # 4. Insert 3 initial e-commerce tenants
    op.execute(
        sa.text(f"""
        INSERT INTO tenants (id, name, slug, contact_email, currency, country, status, created_at, updated_at)
        VALUES 
            ('{TENANT_1_ID}', 'Aura Moda', 'aura-moda', 'contacto@auramoda.bo', 'BOB', 'Bolivia', 'active', now(), now()),
            ('{TENANT_2_ID}', 'UrbanStyle', 'urban-style', 'contacto@urbanstyle.bo', 'BOB', 'Bolivia', 'active', now(), now()),
            ('{TENANT_3_ID}', 'NovaWear', 'nova-wear', 'contacto@novawear.bo', 'BOB', 'Bolivia', 'active', now(), now())
        ON CONFLICT (id) DO NOTHING;
        """)
    )

    # 5. Add tenant_id to users (nullable for superadmin and clients)
    op.add_column("users", sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_users_tenant_id", "users", "tenants", ["tenant_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])

    # Backfill non-client staff users to Tenant 1 ("Aura Moda")
    op.execute(
        sa.text(f"""
        UPDATE users 
        SET tenant_id = '{TENANT_1_ID}' 
        WHERE rol NOT IN ('cliente', 'superadministrador') AND tenant_id IS NULL;
        """)
    )

    # Insert root superadmin user
    op.execute(
        sa.text(f"""
        INSERT INTO users (id, name, email, hashed_password, gender, rol, branch_id, tenant_id, is_active)
        VALUES ('{SUPERADMIN_ID}', 'Super Administrador', 'superadmin@fashionstore.com', '{SUPERADMIN_PASSWORD_HASH}', 'femenino', 'superadministrador', NULL, NULL, true)
        ON CONFLICT (email) DO NOTHING;
        """)
    )

    # 6. List of tables that strictly belong to a tenant
    scoped_tables = [
        "branches",
        "categories",
        "collections",
        "seasons",
        "products",
        "product_variants",
        "inventory",
        "inventory_movements",
        "replenishment_requests",
        "orders",
        "sales",
        "reservations",
        "carts",
        "promotion_codes",
        "providers",
    ]

    for table_name in scoped_tables:
        op.add_column(table_name, sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            f"fk_{table_name}_tenant_id",
            table_name,
            "tenants",
            ["tenant_id"],
            ["id"],
            ondelete="CASCADE",
        )
        op.create_index(f"ix_{table_name}_tenant_id", table_name, ["tenant_id"])
        
        # Backfill existing records to Tenant 1 ("Aura Moda")
        op.execute(
            sa.text(f"""
            UPDATE {table_name} 
            SET tenant_id = '{TENANT_1_ID}' 
            WHERE tenant_id IS NULL;
            """)
        )
        # Enforce NOT NULL after backfill
        op.alter_column(table_name, "tenant_id", nullable=False)

    # 7. Adjust branch uniqueness to be per-tenant
    op.execute("ALTER TABLE branches DROP CONSTRAINT IF EXISTS branches_name_key;")
    op.create_unique_constraint("uq_branches_name_tenant", "branches", ["name", "tenant_id"])


def downgrade() -> None:
    op.drop_constraint("uq_branches_name_tenant", "branches", type_="unique")
    op.create_unique_constraint("branches_name_key", "branches", ["name"])

    scoped_tables = [
        "branches",
        "categories",
        "collections",
        "seasons",
        "products",
        "product_variants",
        "inventory",
        "inventory_movements",
        "replenishment_requests",
        "orders",
        "sales",
        "reservations",
        "carts",
        "promotion_codes",
        "providers",
    ]

    for table_name in scoped_tables:
        op.drop_constraint(f"fk_{table_name}_tenant_id", table_name, type_="foreignkey")
        op.drop_index(f"ix_{table_name}_tenant_id", table_name)
        op.drop_column(table_name, "tenant_id")

    op.execute(f"DELETE FROM users WHERE id = '{SUPERADMIN_ID}';")
    op.drop_constraint("fk_users_tenant_id", "users", type_="foreignkey")
    op.drop_index("ix_users_tenant_id", "users")
    op.drop_column("users", "tenant_id")

    op.drop_index("ix_tenants_slug", table_name="tenants")
    op.drop_index("ix_tenants_id", table_name="tenants")
    op.drop_table("tenants")

    op.execute("DROP TYPE IF EXISTS tenantstatusenum;")
