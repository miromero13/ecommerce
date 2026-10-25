"""CU5 photo try-on endpoint on the disposable PostgreSQL schema.

The Hugging Face Space and the garment download are replaced; plan, tenant and
variant checks run against real SQL.
"""
import pytest
from sqlalchemy import text

from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_saas_subscriptions import make_user, plan_of
from test_employee_authorization import headers

JPEG = b"\xff\xd8\xff\xe0" + b"0" * 64


@pytest.fixture
def try_on(api, api_db, catalog, monkeypatch, tmp_path):
    from app.core.config import settings
    from app.routes import garment_routes
    from app.schemas.enums import RolEnum
    from app.services import virtual_try_on_service as service

    calls = []
    result = tmp_path / "result.png"
    result.write_bytes(b"\x89PNG\r\n\x1a\nfake")

    def fake_space(person_path, garment_path, description):
        calls.append((open(person_path, "rb").read(), open(garment_path, "rb").read(), description))
        return result

    monkeypatch.setattr(settings, "huggingface_api_token", "hf_test_only")
    monkeypatch.setattr(service, "_run_space", fake_space)
    monkeypatch.setattr(service, "_read_source_image", lambda url: (b"garment:" + url.encode(), "image/png"))
    api.app.include_router(garment_routes.router, prefix="/api")
    catalog.foreign.variant.image_url = "https://example.invalid/foreign.png"
    api_db.commit()
    api.calls = calls
    api.client_user = make_user(api_db, RolEnum.cliente, email="client@example.com")
    return api


def post(api, variant, user=None, photo=JPEG):
    return api.post("/api/catalog/try-on", headers=headers(user or api.client_user),
                    data={"variant_id": str(variant.id)}, files={"photo": ("me.jpg", photo, "image/jpeg")})


def assert_error(result, code, message):
    assert result.status_code == code, result.text
    assert result.json()["message"] == message


def test_try_on_puts_the_selected_garment_on_the_customer_photo(try_on, catalog):
    result = post(try_on, catalog.foreign.variant)  # foreign company keeps Enterprise
    assert result.status_code == 200, result.text
    body = result.json()
    assert body["message"] == "Prueba virtual generada exitosamente"
    assert body["data"]["mime_type"] == "image/png"
    assert body["data"]["image_data_url"].startswith("data:image/png;base64,")
    [(person, garment, description)] = try_on.calls
    assert person == JPEG
    assert garment == b"garment:https://example.invalid/foreign.png"
    assert description == catalog.foreign.product.name


def test_try_on_requires_the_selling_company_plan(try_on, api_db, catalog):
    plan_of(api_db, catalog.foreign.tenant, "plan_basic")
    assert_error(post(try_on, catalog.foreign.variant), 403,
                 "Esta tienda no tiene el vestidor virtual incluido en su plan")
    assert try_on.calls == []


@pytest.mark.parametrize("case", ["pending_variant", "suspended_company"])
def test_try_on_hides_unpublished_or_suspended_garments(try_on, api_db, catalog, case):
    variant = catalog.foreign.pending_variant if case == "pending_variant" else catalog.foreign.variant
    if case == "suspended_company":
        api_db.execute(text("UPDATE tenants SET status = 'suspended' WHERE id = :id"),
                       {"id": catalog.foreign.tenant.id})
        api_db.commit()
    assert_error(post(try_on, variant), 404, "Prenda no encontrada")
    assert try_on.calls == []


@pytest.mark.parametrize("photo, message", [
    (b"not an image at all", "La foto debe ser una imagen JPG, PNG o WEBP"),
    (b"", "Subí o tomá una foto para probarte la prenda"),
    (JPEG + b"0" * (8 * 1024 * 1024), "La foto supera el tamaño máximo de 8 MB"),
], ids=["not_image", "empty", "too_large"])
def test_try_on_rejects_invalid_photos_before_calling_the_api(try_on, catalog, photo, message):
    assert_error(post(try_on, catalog.foreign.variant, photo=photo), 422, message)
    assert try_on.calls == []


def test_try_on_reports_an_unavailable_space_without_leaking_details(try_on, catalog, monkeypatch):
    from app.services import virtual_try_on_service as service

    def broken(*args):
        raise RuntimeError("ZeroGPU quota exceeded for hf_secret_token")

    monkeypatch.setattr(service, "_run_space", broken)
    result = post(try_on, catalog.foreign.variant)
    assert_error(result, 503, service.UNAVAILABLE)
    assert "hf_" not in result.text


def test_try_on_without_token_is_not_configured(try_on, catalog, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "huggingface_api_token", None)
    assert_error(post(try_on, catalog.foreign.variant), 503, "El vestidor virtual no está configurado")


def test_try_on_is_only_for_customers(try_on, catalog):
    assert_error(post(try_on, catalog.foreign.variant, user=catalog.user), 403,
                 "No tienes permisos para acceder a este recurso")
