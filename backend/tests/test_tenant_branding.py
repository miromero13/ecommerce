"""CU1 branding: each company's logo and color for the staff panel and receipts (Cloudinary is faked)."""
import pytest

from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_marketplace_transactions import add, call, checkout, market, market_api, rejected  # noqa: F401

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64


@pytest.fixture
def cloud(monkeypatch):
    from app.services import tenant_service

    effects = []

    def upload(content, folder, public_id=None):
        effects.append(("upload", folder))
        return {"image_url": f"https://cdn.test/logo-{len(effects)}.png", "image_public_id": f"logo-{len(effects)}"}

    monkeypatch.setattr(tenant_service, "upload_image", upload)
    monkeypatch.setattr(tenant_service, "delete_image", lambda public_id: effects.append(("delete", public_id)))
    return effects


@pytest.fixture
def superadmin(api_db):
    from app.models.user import User
    from app.schemas.enums import GenderEnum, RolEnum

    user = User(name="Root", email="root@example.com", hashed_password="unused",
                gender=GenderEnum.femenino, rol=RolEnum.superadministrador, is_active=True)
    api_db.add(user)
    api_db.commit()
    return user


def logo(api, user, content=PNG, content_type="image/png", path="/saas/tenants/me/logo"):
    return api.post("/api" + path, headers=__import__("test_employee_authorization").headers(user),
                    files={"file": ("logo.png", content, content_type)})


def test_public_branding_is_readable_without_login(market_api, market):
    result = market_api.get(f"/api/saas/tenants/{market.own.tenant.id}/branding")
    assert result.status_code == 200
    assert result.json()["data"] == {"tenant_id": str(market.own.tenant.id), "name": market.own.tenant.name,
                                     "logo_url": None, "primary_color": None, "currency": "BOB"}


def test_admin_sets_color_and_replaces_logo(market_api, api_db, market, cloud):
    admin = market.staff[0, "administrador"]
    data = call(market_api, admin, "PUT", "/saas/tenants/me/branding",
                expected_message="Marca de la empresa actualizada", json={"primary_color": "#112233"})
    assert data["primary_color"] == "#112233"

    first = logo(market_api, admin)
    assert first.status_code == 200, first.text
    assert first.json()["data"]["logo_url"] == "https://cdn.test/logo-1.png"
    logo(market_api, admin)
    assert cloud[-1] == ("delete", "logo-1")  # the previous logo is removed from Cloudinary


@pytest.mark.parametrize("content, content_type, message", [
    (b"plain text", "text/plain", "El logo debe ser una imagen PNG, JPG o WEBP"),
    (PNG + b"0" * (2 * 1024 * 1024), "image/png", "El logo no puede superar los 2 MB"),
], ids=["not-an-image", "too-large"])
def test_logo_upload_is_validated(market_api, api_db, market, cloud, content, content_type, message):
    result = logo(market_api, market.staff[0, "administrador"], content, content_type)
    assert (result.status_code, result.json()["message"]) == (400, message)
    assert cloud == []


def test_invalid_color_and_non_admin_are_rejected(market_api, api_db, market):
    bad = market_api.put("/api/saas/tenants/me/branding", json={"primary_color": "red"},
                         headers=__import__("test_employee_authorization").headers(market.staff[0, "administrador"]))
    assert bad.status_code == 422
    rejected(market_api, api_db, market.staff[0, "cajero"], "PUT", "/saas/tenants/me/branding", 403,
             json={"primary_color": "#112233"})


def test_superadmin_edits_any_company_branding(market_api, api_db, market, cloud, superadmin):
    tenant_id = market.own.tenant.id
    call(market_api, superadmin, "PATCH", f"/saas/tenants/{tenant_id}", json={"primary_color": "#aabbcc"})
    assert logo(market_api, superadmin, path=f"/saas/tenants/{tenant_id}/logo").status_code == 200
    branding = market_api.get(f"/api/saas/tenants/{tenant_id}/branding").json()["data"]
    assert (branding["primary_color"], branding["logo_url"]) == ("#aabbcc", "https://cdn.test/logo-1.png")


def test_orders_expose_their_company_for_receipt_branding(market_api, api_db, market):
    add(market_api, market)
    order = checkout(market_api, market)
    assert order["tenant_id"] == str(market.own.tenant.id)
