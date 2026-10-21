"""add saas plans and subscriptions

Revision ID: 0039
Revises: 0038
Create Date: 2026-10-21 17:00:00.000000
"""

import json
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0039"
down_revision = "0038"
branch_labels = None
depends_on = None

TENANT_1_ID = "11111111-1111-1111-1111-111111111111"
TENANT_2_ID = "22222222-2222-2222-2222-222222222222"
TENANT_3_ID = "33333333-3333-3333-3333-333333333333"

SUBSCRIPTION_1_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
SUBSCRIPTION_2_ID = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
SUBSCRIPTION_3_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"


def upgrade() -> None:
    # 1. Create enum types idempotently
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'billingcycleenum') THEN
            CREATE TYPE billingcycleenum AS ENUM ('monthly', 'yearly');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'subscriptionstatusenum') THEN
            CREATE TYPE subscriptionstatusenum AS ENUM ('active', 'trialing', 'past_due', 'canceled');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'subscriptionpaymentmethodenum') THEN
            CREATE TYPE subscriptionpaymentmethodenum AS ENUM ('simulated_card', 'cash', 'stripe');
        END IF;
    END$$;
    """)

    # 2. Create saas_plans table
    op.create_table(
        "saas_plans",
        sa.Column("id", sa.String(length=50), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("price_monthly", sa.Numeric(precision=10, scale=2), server_default="0.00", nullable=False),
        sa.Column("price_yearly", sa.Numeric(precision=10, scale=2), server_default="0.00", nullable=False),
        sa.Column("max_branches", sa.Integer(), server_default="2", nullable=False),
        sa.Column("max_garments", sa.Integer(), server_default="500", nullable=False),
        sa.Column("features", sa.JSON(), server_default="[]", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("slug", name="uq_saas_plans_slug"),
    )
    op.create_index("ix_saas_plans_slug", "saas_plans", ["slug"])

    # 3. Create tenant_subscriptions table
    op.create_table(
        "tenant_subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "plan_id",
            sa.String(length=50),
            sa.ForeignKey("saas_plans.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "billing_cycle",
            postgresql.ENUM("monthly", "yearly", name="billingcycleenum", create_type=False),
            server_default="monthly",
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM("active", "trialing", "past_due", "canceled", name="subscriptionstatusenum", create_type=False),
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "payment_method",
            postgresql.ENUM("simulated_card", "cash", "stripe", name="subscriptionpaymentmethodenum", create_type=False),
            server_default="simulated_card",
            nullable=False,
        ),
        sa.Column("start_date", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_tenant_subscriptions_id", "tenant_subscriptions", ["id"])
    op.create_index("ix_tenant_subscriptions_tenant_id", "tenant_subscriptions", ["tenant_id"])
    op.create_index("ix_tenant_subscriptions_plan_id", "tenant_subscriptions", ["plan_id"])
    op.create_index("ix_tenant_subscriptions_status", "tenant_subscriptions", ["status"])

    # 4. Insert 3 initial SaaS plans
    basic_features = json.dumps(["catalog", "pos", "inventory", "reservations", "standard_reports"])
    pro_features = json.dumps([
        "catalog", "pos", "inventory", "reservations", "standard_reports",
        "chatbot", "virtual_try_on_2d", "ai_text_reports"
    ])
    enterprise_features = json.dumps([
        "catalog", "pos", "inventory", "reservations", "standard_reports",
        "chatbot", "virtual_try_on_2d", "virtual_try_on_3d_ar",
        "ai_text_reports", "ai_ml_smart_reports"
    ])

    op.execute(
        sa.text(f"""
        INSERT INTO saas_plans (id, name, slug, description, price_monthly, price_yearly, max_branches, max_garments, features, is_active, created_at, updated_at)
        VALUES 
            ('plan_basic', 'Básico', 'basic', 'Ideal para boutiques iniciales con catálogo, ventas POS presenciales e inventario unificado.', 49.00, 490.00, 2, 500, '{basic_features}', true, now(), now()),
            ('plan_pro', 'Profesional', 'pro', 'Para marcas en crecimiento que requieren vestidor virtual 2D con fotos y reportes asistidos por IA.', 129.00, 1290.00, 5, 3000, '{pro_features}', true, now(), now()),
            ('plan_enterprise', 'Enterprise', 'enterprise', 'Para grandes cadenas con vestidor virtual 3D en Realidad Aumentada y analítica predictiva con Machine Learning.', 299.00, 2990.00, 10, 10000, '{enterprise_features}', true, now(), now())
        ON CONFLICT (id) DO NOTHING;
        """)
    )

    # 5. Assign initial subscriptions to existing tenants
    op.execute(
        sa.text(f"""
        INSERT INTO tenant_subscriptions (id, tenant_id, plan_id, billing_cycle, status, payment_method, start_date, end_date, created_at, updated_at)
        VALUES
            ('{SUBSCRIPTION_1_ID}', '{TENANT_1_ID}', 'plan_enterprise', 'monthly', 'active', 'cash', now(), now() + interval '1 year', now(), now()),
            ('{SUBSCRIPTION_2_ID}', '{TENANT_2_ID}', 'plan_pro', 'monthly', 'active', 'cash', now(), now() + interval '1 year', now(), now()),
            ('{SUBSCRIPTION_3_ID}', '{TENANT_3_ID}', 'plan_basic', 'monthly', 'active', 'cash', now(), now() + interval '1 year', now(), now())
        ON CONFLICT (id) DO NOTHING;
        """)
    )


def downgrade() -> None:
    op.drop_table("tenant_subscriptions")
    op.drop_table("saas_plans")
    op.execute("DROP TYPE IF EXISTS subscriptionpaymentmethodenum;")
    op.execute("DROP TYPE IF EXISTS subscriptionstatusenum;")
    op.execute("DROP TYPE IF EXISTS billingcycleenum;")
