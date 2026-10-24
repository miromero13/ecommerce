"""CU1: missing provider/user tenant predicates must fail real API contracts."""
from types import SimpleNamespace

import pytest

from test_catalog_tenant_isolation import catalog, snapshot
from test_employee_authorization import headers


ROOT = "/api/providers"


@pytest.fixture(autouse=True)
def provider_routes(api):
    from app.routes.provider_routes import router
    api.app.include_router(router, prefix="/api")


def data(api, path, user):
    result = api.get(ROOT + path, headers=headers(user))
    assert result.status_code == 200, result.text
    return result.json()["data"]


def reject(api, db, user, method, path, message, code=404, **kwargs):
    before = snapshot(db)
    result = api.request(method, ROOT + path, headers=headers(user), **kwargs)
    assert result.status_code == code, result.text
    assert result.json() == {"statusCode": code, "message": message, "error": "HTTPException"}
    assert snapshot(db) == before


def payload(**changes):
    return {"business_name": "New supplier", "contact_name": "New contact",
            "email": "new-supplier@example.com", "gender": "femenino", **changes}


def test_admin_lists_only_own_providers_and_products(api, catalog):
    assert [row["id"] for row in data(api, "/", catalog.user)] == [str(catalog.own.provider.id)]
    products = data(api, f"/{catalog.own.provider.id}/products", catalog.user)
    assert {row["id"] for row in products} == {str(catalog.own.product.id), str(catalog.own.pending.id)}


@pytest.mark.parametrize("method,suffix,kwargs", [
    ("GET", "/products", {}),
    ("PATCH", "/status", {"json": {"status": "suspended"}}),
    ("PUT", "", {"json": payload(status="suspended")}),
    ("DELETE", "", {}),
])
def test_foreign_provider_rejected_before_linked_user_or_products_change(api, api_db, catalog, method, suffix, kwargs):
    provider_id = catalog.foreign.provider.id
    # The product-detail endpoint already has a non-ID-specific not-found contract.
    message = "Proveedor no encontrado" if method == "GET" else f"Proveedor con id {provider_id} no encontrado"
    reject(api, api_db, catalog.user, method, f"/{provider_id}{suffix}", message, **kwargs)


def test_create_assigns_company_to_supplier_and_login_user(api, api_db, catalog):
    from app.schemas.enums import RolEnum
    result = api.post(ROOT + "/", headers=headers(catalog.user), json=payload(password="safe-password"))
    assert result.status_code == 201, result.text
    assert result.json()["message"] == "Proveedor creado exitosamente"
    created = result.json()["data"]
    assert created["email"] == "new-supplier@example.com"
    assert {row["id"] for row in data(api, "/", catalog.user)} == {str(catalog.own.provider.id), created["id"]}
    linked = SimpleNamespace(id=created["user_id"], rol=RolEnum.proveedor,
                             tenant_id=catalog.own.tenant.id, branch_id=None)
    profile = api.get("/api/users/me", headers=headers(linked))
    assert profile.status_code == 200, profile.text
    assert profile.json()["data"]["tenant_id"] == str(catalog.own.tenant.id)
    catalog.user.tenant_id = catalog.foreign.tenant.id
    api_db.commit()
    assert [row["id"] for row in data(api, "/", catalog.user)] == [str(catalog.foreign.provider.id)]


def test_own_provider_update_status_and_delete_preserve_management(api, catalog):
    provider_id = catalog.own.provider.id
    auth = headers(catalog.user)
    result = api.put(ROOT + f"/{provider_id}", headers=auth, json=payload())
    assert result.status_code == 200, result.text
    assert result.json()["message"] == "Proveedor actualizado exitosamente"
    assert data(api, "/", catalog.user)[0]["business_name"] == "New supplier"
    result = api.patch(ROOT + f"/{provider_id}/status", headers=auth, json={"status": "suspended"})
    assert result.status_code == 200, result.text
    assert result.json()["message"] == "Estado de proveedor actualizado exitosamente"
    assert data(api, "/", catalog.user)[0]["status"] == "suspended"
    result = api.get("/api/users/me", headers=headers(catalog.own.supplier_user))
    assert result.status_code == 403
    assert result.json()["message"] == "Usuario inactivo"
    result = api.delete(ROOT + f"/{provider_id}", headers=auth)
    assert result.status_code == 200, result.text
    assert result.json()["message"] == "Proveedor eliminado exitosamente"
    assert data(api, "/", catalog.user) == []
    detail = api.get(f"/api/catalog/products/{catalog.own.product.id}")
    assert detail.status_code == 200, detail.text
    assert detail.json()["data"]["provider_id"] is None


def test_supplier_self_availability_preserves_owned_quantity_and_rejects_foreign_batch(api, api_db, catalog):
    supplier = catalog.own.supplier_user
    path = "/me/availability"
    result = api.put(ROOT + path, headers=headers(supplier), json={"updates": [
        {"variant_id": str(catalog.own.variant.id), "quantity": 11}]})
    assert result.status_code == 200, result.text
    assert result.json()["message"] == "Disponibilidad actualizada exitosamente"
    assert result.json()["data"] == [{"variant_id": str(catalog.own.variant.id), "quantity": 11}]
    products_before = data(api, "/me/products", supplier)
    assert {row["id"] for row in products_before} == {str(catalog.own.product.id), str(catalog.own.pending.id)}
    active = next(row for row in products_before if row["id"] == str(catalog.own.product.id))
    assert active["variants"][0]["provider_quantity"] == 11
    reject(api, api_db, supplier, "PUT", path,
           "La variante no pertenece a un producto asignado a este proveedor", 403,
           json={"updates": [{"variant_id": str(catalog.own.variant.id), "quantity": 99},
                             {"variant_id": str(catalog.foreign.variant.id), "quantity": 99}]})
    assert data(api, "/me/products", supplier) == products_before


@pytest.mark.parametrize("path,method,kwargs", [
    ("/me/products", "GET", {}),
    ("/me/availability", "PUT", {"json": {"updates": []}}),
])
def test_supplier_profile_cannot_survive_company_reassignment(api, api_db, catalog, path, method, kwargs):
    supplier = catalog.own.supplier_user
    supplier.tenant_id = catalog.foreign.tenant.id
    api_db.commit()
    reject(api, api_db, supplier, method, path, "Proveedor no encontrado", **kwargs)


def test_provider_products_exclude_foreign_rows_even_with_same_provider_id(api, api_db, catalog):
    catalog.foreign.product.provider_id = catalog.own.provider.id
    api_db.commit()
    for path, user in ((f"/{catalog.own.provider.id}/products", catalog.user),
                       ("/me/products", catalog.own.supplier_user)):
        assert {row["id"] for row in data(api, path, user)} == {str(catalog.own.product.id), str(catalog.own.pending.id)}
    reject(api, api_db, catalog.own.supplier_user, "PUT", "/me/availability",
           "La variante no pertenece a un producto asignado a este proveedor", 403,
           json={"updates": [{"variant_id": str(catalog.foreign.variant.id), "quantity": 99}]})
