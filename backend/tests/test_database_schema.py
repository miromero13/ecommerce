"""Real PostgreSQL snapshot checks; never use the application's database URL."""
import importlib
import os
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit
from uuid import uuid4

import psycopg2
from psycopg2 import errors, sql
import pytest


@pytest.fixture
def database():
    url = os.environ.get("CU1_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set CU1_TEST_DATABASE_URL to the disposable local cu1_test database")
    target = urlsplit(url)
    if (target.scheme not in {"postgresql", "postgres"}
            or target.hostname != "127.0.0.1" or target.path != "/cu1_test"
            or target.query or target.fragment):
        pytest.fail("CU1_TEST_DATABASE_URL must target 127.0.0.1/cu1_test without options")
    connection = psycopg2.connect(url, connect_timeout=3)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout = '5s'")
            cursor.execute("SET LOCAL lock_timeout = '2s'")
            schema = "cu1_" + uuid4().hex
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
            cursor.execute(sql.SQL("SET LOCAL search_path TO {}").format(sql.Identifier(schema)))
            yield cursor
    finally:
        connection.rollback()
        connection.close()


@pytest.fixture
def snapshot(database):
    sql_path = Path(__file__).parents[1].joinpath("database_schema.sql")
    if not sql_path.exists():
        pytest.skip("database_schema.sql not present; schema is managed via Alembic migrations")
    database.execute(sql_path.read_text())
    return database


@pytest.fixture
def metadata(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", os.environ["CU1_TEST_DATABASE_URL"])
    monkeypatch.setenv("SECRET_KEY", "cu1-test-only")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    # Disable dotenv loading, including unrelated optional credentials.
    with patch("pydantic_settings.sources.DotEnvSettingsSource._read_env_files", return_value={}):
        for path in sorted(Path(__file__).parents[1].joinpath("app/models").glob("*.py")):
            importlib.import_module("app.models." + path.stem)
    from app.core.database import Base
    return Base.metadata


def insert(cursor, table, **values):
    values = {"id": str(uuid4()), **values}
    cursor.execute(sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING id").format(
        sql.Identifier(table), sql.SQL(", ").join(map(sql.Identifier, values)),
        sql.SQL(", ").join(sql.Placeholder() for _ in values)), list(values.values()))
    return str(cursor.fetchone()[0])


def rows(cursor, table):
    cursor.execute(sql.SQL("SELECT * FROM {} ORDER BY id").format(sql.Identifier(table)))
    return cursor.fetchall()


def reject(cursor, table, exception, **values):
    before = rows(cursor, table)
    cursor.execute("SAVEPOINT rejected_insert")
    try:
        with pytest.raises(exception):
            insert(cursor, table, **values)
    finally:
        cursor.execute("ROLLBACK TO SAVEPOINT rejected_insert")
        cursor.execute("RELEASE SAVEPOINT rejected_insert")
    assert rows(cursor, table) == before


def tenant(cursor, suffix):
    return insert(cursor, "tenants", name="Store " + suffix, slug="store-" + suffix,
                  contact_email=suffix + "@example.test", currency="BOB", status="active",
                  created_at="2026-01-01", updated_at="2026-01-01")


def customer(cursor, suffix="one"):
    return insert(cursor, "users", name="Customer", email=suffix + "@example.test",
                  hashed_password="not-a-real-password", gender="femenino", rol="cliente",
                  is_active=True)


@pytest.fixture
def commerce(snapshot):
    c = snapshot
    tid = tenant(c, "one")
    uid = customer(c)
    other_uid = customer(c, "two")
    branch = insert(c, "branches", tenant_id=tid, name="Central", city="City",
                    is_default=False, is_active=True)
    category = insert(c, "categories", tenant_id=tid, name="Clothing")
    product = insert(c, "products", tenant_id=tid, name="Shirt", category_id=category)
    cart = insert(c, "carts", tenant_id=tid, user_id=uid, status="active",
                  subtotal=0, discount_amount=0, total_amount=0)
    reservation = insert(c, "reservations", tenant_id=tid, branch_id=branch, user_id=uid,
                         cart_id=cart, visit_date="2026-01-01", expires_at="2026-01-02",
                         status="pending", total_amount=0)
    return dict(tenant=tid, user=uid, other_user=other_uid, branch=branch,
                product=product, cart=cart, reservation=reservation)


def test_snapshot_bootstraps_37_empty_tables(snapshot):
    snapshot.execute("SELECT tablename FROM pg_tables WHERE schemaname = current_schema()")
    tables = [r[0] for r in snapshot.fetchall()]
    assert len(tables) == 37
    assert "alembic_version" not in tables
    for table in tables:
        assert rows(snapshot, table) == []


@pytest.mark.parametrize("source", ["snapshot", "metadata"])
def test_branch_ownership_and_per_tenant_names(database, source, request):
    c = database
    if source == "snapshot":
        request.getfixturevalue("snapshot")
    else:
        from sqlalchemy.dialects.postgresql import dialect
        from sqlalchemy.schema import CreateTable
        metadata = request.getfixturevalue("metadata")
        # Execute the actual ORM's branch DDL with its tenant dependency.
        c.execute("CREATE TYPE tenantstatusenum AS ENUM ('active', 'trial', 'suspended')")
        for name in ("tenants", "branches"):
            c.execute(str(CreateTable(metadata.tables[name]).compile(dialect=dialect())))
    first, second = tenant(c, "one"), tenant(c, "two")
    values = dict(name="Central", city="City", is_default=False, is_active=True)
    insert(c, "branches", tenant_id=first, **values)
    insert(c, "branches", tenant_id=second, **values)
    assert len(rows(c, "branches")) == 2
    reject(c, "branches", errors.UniqueViolation, tenant_id=first, **values)
    reject(c, "branches", errors.NotNullViolation, tenant_id=None, **{**values, "name": "Other"})
    insert(c, "branches", tenant_id=first, **{**values, "name": "North"})
    assert len(rows(c, "branches")) == 3


def test_global_customer_and_unique_email(snapshot):
    uid = customer(snapshot)
    snapshot.execute("SELECT tenant_id, branch_id, rol FROM users WHERE id = %s", (uid,))
    assert snapshot.fetchone() == (None, None, "cliente")
    reject(snapshot, "users", errors.UniqueViolation, name="Duplicate", email="one@example.test",
           hashed_password="unused", gender="masculino", rol="cliente", is_active=True)


@pytest.mark.parametrize("table,values", [
    ("tenants", dict(name="Different name", slug="store-one", contact_email="x@example.test",
                     currency="BOB", status="active", created_at="2026-01-01", updated_at="2026-01-01")),
    ("saas_plans", dict(name="Plan", slug="basic", price_monthly=0, price_yearly=0,
                        max_branches=2, max_garments=500, features="[]", is_active=True,
                        created_at="2026-01-01", updated_at="2026-01-01")),
    ("stripe_events", dict(stripe_event_id="evt_test")),
])
def test_unique_slugs_and_stripe_events(snapshot, table, values):
    if table == "tenants":
        tenant(snapshot, "one")
    else:
        insert(snapshot, table, **values)
    reject(snapshot, table, errors.UniqueViolation, **values)


@pytest.mark.parametrize("table", [
    "product_variants", "providers", "carts", "conversations", "device_tokens",
    "notifications", "promotion_codes", "reservations", "sales",
])
def test_existing_unique_indexes_reject_duplicates(snapshot, commerce, table):
    f = commerce
    money = dict(subtotal=0, discount_amount=0, total_amount=0)
    values = {
        "product_variants": dict(tenant_id=f["tenant"], product_id=f["product"],
                                 sku="SKU-1", price=1, status="active"),
        "providers": dict(tenant_id=f["tenant"], user_id=f["user"],
                          business_name="Provider", contact_name="Contact", status="active"),
        "carts": dict(tenant_id=f["tenant"], user_id=f["user"], status="active", **money),
        "conversations": dict(user_id=f["user"]),
        "device_tokens": dict(user_id=f["user"], token="device-token",
                              platform="android", is_active=True),
        "notifications": dict(user_id=f["user"], title="Notice", body="Body",
                              data="{}", dedupe_key="notice-1"),
        "promotion_codes": dict(tenant_id=f["tenant"], code="SAVE", discount_type="fixed",
                                discount_value=1, created_by=f["user"], is_active=True),
        "reservations": dict(tenant_id=f["tenant"], branch_id=f["branch"], user_id=f["user"],
                             cart_id=f["cart"], visit_date="2026-01-01",
                             expires_at="2026-01-02", status="pending", total_amount=0),
        "sales": dict(tenant_id=f["tenant"], branch_id=f["branch"], user_id=f["user"],
                      reservation_id=f["reservation"], status="completed", payment_method="cash",
                      payment_status="paid", currency="BOB", **money),
    }[table]
    if table not in {"carts", "reservations"}:
        insert(snapshot, table, **values)
    if table in {"device_tokens", "reservations", "sales"}:
        # A different customer must not bypass token/cart/reservation uniqueness.
        values = {**values, "user_id": f["other_user"]}
    reject(snapshot, table, errors.UniqueViolation, **values)


def test_snapshot_preserves_orm_indexes_and_enum_labels(snapshot, metadata):
    from sqlalchemy import Enum
    snapshot.execute("SELECT indexname FROM pg_indexes WHERE schemaname = current_schema()")
    names = {row[0] for row in snapshot.fetchall()}
    expected = {index.name for table in metadata.tables.values() for index in table.indexes}
    assert expected <= names
    seen = set()
    for table in metadata.tables.values():
        for column in table.columns:
            if isinstance(column.type, Enum) and column.type.name not in seen:
                seen.add(column.type.name)
                for label in column.type.enums:
                    snapshot.execute(sql.SQL("SELECT %s::{}").format(sql.Identifier(column.type.name)), (label,))
                    assert snapshot.fetchone() == (label,)
    assert len(seen) == 17
