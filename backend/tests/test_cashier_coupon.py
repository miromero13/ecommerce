"""CU15: the cashier applies a coupon in store, identifying a registered customer by email."""
from decimal import Decimal

from sqlalchemy import text

from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_marketplace_transactions import call, coupons, market, market_api, rejected  # noqa: F401


def sale(market, coupon=None, email=None):
    body = {"items": [{"variant_id": str(market.own.variant.id), "quantity": 1}]}
    if coupon:
        body["promotion_code"] = coupon
    if email:
        body["customer_email"] = email
    return body


def usages(db):
    return [tuple(r) for r in db.execute(text("SELECT promotion_code_id, user_id FROM promotion_code_usages"))]


def test_cashier_coupon_discounts_the_sale_and_records_one_use(market_api, api_db, market, coupons):
    cashier = market.staff[0, "cajero"]
    created = call(market_api, cashier, "POST", "/sales/", 201,
                   json=sale(market, coupons[0].code, market.customer.email))
    assert Decimal(str(created["discount_amount"])) == Decimal("5")
    assert Decimal(str(created["total_amount"])) == Decimal("20")
    assert created["customer_id"] == str(market.customer.id)
    assert usages(api_db) == [(coupons[0].id, market.customer.id)]
    rejected(market_api, api_db, cashier, "POST", "/sales/", 400, "Ya utilizaste este código promocional",
             json=sale(market, coupons[0].code, market.customer.email))


def test_cashier_coupon_requires_a_registered_customer(market_api, api_db, market, coupons):
    cashier = market.staff[0, "cajero"]
    rejected(market_api, api_db, cashier, "POST", "/sales/", 400,
             "Ingresa el correo del cliente registrado para aplicar el cupón", json=sale(market, coupons[0].code))
    rejected(market_api, api_db, cashier, "POST", "/sales/", 400,
             "No existe un cliente registrado con ese correo",
             json=sale(market, coupons[0].code, "nadie@example.com"))


def test_cashier_cannot_use_another_company_coupon(market_api, api_db, market, coupons):
    rejected(market_api, api_db, market.staff[0, "cajero"], "POST", "/sales/", 400,
             "El código promocional no existe, está inactivo o fuera de vigencia",
             json=sale(market, coupons[1].code, market.customer.email))


def test_coupon_does_not_combine_with_products_on_sale(market_api, api_db, market, coupons):
    market.own.variant.product.discount_type, market.own.variant.product.discount_value = "fixed", 2
    api_db.commit()
    rejected(market_api, api_db, market.staff[0, "cajero"], "POST", "/sales/", 400,
             "El cupón no se puede combinar con productos en oferta",
             json=sale(market, coupons[0].code, market.customer.email))


def test_qr_quote_includes_the_coupon_discount(market_api, api_db, market, coupons):
    qr = call(market_api, market.staff[0, "cajero"], "POST", "/payments/qr/sale-intent", 201,
              json=sale(market, coupons[0].code, market.customer.email))
    assert Decimal(str(qr["amount"])) == Decimal("20")
    assert usages(api_db) == []  # the quote is a rolled-back dry run
