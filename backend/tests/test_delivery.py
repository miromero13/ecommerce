"""CU20 delivery: distance-based shipping, platform drivers shared by every company, PIN hand-over."""
from decimal import ROUND_HALF_UP, Decimal

import pytest
from sqlalchemy import text

from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_marketplace_transactions import add, call, market, market_api, rejected, stock  # noqa: F401

# Branch A1 at Plaza 24 de Septiembre (Santa Cruz); destinations measured from it.
BRANCH = (-17.783300, -63.182100)
NEAR = {"latitude": -17.7833, "longitude": -63.1450}   # ~3.9 km east
FAR = {"latitude": -17.9500, "longitude": -63.1821}    # ~18.5 km south (outside 15 km)


@pytest.fixture
def delivery_api(market_api, api_db, market):
    from app.models.user import User
    from app.routes import delivery_routes
    from app.schemas.enums import GenderEnum, RolEnum

    market_api.app.include_router(delivery_routes.router, prefix="/api")
    for branch in market.branches:
        branch.latitude, branch.longitude = BRANCH
    market.drivers = [User(name=f"Driver {n}", email=f"driver{n}@example.com", hashed_password="unused",
                           gender=GenderEnum.masculino, rol=RolEnum.delivery, is_active=True) for n in (1, 2)]
    api_db.add_all(market.drivers)
    api_db.commit()
    return market_api


def delivery_checkout(api, market, method="cash"):
    add(api, market)
    path = "/payments/cash/checkout" if method == "cash" else "/payments/stripe/checkout"
    return call(api, market.customer, "POST", path, 201, json={
        "pickup_branch_id": str(market.branches[0].id),
        "delivery": {"address": "Av. San Martín 450", "reference": "Edificio azul", **NEAR},
    })


def test_quote_charges_by_distance_and_enforces_coverage(delivery_api, api_db, market):
    quote = call(delivery_api, market.customer, "POST", "/delivery/quotes",
                 json={"branch_id": str(market.branches[0].id), **NEAR})
    assert 3.8 < quote["distance_km"] < 4.0
    assert Decimal(str(quote["shipping_cost"])) == (Decimal("8") + Decimal("2.5") * Decimal(str(quote["distance_km"]))).quantize(Decimal("0.01"), ROUND_HALF_UP)
    rejected(delivery_api, api_db, market.customer, "POST", "/delivery/quotes", 422,
             "La dirección de entrega se encuentra fuera del radio de cobertura",
             json={"branch_id": str(market.branches[0].id), **FAR})


def test_cash_on_delivery_flow_across_companies(delivery_api, api_db, market):
    order = delivery_checkout(delivery_api, market)
    assert order["fulfillment_type"] == "delivery"
    assert Decimal(str(order["total_amount"])) == Decimal("25") + Decimal(str(order["shipping_cost"]))
    mine = call(delivery_api, market.customer, "GET", "/delivery/my-orders")
    pin = mine[0]["delivery_pin"]
    assert len(pin) == 4 and pin.isdigit()

    rejected(delivery_api, api_db, market.staff[0, "cajero"], "POST", f"/orders/{order['id']}/hand-over", 400,
             "Este pedido se entrega a domicilio", json={"pickup_code": order["pickup_code"]})
    call(delivery_api, market.staff[0, "encargado"], "POST", f"/orders/{order['id']}/ready")

    driver, other = market.drivers
    pool = call(delivery_api, driver, "GET", "/delivery/available")
    assert [(o["order_id"], o["tenant_name"]) for o in pool] == [(order["id"], market.own.tenant.name)]
    assert "delivery_pin" not in pool[0]
    call(delivery_api, driver, "POST", f"/delivery/orders/{order['id']}/claim")
    rejected(delivery_api, api_db, other, "POST", f"/delivery/orders/{order['id']}/claim", 409,
             "Otro repartidor ya tomó este pedido")
    assert [o["status"] for o in call(delivery_api, driver, "GET", "/delivery/routes")] == ["in_transit"]

    rejected(delivery_api, api_db, other, "POST", "/delivery/confirm-delivery", 404, "Pedido no encontrado en tu hoja de ruta",
             json={"order_id": order["id"], "security_pin": pin})
    rejected(delivery_api, api_db, driver, "POST", "/delivery/confirm-delivery", 400, "El código PIN de seguridad es incorrecto",
             json={"order_id": order["id"], "security_pin": "0000" if pin != "0000" else "1111"})
    quantity, reserved = stock(api_db, market.own.variant, market.branches[0])
    done = call(delivery_api, driver, "POST", "/delivery/confirm-delivery",
                expected_message="Entrega confirmada y registrada exitosamente",
                json={"order_id": order["id"], "security_pin": pin})
    assert done["delivered_at"]
    assert stock(api_db, market.own.variant, market.branches[0]) == (quantity - 1, reserved - 1)
    # Driver collected cash for the platform: the company is owed the garments, not the shipping.
    row = api_db.execute(text("SELECT tenant_id, method, gross_amount FROM payment_transactions")).one()
    assert tuple(row) == (market.own.tenant.id, "cash", Decimal("25.00"))


def test_company_admins_cannot_create_platform_drivers(delivery_api, api_db, market):
    rejected(delivery_api, api_db, market.staff[0, "administrador"], "POST", "/delivery/drivers", 403)
    driver = call(delivery_api, market.superadmin if hasattr(market, "superadmin") else _superadmin(api_db, market),
                  "POST", "/delivery/drivers", 201, json={
                      "name": "Nuevo Repartidor", "email": "nuevo.driver@example.com",
                      "password": "Secreto123!", "gender": "masculino"})
    assert (driver["rol"], driver["tenant_id"], driver["branch_id"]) == ("delivery", None, None)


def _superadmin(db, market):
    from app.models.user import User
    from app.schemas.enums import GenderEnum, RolEnum

    market.superadmin = User(name="Root", email="root@example.com", hashed_password="unused",
                             gender=GenderEnum.femenino, rol=RolEnum.superadministrador, is_active=True)
    db.add(market.superadmin)
    db.commit()
    return market.superadmin


def test_platform_driver_cannot_read_company_staff_data(delivery_api, api_db, market):
    # Without a company, a driver must never fall into the global (all companies) staff scope.
    rejected(delivery_api, api_db, market.drivers[0], "GET", "/branches/", 403)
