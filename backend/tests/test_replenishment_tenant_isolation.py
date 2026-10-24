"""CU1: real API request ownership, tenant references and receipt effects."""
from types import SimpleNamespace

import pytest
from sqlalchemy import text

from test_employee_authorization import DENIED, headers
from test_inventory_tenant_isolation import (
    catalog, data, inventory_api, rejected, stock,
)

ROOT = "/api/replenishment/requests"


@pytest.fixture
def replenishment_api(inventory_api):
    from app.routes import replenishment_routes
    inventory_api.app.include_router(replenishment_routes.router, prefix="/api")
    return inventory_api


@pytest.fixture
def requests(api_db, stock):
    from app.models.replenishment_request import ReplenishmentRequest
    from app.models.replenishment_request_item import ReplenishmentRequestItem
    from app.schemas.replenishment_schema import ReplenishmentStatusEnum
    rows = []
    for group, branch in ((stock.own, stock.branches[0]), (stock.own, stock.branches[1]),
                           (stock.foreign, stock.branches[2])):
        row = ReplenishmentRequest(tenant_id=group.tenant.id, provider_id=group.provider.id,
                                   branch_id=branch.id, requested_by=stock.user.id,
                                   status=ReplenishmentStatusEnum.awaiting_receipt)
        row.items = [ReplenishmentRequestItem(variant_id=group.variant.id, requested_quantity=4)]
        api_db.add(row)
        rows.append(row)
    api_db.commit()
    return SimpleNamespace(own=rows[0], sibling=rows[1], foreign=rows[2])


def payload(stock, **changes):
    return {"provider_id": str(stock.own.provider.id), "branch_id": str(stock.branches[0].id),
            "items": [{"variant_id": str(stock.own.variant.id), "requested_quantity": 4}], **changes}


@pytest.mark.parametrize("role", ["administrador", "encargado", "proveedor"])
def test_request_list_obeys_current_tenant_branch_and_provider(replenishment_api, api_db, stock, requests, role):
    from app.schemas.enums import RolEnum
    user = stock.own.supplier_user if role == "proveedor" else stock.user
    user.rol = RolEnum(role)
    user.branch_id = stock.branches[0].id
    api_db.commit()
    auth = headers(user)
    expected = {str(requests.own.id), str(requests.sibling.id)}
    if role == "encargado":
        expected = {str(requests.own.id)}
    if role == "administrador":
        user.tenant_id = stock.foreign.tenant.id
        api_db.commit()
        expected = {str(requests.foreign.id)}
    rows = data(replenishment_api, ROOT, auth, "Solicitudes obtenidas exitosamente",
                tenant_id=str(stock.own.tenant.id))
    assert {r["id"] for r in rows} == expected


@pytest.mark.parametrize("target,message", [
    ("provider", "El proveedor no existe o no está activo"),
    ("branch", "La sucursal de destino no existe o está inactiva"),
    ("variant", "La variante no está asignada a este proveedor"),
])
def test_create_validates_each_reference_tenant_before_insert(replenishment_api, api_db, stock, target, message):
    changes = {}
    if target == "variant":
        # Keep the existing provider-assignment predicate satisfied: tenant
        # validation, not an incidental provider mismatch, must reject this.
        stock.foreign.product.provider_id = stock.own.provider.id
        api_db.commit()
        changes["items"] = [{"variant_id": str(stock.foreign.variant.id), "requested_quantity": 4}]
    else:
        changes[target + "_id"] = str(stock.foreign.provider.id if target == "provider" else stock.branches[2].id)
    rejected(replenishment_api, api_db, "POST", ROOT, headers(stock.user), message, 400,
             json=payload(stock, **changes))


@pytest.mark.parametrize("role", ["administrador", "encargado"])
def test_create_assigns_tenant_and_preserves_manager_branch_override(replenishment_api, api_db, stock, role):
    from app.schemas.enums import RolEnum
    stock.user.rol = RolEnum(role)
    stock.user.branch_id = stock.branches[0].id
    api_db.commit()
    auth = headers(stock.user, tenant_id=str(stock.foreign.tenant.id))
    branch = stock.branches[1] if role == "encargado" else stock.branches[0]
    result = replenishment_api.post(ROOT, headers=auth, json=payload(stock, branch_id=str(branch.id)))
    assert result.status_code == 201, result.text
    assert result.json()["message"] == "Solicitud creada exitosamente"
    row = result.json()["data"]
    assert (row["status"], row["branch_id"], row["requested_by"]) == (
        "requested", str(stock.branches[0].id), str(stock.user.id))
    assert row["items"][0]["requested_quantity"] == 4
    assert api_db.execute(text("SELECT tenant_id FROM replenishment_requests WHERE id = :id"),
                          {"id": row["id"]}).scalar_one() == stock.own.tenant.id
    assert row["id"] in {r["id"] for r in data(replenishment_api, ROOT, auth, "Solicitudes obtenidas exitosamente")}


@pytest.mark.parametrize("role", ["administrador", "encargado", "proveedor"])
def test_foreign_request_transition_is_not_found_without_receipt_effects(replenishment_api, api_db, stock, requests, role):
    from app.schemas.enums import RolEnum
    user = stock.own.supplier_user if role == "proveedor" else stock.user
    user.rol = RolEnum(role)
    user.branch_id = stock.branches[0].id
    api_db.commit()
    rejected(replenishment_api, api_db, "PATCH", ROOT + f"/{requests.foreign.id}/status",
             headers(user), "Solicitud no encontrada", 404, json={"status": "delivered"})


def test_manager_cannot_receive_sibling_branch_request(replenishment_api, api_db, stock, requests):
    from app.schemas.enums import RolEnum
    stock.user.rol = RolEnum.encargado
    stock.user.branch_id = stock.branches[0].id
    api_db.commit()
    rejected(replenishment_api, api_db, "PATCH", ROOT + f"/{requests.sibling.id}/status",
             headers(stock.user), "No tienes permisos para confirmar la recepción", json={"status": "delivered"})


@pytest.mark.parametrize("operation", ["list", "create", "receive"])
def test_cashier_gets_no_replenishment_permissions(replenishment_api, api_db, stock, requests, operation):
    from app.schemas.enums import RolEnum
    stock.user.rol = RolEnum.cajero
    stock.user.branch_id = stock.branches[0].id
    api_db.commit()
    method, path, kwargs = {
        "list": ("GET", ROOT, {}), "create": ("POST", ROOT, {"json": payload(stock)}),
        "receive": ("PATCH", ROOT + f"/{requests.own.id}/status", {"json": {"status": "delivered"}}),
    }[operation]
    rejected(replenishment_api, api_db, method, path, headers(stock.user), DENIED, **kwargs)


@pytest.mark.parametrize("existing_stock", [True, False])
def test_supplier_lifecycle_and_single_receipt_keep_stock_accounting(replenishment_api, api_db, stock, requests, existing_stock):
    from app.schemas.replenishment_schema import ReplenishmentStatusEnum
    request = requests.own if existing_stock else requests.sibling
    request.status = ReplenishmentStatusEnum.requested
    api_db.commit()
    path = ROOT + f"/{request.id}/status"
    for state in ("accepted", "preparing", "awaiting_receipt"):
        result = replenishment_api.patch(path, headers=headers(stock.own.supplier_user), json={"status": state})
        assert result.status_code == 200, result.text
        assert result.json()["message"] == "Estado actualizado exitosamente"
        assert result.json()["data"]["status"] == state
    result = replenishment_api.patch(path, headers=headers(stock.user), json={"status": "delivered"})
    assert result.status_code == 200, result.text
    assert result.json()["message"] == "Estado actualizado exitosamente"
    row = result.json()["data"]
    assert (row["status"], row["delivered_by"]) == ("delivered", str(stock.user.id))
    assert row["delivered_at"] is not None
    rows = data(replenishment_api, f"/api/inventory/branches/{request.branch_id}", headers(stock.user),
                "Inventario por sucursal obtenido exitosamente")
    assert [(r["quantity"], r["reserved_quantity"], r["minimum_stock"], r["available_quantity"])
            for r in rows] == ([(13, 2, 1, 11)] if existing_stock else [(4, 0, 0, 4)])
    for table in ("inventory", "inventory_movements"):
        tenants = api_db.execute(text(f"SELECT tenant_id FROM {table} WHERE branch_id = :branch AND variant_id = :variant"),
                                 {"branch": request.branch_id, "variant": stock.own.variant.id}).scalars().all()
        assert tenants and set(tenants) == {stock.own.tenant.id}
    movements = data(replenishment_api, "/api/inventory/movements", headers(stock.user),
                     "Movimientos de inventario obtenidos exitosamente", branch_id=str(request.branch_id))
    receipts = [r for r in movements if r["note"] == f"Solicitud de reposición {request.id}"]
    assert [(r["movement_type"], r["quantity"], r["created_by"]) for r in receipts] == [("income", 4, str(stock.user.id))]
    rejected(replenishment_api, api_db, "PATCH", path, headers(stock.user),
             "La solicitud no está pendiente de recepción", 400, json={"status": "delivered"})


@pytest.mark.parametrize("target,message", [
    ("provider", "El proveedor no existe o no está activo"),
    ("branch", "La sucursal de destino no existe o está inactiva"),
    ("variant", "La variante no está asignada a este proveedor"),
])
def test_receipt_revalidates_persisted_references_before_stock_changes(replenishment_api, api_db, stock, requests, target, message):
    if target == "variant":
        requests.own.items[0].variant_id = stock.foreign.variant.id
    else:
        setattr(requests.own, target + "_id", stock.foreign.provider.id if target == "provider" else stock.branches[2].id)
    api_db.commit()
    rejected(replenishment_api, api_db, "PATCH", ROOT + f"/{requests.own.id}/status",
             headers(stock.user), message, 400, json={"status": "delivered"})


def test_duplicate_items_still_rejected_without_request_or_counter_changes(replenishment_api, api_db, stock):
    body = payload(stock)
    body["items"] *= 2
    rejected(replenishment_api, api_db, "POST", ROOT, headers(stock.user),
             "No puedes repetir variantes en una solicitud", 400, json=body)
