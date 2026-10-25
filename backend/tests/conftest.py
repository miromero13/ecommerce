"""Opt-in CU1 API fixtures; never load application dotenv credentials."""
import importlib
import os
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlsplit
from uuid import uuid4

import pytest


def guarded_url():
    url = os.environ.get("CU1_TEST_DATABASE_URL")
    if not url:
        return None
    target = urlsplit(url)
    if (target.scheme != "postgresql" or target.hostname != "127.0.0.1"
            or target.port != 53419 or target.path != "/cu1_test"
            or target.username != "postgres" or target.password != "cu1-disposable-only"
            or target.query or target.fragment):
        raise ValueError("CU1_TEST_DATABASE_URL must be the authorized disposable local target")
    return url


# Collection-time imports in other tests may instantiate settings. Only an
# explicit, guarded opt-in initializes them; no fallback to DATABASE_URL/.env.
if guarded_url():
    with patch.dict(os.environ, {
        "DATABASE_URL": guarded_url(), "SECRET_KEY": "cu1-test-only",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
    }, clear=True), patch(
        "pydantic_settings.sources.DotEnvSettingsSource._read_env_files", return_value={}
    ):
        importlib.import_module("app.core.config")


@pytest.fixture(scope="session")
def api_schema():
    """Build empty test tables once; each test still rolls back all its rows."""
    url = guarded_url()
    if not url:
        pytest.skip("Set CU1_TEST_DATABASE_URL to the authorized disposable local target")
    from sqlalchemy import create_engine

    for path in sorted(Path(__file__).parents[1].joinpath("app/models").glob("*.py")):
        importlib.import_module("app.models." + path.stem)
    engine = create_engine(url, connect_args={"connect_timeout": 3})
    schema = "cu1_api_" + uuid4().hex
    try:
        with engine.begin() as connection:
            connection.exec_driver_sql("SET LOCAL statement_timeout = '5s'")
            connection.exec_driver_sql("SET LOCAL lock_timeout = '2s'")
            connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
            connection.exec_driver_sql(f'SET LOCAL search_path TO "{schema}"')
            sql_path = Path(__file__).parents[1].joinpath("database_schema.sql")
            if sql_path.exists():
                cursor = connection.connection.cursor()
                try:
                    cursor.execute(sql_path.read_text())
                finally:
                    cursor.close()
            else:
                from app.core.database import Base
                Base.metadata.create_all(bind=connection)
        yield engine, schema
    finally:
        # Only this fixture's uniquely named schema in the guarded test DB.
        with engine.begin() as connection:
            connection.exec_driver_sql("SET LOCAL lock_timeout = '2s'")
            connection.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        engine.dispose()


@pytest.fixture
def api_db(api_schema):
    from sqlalchemy.orm import Session

    engine, schema = api_schema
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.exec_driver_sql("SET LOCAL statement_timeout = '5s'")
            connection.exec_driver_sql("SET LOCAL lock_timeout = '2s'")
            connection.exec_driver_sql(f'SET LOCAL search_path TO "{schema}"')
            with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
                yield session
        finally:
            transaction.rollback()


@pytest.fixture
def api(api_db):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.core.database import get_db
    from app.core.error_handlers import register_error_handlers
    from app.routes import branch_routes, catalog_routes, tenant_routes, user_routes

    app = FastAPI()
    register_error_handlers(app)
    for module in (branch_routes, catalog_routes, tenant_routes, user_routes):
        app.include_router(module.router, prefix="/api")

    def override_db():
        from sqlalchemy.orm import Session

        # Match production request lifetime: closing an uncommitted request must
        # discard its writes, rather than leaking them through one identity map.
        with Session(bind=api_db.bind, join_transaction_mode="create_savepoint") as session:
            yield session

    app.dependency_overrides[get_db] = override_db
    # Deliberately not a context manager: no lifespan/background expiry tasks.
    client = TestClient(app)
    try:
        yield client
    finally:
        client.close()
        app.dependency_overrides.clear()


PLAN_FEATURES = {
    "plan_basic": ["catalog", "pos", "inventory", "reservations", "standard_reports"],
    "plan_pro": ["catalog", "pos", "inventory", "reservations", "standard_reports",
                 "chatbot", "virtual_try_on_2d", "ai_text_reports"],
    "plan_enterprise": ["catalog", "pos", "inventory", "reservations", "standard_reports",
                        "chatbot", "virtual_try_on_2d", "virtual_try_on_3d_ar",
                        "ai_text_reports", "ai_ml_smart_reports"],
}


def seed_plans(db):
    """Same three plans that migration 0039 seeds; the schema snapshot has none."""
    from app.models.subscription_plan import SubscriptionPlan

    rows = {
        "plan_basic": ("Básico", "basic", 49, 490, 2, 500),
        "plan_pro": ("Profesional", "pro", 129, 1290, 5, 3000),
        "plan_enterprise": ("Enterprise", "enterprise", 299, 2990, 10, 10000),
    }
    plans = {}
    for plan_id, (name, slug, monthly, yearly, branches, garments) in rows.items():
        plans[plan_id] = SubscriptionPlan(
            id=plan_id, name=name, slug=slug, price_monthly=monthly, price_yearly=yearly,
            max_branches=branches, max_garments=garments, features=PLAN_FEATURES[plan_id],
            is_active=True,
        )
    db.add_all(plans.values())
    db.flush()
    return plans


def subscribe(db, tenant, plan, days=30):
    from datetime import datetime, timedelta, timezone
    from app.models.tenant_subscription import TenantSubscription

    now = datetime.now(timezone.utc)
    subscription = TenantSubscription(tenant_id=tenant.id, plan_id=plan.id,
                                      start_date=now, end_date=now + timedelta(days=days))
    db.add(subscription)
    db.flush()
    return subscription


@pytest.fixture
def identities(api_db):
    from app.models.branch import Branch
    from app.models.tenant import Tenant
    from app.models.user import User
    from app.schemas.enums import GenderEnum, RolEnum

    tenants = [Tenant(name=name, slug=name.lower(), contact_email=name + "@example.com")
               for name in ("Alpha", "Beta")]
    api_db.add_all(tenants)
    api_db.flush()
    # Companies need a current plan to create branches/products (CU2).
    plans = seed_plans(api_db)
    for tenant in tenants:
        subscribe(api_db, tenant, plans["plan_enterprise"])
    branches = [Branch(name=name, city="City", tenant_id=tenants[index].id)
                for name, index in (("A1", 0), ("A2", 0), ("B1", 1))]
    api_db.add_all(branches)
    user = User(name="Employee", email="employee@example.com", hashed_password="unused",
                gender=GenderEnum.femenino, rol=RolEnum.administrador,
                tenant_id=tenants[0].id, is_active=True)
    api_db.add(user)
    api_db.commit()
    return user, tenants, branches
