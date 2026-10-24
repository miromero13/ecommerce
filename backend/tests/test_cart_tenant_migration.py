"""Exercise actual 0040 DDL in the guarded CU1 fixture transaction only."""
import importlib.util
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import text


def test_0040_round_trip_preserves_carts_and_refuses_unsafe_downgrade(api_db, api_schema, identities):
    from app.models.cart import Cart
    from app.models.user import User
    from app.schemas.enums import GenderEnum, RolEnum

    connection = api_db.connection()
    # Neither setup DDL nor the migration may resolve carts outside our schema.
    assert connection.execute(text("SELECT current_schema()")).scalar_one() == api_schema[1]
    assert api_schema[1].startswith("cu1_api_")
    assert connection.execute(text("SELECT count(*) FROM carts")).scalar_one() == 0
    connection.execute(text("ALTER TABLE carts ALTER COLUMN tenant_id SET NOT NULL"))

    def nullable():
        # Fresh catalog query after every DDL operation; no inspector cache.
        return connection.execute(text(
            "SELECT is_nullable FROM information_schema.columns "
            "WHERE table_schema = current_schema() AND table_name = 'carts' "
            "AND column_name = 'tenant_id'"
        )).scalar_one()

    def carts():
        return connection.execute(text(
            "SELECT row_to_json(c)::text FROM carts c ORDER BY id"
        )).scalars().all()

    employee, tenants, _ = identities
    owned = Cart(user_id=employee.id, tenant_id=tenants[0].id,
                 subtotal=25, discount_amount=0, total_amount=25)
    api_db.add(owned)
    api_db.flush()
    original = carts()
    assert len(original) == 1
    assert nullable() == "NO"

    path = Path(__file__).parents[1] / "alembic/versions/0040_allow_empty_global_carts.py"
    spec = importlib.util.spec_from_file_location("cu1_cart_migration_0040", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    context = MigrationContext.configure(api_db.connection())
    with Operations.context(context):
        migration.upgrade()
        assert nullable() == "YES"
        assert carts() == original  # Includes ids, company, prices and timestamps.

        customer = User(name="Migration customer", email="migration-customer@example.com",
                        hashed_password="unused", gender=GenderEnum.femenino,
                        rol=RolEnum.cliente, tenant_id=None, is_active=True)
        api_db.add(customer)
        api_db.flush()
        empty = Cart(user_id=customer.id, tenant_id=None,
                     subtotal=0, discount_amount=0, total_amount=0)
        api_db.add(empty)
        api_db.flush()  # A real INSERT must succeed against the upgraded column.
        stored = connection.execute(text(
            "SELECT tenant_id, user_id, subtotal, discount_amount, total_amount "
            "FROM carts WHERE id = :id"
        ), {"id": empty.id}).one()
        assert tuple(stored) == (None, customer.id, 0, 0, 0)
        before_refusal = carts()
        assert len(before_refusal) == 2

        with pytest.raises(RuntimeError, match=(
            r"^Cannot downgrade 0040: customer carts without a company still exist$"
        )):
            migration.downgrade()
        assert nullable() == "YES"
        assert carts() == before_refusal  # No deletion, reassignment or row rewrite.

        # Remove only the empty row this test inserted, never other fixture rows.
        api_db.delete(empty)
        api_db.flush()
        assert carts() == original
        migration.downgrade()
        assert nullable() == "NO"
        assert carts() == original
    # api_db closes its Session and rolls back the outer transaction, including
    # setup ALTER, both migration directions, inserted rows and the row removal.
