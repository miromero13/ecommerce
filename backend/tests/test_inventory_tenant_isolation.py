"""CU1 API regressions: missing tenant predicates/assignments must fail.

No ownership mocks: only external push delivery is disabled. SQL snapshots
include all stock, movements, requests, notifications and tenant counters.
"""
import pytest
from sqlalchemy import text

from test_catalog_tenant_isolation import TABLES, catalog
from test_employee_authorization import DENIED, headers

ROOT = "/api/inventory"
TENANT_DENIED = "No tenés permisos para acceder a los datos de esta empresa"
BRANCH_DENIED = "No tienes permisos para esta sucursal"


def snapshot(db):
    tables = TABLES + ("replenishment_requests", "replenishment_request_items",
                       "notifications", "device_tokens")
    return {table: db.execute(text(
        f"SELECT row_to_json(t)::text FROM {table} t ORDER BY id"
    )).all() for table in tables}


def rejected(api, db, method, path, auth, message, code=403, **kwargs):
    before = snapshot(db)
    result = api.request(method, path, headers=auth, **kwargs)
    assert result.status_code == code, result.text
    assert result.json() == {"statusCode": code, "message": message, "error": "HTTPException"}
    assert snapshot(db) == before


def data(api, path, auth, message, **params):
    result = api.get(path, headers=auth, params=params)
    assert result.status_code == 200, result.text
    assert result.json()["message"] == message
    return result.json()["data"]


@pytest.fixture
def inventory_api(api, monkeypatch):
    from app.routes import inventory_routes
    from app.services import notification_delivery
    api.app.include_router(inventory_routes.router, prefix="/api")
    monkeypatch.setattr(notification_delivery, "_send_push", lambda *args: None)
    return api


@pytest.fixture
def stock(catalog, api_db):
    from app.models.inventory_movement import InventoryMovement
    from app.models.user import User
    from app.schemas.enums import GenderEnum, RolEnum
    from app.schemas.inventory_schema import InventoryMovementTypeEnum
    for group in (catalog.own, catalog.foreign):
        api_db.add(InventoryMovement(
            tenant_id=group.tenant.id, variant_id=group.variant.id,
            branch_id=group.inventory.branch_id, quantity=9,
            movement_type=InventoryMovementTypeEnum.income, created_by=catalog.user.id))
    foreign_admin = User(name="Other admin", email="other-admin@example.com",
                         hashed_password="unused", gender=GenderEnum.femenino,
                         rol=RolEnum.administrador, tenant_id=catalog.foreign.tenant.id,
                         is_active=True)
    api_db.add(foreign_admin)
    api_db.commit()
    return catalog


def movement_payload(stock, **changes):
    return {"variant_id": str(stock.own.variant.id),
            "branch_id": str(stock.branches[0].id), "quantity": 3, **changes}


def transfer_payload(stock, **changes):
    return {"variant_id": str(stock.own.variant.id),
            "from_branch_id": str(stock.branches[0].id),
            "to_branch_id": str(stock.branches[1].id), "quantity": 3, **changes}


def test_admin_lists_only_current_company_despite_forged_query_and_claim(inventory_api, api_db, stock):
    auth = headers(stock.user)
    stock.user.tenant_id = stock.foreign.tenant.id
    api_db.commit()
    rows = data(inventory_api, ROOT + "/consolidated", auth,
                "Inventario consolidado obtenido exitosamente", tenant_id=str(stock.own.tenant.id))
    assert [(r["variant_id"], r["quantity"], r["reserved_quantity"], r["available_quantity"])
            for r in rows] == [(str(stock.foreign.variant.id), 9, 2, 7)]
    rows = data(inventory_api, ROOT + "/movements", auth,
                "Movimientos de inventario obtenidos exitosamente")
    assert [(r["variant_id"], r["quantity"]) for r in rows] == [(str(stock.foreign.variant.id), 9)]


@pytest.mark.parametrize("role", ["administrador", "encargado", "cajero"])
def test_branch_read_retains_own_stock_and_rejects_other_scope(inventory_api, api_db, stock, role):
    from app.schemas.enums import RolEnum
    stock.user.rol = RolEnum(role)
    stock.user.branch_id = stock.branches[0].id
    api_db.commit()
    auth = headers(stock.user)
    rows = data(inventory_api, ROOT + f"/branches/{stock.branches[0].id}", auth,
                "Inventario por sucursal obtenido exitosamente")
    assert [(r["quantity"], r["reserved_quantity"], r["available_quantity"], r["minimum_stock"])
            for r in rows] == [(9, 2, 7, 1)]
    branch = stock.branches[2 if role == "administrador" else 1]
    rejected(inventory_api, api_db, "GET", ROOT + f"/branches/{branch.id}", auth,
             TENANT_DENIED if role == "administrador" else BRANCH_DENIED)


@pytest.mark.parametrize("operation", ["income", "outcome", "threshold"])
@pytest.mark.parametrize("target", ["branch", "variant"])
def test_stock_mutations_reject_foreign_references_atomically(inventory_api, api_db, stock, operation, target):
    payload = movement_payload(stock, **{target + "_id": str(
        stock.branches[2].id if target == "branch" else stock.foreign.variant.id)})
    if operation == "threshold":
        payload.pop("quantity")
        payload["minimum_stock"] = 5
    path = "/threshold" if operation == "threshold" else "/movements/" + operation
    rejected(inventory_api, api_db, "PATCH" if operation == "threshold" else "POST",
             ROOT + path, headers(stock.user), TENANT_DENIED, json=payload)


@pytest.mark.parametrize("target", ["from_branch_id", "to_branch_id", "variant_id"])
def test_transfer_checks_both_branches_and_variant_before_mutation(inventory_api, api_db, stock, target):
    foreign_id = stock.foreign.variant.id if target == "variant_id" else stock.branches[2].id
    rejected(inventory_api, api_db, "POST", ROOT + "/movements/transfer", headers(stock.user),
             TENANT_DENIED, json=transfer_payload(stock, **{target: str(foreign_id)}))


@pytest.mark.parametrize("role,operation", [
    ("cajero", "income"), ("cajero", "outcome"), ("cajero", "transfer"),
    ("cajero", "threshold"), ("encargado", "threshold"),
])
def test_existing_readonly_and_adminonly_roles_do_not_expand(inventory_api, api_db, stock, role, operation):
    from app.schemas.enums import RolEnum
    stock.user.rol = RolEnum(role)
    stock.user.branch_id = stock.branches[0].id
    api_db.commit()
    payload = transfer_payload(stock) if operation == "transfer" else movement_payload(stock)
    if operation == "threshold":
        payload.pop("quantity")
        payload["minimum_stock"] = 2
    rejected(inventory_api, api_db, "PATCH" if operation == "threshold" else "POST",
             ROOT + ("/threshold" if operation == "threshold" else "/movements/" + operation),
             headers(stock.user), DENIED, json=payload)


def test_manager_uses_persisted_branch_for_movement_reads_and_writes(inventory_api, api_db, stock):
    from app.schemas.enums import RolEnum
    stock.user.rol = RolEnum.encargado
    stock.user.branch_id = stock.branches[1].id
    api_db.commit()
    auth = headers(stock.user)
    stock.user.branch_id = stock.branches[0].id
    api_db.commit()
    rows = data(inventory_api, ROOT + "/movements", auth, "Movimientos de inventario obtenidos exitosamente")
    assert [(r["branch_id"], r["quantity"]) for r in rows] == [(str(stock.branches[0].id), 9)]
    for operation in ("income", "outcome"):
        rejected(inventory_api, api_db, "POST", ROOT + "/movements/" + operation, auth,
                 BRANCH_DENIED, json=movement_payload(stock, branch_id=str(stock.branches[1].id)))
    rejected(inventory_api, api_db, "GET", ROOT + "/movements", auth, BRANCH_DENIED,
             params={"branch_id": str(stock.branches[1].id)})
    result = inventory_api.post(ROOT + "/movements/income", headers=auth, json=movement_payload(stock))
    assert result.status_code == 201, result.text
    assert result.json()["message"] == "Ingreso de inventario registrado exitosamente"
    assert result.json()["data"]["quantity"] == 12


def test_manager_transfers_only_out_of_own_branch(inventory_api, api_db, stock):
    from app.schemas.enums import RolEnum
    stock.user.rol = RolEnum.encargado
    stock.user.branch_id = stock.branches[1].id
    api_db.commit()
    auth = headers(stock.user)
    rejected(inventory_api, api_db, "POST", ROOT + "/movements/transfer", auth, BRANCH_DENIED,
             json=transfer_payload(stock))
    stock.user.branch_id = stock.branches[0].id
    api_db.commit()
    result = inventory_api.post(ROOT + "/movements/transfer", headers=auth, json=transfer_payload(stock))
    assert result.status_code == 201, result.text
    assert result.json()["message"] == "Traspaso de inventario registrado exitosamente"


def test_own_transfer_income_outcome_threshold_preserve_reserved_arithmetic(inventory_api, api_db, stock):
    auth = headers(stock.user)
    result = inventory_api.post(ROOT + "/movements/transfer", headers=auth, json=transfer_payload(stock))
    assert result.status_code == 201, result.text
    assert result.json()["message"] == "Traspaso de inventario registrado exitosamente"
    assert len(result.json()["data"]["movements"]) == 2
    for operation, expected, message in (("income", 9, "Ingreso de inventario registrado exitosamente"),
                                         ("outcome", 6, "Salida de inventario registrada exitosamente")):
        result = inventory_api.post(ROOT + "/movements/" + operation, headers=auth, json=movement_payload(stock))
        assert result.status_code == 201, result.text
        assert result.json()["message"] == message
        assert result.json()["data"]["quantity"] == expected
    result = inventory_api.patch(ROOT + "/threshold", headers=auth, json={
        "variant_id": str(stock.own.variant.id), "branch_id": str(stock.branches[1].id), "minimum_stock": 2})
    assert result.status_code == 200, result.text
    assert result.json()["message"] == "Stock mínimo actualizado exitosamente"
    rows = data(inventory_api, ROOT + "/consolidated", auth, "Inventario consolidado obtenido exitosamente")
    assert [(r["quantity"], r["reserved_quantity"], r["available_quantity"]) for r in rows] == [(9, 2, 7)]
    assert {(r["branch_id"], r["quantity"], r["reserved_quantity"], r["minimum_stock"])
            for r in rows[0]["branches"]} == {(str(stock.branches[0].id), 6, 2, 1), (str(stock.branches[1].id), 3, 0, 2)}
    for table in ("inventory", "inventory_movements"):
        tenants = api_db.execute(text(f"SELECT tenant_id FROM {table} WHERE variant_id = :id"),
                                 {"id": stock.own.variant.id}).scalars().all()
        assert tenants and set(tenants) == {stock.own.tenant.id}


@pytest.mark.parametrize("operation,message,changes", [
    ("outcome", "No hay stock disponible suficiente", {"quantity": 8}),
    ("transfer", "No hay stock disponible suficiente en la sucursal origen", {"quantity": 8}),
    ("transfer", "La sucursal origen y destino no pueden ser iguales", {"same_branch": True}),
])
def test_existing_stock_rejections_leave_every_counter_unchanged(inventory_api, api_db, stock, operation, message, changes):
    payload = transfer_payload(stock) if operation == "transfer" else movement_payload(stock)
    if changes.get("same_branch"):
        payload["to_branch_id"] = payload["from_branch_id"]
    else:
        payload.update(changes)
    rejected(inventory_api, api_db, "POST", ROOT + "/movements/" + operation,
             headers(stock.user), message, 400, json=payload)


@pytest.mark.parametrize("operation", ["income", "threshold"])
def test_new_stock_rows_receive_actor_company(inventory_api, api_db, stock, operation):
    payload = movement_payload(stock, branch_id=str(stock.branches[1].id))
    if operation == "threshold":
        payload.pop("quantity")
        payload["minimum_stock"] = 2
    result = inventory_api.request("PATCH" if operation == "threshold" else "POST",
                                   ROOT + ("/threshold" if operation == "threshold" else "/movements/income"),
                                   headers=headers(stock.user), json=payload)
    assert result.status_code == (200 if operation == "threshold" else 201), result.text
    assert result.json()["message"] == ("Stock mínimo actualizado exitosamente" if operation == "threshold"
                                        else "Ingreso de inventario registrado exitosamente")
    assert api_db.execute(text("SELECT tenant_id FROM inventory WHERE branch_id = :id"),
                          {"id": stock.branches[1].id}).scalar_one() == stock.own.tenant.id


def test_low_stock_notifications_never_reach_foreign_admins(inventory_api, api_db, stock):
    result = inventory_api.post(ROOT + "/movements/outcome", headers=headers(stock.user),
                                json=movement_payload(stock, quantity=7))
    assert result.status_code == 201, result.text
    assert result.json()["message"] == "Salida de inventario registrada exitosamente"
    assert result.json()["data"]["quantity"] == 2
    recipients = api_db.execute(text("SELECT user_id FROM notifications ORDER BY user_id")).scalars().all()
    assert recipients == [stock.user.id]
