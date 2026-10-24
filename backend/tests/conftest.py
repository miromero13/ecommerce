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


@pytest.fixture
def api_db():
    url = guarded_url()
    if not url:
        pytest.skip("Set CU1_TEST_DATABASE_URL to the authorized disposable local target")
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    for path in sorted(Path(__file__).parents[1].joinpath("app/models").glob("*.py")):
        importlib.import_module("app.models." + path.stem)
    engine = create_engine(url, connect_args={"connect_timeout": 3})
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.exec_driver_sql("SET LOCAL statement_timeout = '5s'")
            connection.exec_driver_sql("SET LOCAL lock_timeout = '2s'")
            schema = "cu1_api_" + uuid4().hex
            connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
            connection.exec_driver_sql(f'SET LOCAL search_path TO "{schema}"')
            cursor = connection.connection.cursor()
            try:
                cursor.execute(Path(__file__).parents[1].joinpath("database_schema.sql").read_text())
            finally:
                cursor.close()
            with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
                yield session
        finally:
            transaction.rollback()
    engine.dispose()


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
        yield api_db

    app.dependency_overrides[get_db] = override_db
    # Deliberately not a context manager: no lifespan/background expiry tasks.
    client = TestClient(app)
    try:
        yield client
    finally:
        client.close()
        app.dependency_overrides.clear()


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
    branches = [Branch(name=name, city="City", tenant_id=tenants[index].id)
                for name, index in (("A1", 0), ("A2", 0), ("B1", 1))]
    api_db.add_all(branches)
    user = User(name="Employee", email="employee@example.com", hashed_password="unused",
                gender=GenderEnum.femenino, rol=RolEnum.administrador,
                tenant_id=tenants[0].id, is_active=True)
    api_db.add(user)
    api_db.commit()
    return user, tenants, branches
