"""1P-CU18 cash drawer: opening amount, change given, deposits/withdrawals, closing count and branch isolation.
The shared `market` fixture opens a drawer of 100 Bs. for every cashier; the own variant costs 25 Bs."""
from decimal import Decimal

import pytest

from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_marketplace_transactions import add, call, market, market_api, rejected  # noqa: F401


@pytest.fixture
def cash_api(market_api):
    from app.routes import cash_session_routes

    market_api.app.include_router(cash_session_routes.router, prefix="/api")
    return market_api


def sale(market, **extra):
    return {"items": [{"variant_id": str(market.own.variant.id), "quantity": 1}], **extra}


def drawer(api, cashier):
    from test_marketplace_transactions import headers

    result = api.get("/api/cash-sessions/current", headers=headers(cashier))
    assert result.status_code == 200, result.text
    return result.json().get("data")  # absent when the cashier has no open drawer


def test_cash_sale_records_received_cash_and_change(cash_api, api_db, market):
    cashier = market.staff[0, "cajero"]
    created = call(cash_api, cashier, "POST", "/sales/", 201, json=sale(market, cash_received="50.00"))
    assert (Decimal(str(created["cash_received"])), Decimal(str(created["change_given"]))) == (Decimal("50.00"), Decimal("25.00"))
    current = drawer(cash_api, cashier)
    assert Decimal(str(current["cash_sales"])) == Decimal("25.00")
    assert Decimal(str(current["change_given"])) == Decimal("25.00")
    assert Decimal(str(current["expected_amount"])) == Decimal("125.00")  # 100 opening + 25 sale
    assert [(m["type"], m["method"]) for m in current["movements"]] == [("sale", "cash")]
    rejected(cash_api, api_db, cashier, "POST", "/sales/", 400,
             "El monto recibido (20.00 Bs.) es menor al total a cobrar (25.00 Bs.)", json=sale(market, cash_received="20"))


def test_selling_needs_an_open_drawer_and_closing_reports_the_difference(cash_api, api_db, market):
    cashier = market.staff[0, "cajero"]
    call(cash_api, cashier, "POST", "/sales/", 201, json=sale(market))  # exact amount: no change
    call(cash_api, cashier, "POST", "/cash-sessions/current/movements", 201,
         expected_message="Ingreso de efectivo registrado", json={"type": "deposit", "amount": "10", "reason": "Sencillo para cambio"})
    call(cash_api, cashier, "POST", "/cash-sessions/current/movements", 201,
         expected_message="Retiro de efectivo registrado", json={"type": "withdrawal", "amount": "35", "reason": "Depósito bancario"})
    rejected(cash_api, api_db, cashier, "POST", "/cash-sessions/current/movements", 400,
             "No puedes retirar 500.00 Bs.: la caja tiene 100.00 Bs.", json={"type": "withdrawal", "amount": "500", "reason": "Prueba"})
    closed = call(cash_api, cashier, "POST", "/cash-sessions/current/close",
                  expected_message="Caja cerrada: faltante de 2.00 Bs.", json={"counted_amount": "98", "note": "Faltó sencillo"})
    # 100 + 25 + 10 - 35 = 100 expected; 98 counted.
    assert (Decimal(str(closed["expected_amount"])), Decimal(str(closed["difference"]))) == (Decimal("100.00"), Decimal("-2.00"))
    assert drawer(cash_api, cashier) is None
    rejected(cash_api, api_db, cashier, "POST", "/sales/", 400, "Abre tu caja para registrar ventas", json=sale(market))
    rejected(cash_api, api_db, cashier, "POST", "/payments/qr/sale-intent", 400, "Abre tu caja para registrar ventas",
             json=sale(market))
    opened = call(cash_api, cashier, "POST", "/cash-sessions/open", 201, expected_message="Caja abierta exitosamente",
                  json={"opening_amount": "80"})
    assert Decimal(str(opened["expected_amount"])) == Decimal("80.00")
    rejected(cash_api, api_db, cashier, "POST", "/cash-sessions/open", 409,
             "Ya tienes una caja abierta: ciérrala antes de abrir otra", json={"opening_amount": "10"})


def test_drawers_of_different_branches_never_mix(cash_api, api_db, market):
    own_cashier, other_branch_cashier = market.staff[0, "cajero"], market.staff[1, "cajero"]
    call(cash_api, own_cashier, "POST", "/sales/", 201, json=sale(market))
    own_drawer = drawer(cash_api, own_cashier)
    assert drawer(cash_api, other_branch_cashier)["movements"] == []

    admin = market.staff[0, "administrador"]
    branch0 = call(cash_api, admin, "GET", "/cash-sessions", params={"branch_id": str(market.branches[0].id)})
    assert {row["branch_id"] for row in branch0} == {str(market.branches[0].id)}
    # Another company's branch is invisible even when named explicitly.
    assert call(cash_api, admin, "GET", "/cash-sessions", params={"branch_id": str(market.branches[2].id)}) == []

    manager1 = market.staff[1, "encargado"]
    assert {row["branch_id"] for row in call(cash_api, manager1, "GET", "/cash-sessions")} == {str(market.branches[1].id)}
    rejected(cash_api, api_db, manager1, "GET", f"/cash-sessions/{own_drawer['id']}", 404, "Caja no encontrada")
    rejected(cash_api, api_db, other_branch_cashier, "GET", f"/cash-sessions/{own_drawer['id']}", 404, "Caja no encontrada")
    assert call(cash_api, admin, "GET", f"/cash-sessions/{own_drawer['id']}")["cashier_name"] == "cajero"
