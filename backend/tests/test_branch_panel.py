"""Admin branch panel: the administrator lists the orders of ONE branch of their company, never another company's."""
from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_marketplace_transactions import add, call, market, market_api, rejected  # noqa: F401


def test_admin_sees_only_the_orders_of_the_branch_it_enters(market_api, api_db, market):
    add(market_api, market)
    order = call(market_api, market.customer, "POST", "/payments/cash/checkout", 201,
                 json={"pickup_branch_id": str(market.branches[0].id)})
    admin = market.staff[0, "administrador"]
    branch0 = call(market_api, admin, "GET", "/orders/branch", params={"branch_id": str(market.branches[0].id)})
    assert [row["id"] for row in branch0] == [order["id"]]
    assert branch0[0]["pickup_code"] is None  # staff never read the customer's pickup code
    assert call(market_api, admin, "GET", "/orders/branch", params={"branch_id": str(market.branches[1].id)}) == []
    rejected(market_api, api_db, admin, "GET", "/orders/branch", 404, "Sucursal no encontrada",
             params={"branch_id": str(market.branches[2].id)})  # another company's branch
    rejected(market_api, api_db, admin, "GET", "/orders/branch", 422, "branch_id es requerido")
