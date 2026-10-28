"""CU6: every customer signal feeds the model (till purchases, favorites), retraining uses them,
suspended companies are never recommended, and errors are in Spanish."""
import pytest
from sqlalchemy import text

from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_marketplace_transactions import call, market, market_api, rejected  # noqa: F401


@pytest.fixture
def rec_api(market_api):
    from app.routes import recommendation_routes, wishlist_routes

    market_api.app.include_router(recommendation_routes.router, prefix="/api")
    market_api.app.include_router(wishlist_routes.router, prefix="/api")
    return market_api


def signals(db, user):
    return sorted(tuple(r) for r in db.execute(text(
        "SELECT interaction_type, weight FROM user_product_interactions WHERE user_id = :u"), {"u": user.id}))


def recommended(api, market):
    data = call(api, market.customer, "GET", f"/recommendations/collaborative/user/{market.customer.id}")
    return data["logic_type"], {row["product_id"] for row in data["recommendations"]}


def test_till_purchase_and_favorites_are_signals_and_retraining_uses_them(rec_api, api_db, market):
    from app.services.recommendation_service import train

    call(rec_api, market.customer, "POST", "/wishlist/items", 201, json={"product_id": str(market.foreign.variant.product_id)})
    call(rec_api, market.customer, "DELETE", f"/wishlist/items/{market.foreign.variant.product_id}")
    call(rec_api, market.customer, "POST", "/wishlist/items", 201, json={"product_id": str(market.foreign.variant.product_id)})
    call(rec_api, market.staff[0, "cajero"], "POST", "/sales/", 201, json={
        "items": [{"variant_id": str(market.own.variant.id), "quantity": 1}], "customer_email": market.customer.email})
    # The favorite counts once; the identified till purchase counts like a web purchase.
    assert signals(api_db, market.customer) == [("completed_order", 5), ("wishlist", 3)]

    _, before = recommended(rec_api, market)
    assert str(market.own.variant.product_id) not in before  # already bought in store
    train(api_db)  # what the nightly job runs
    logic, _ = recommended(rec_api, market)
    assert logic == "implicit_als"


def test_suspended_company_is_never_recommended(rec_api, api_db, market):
    from app.schemas.enums import TenantStatusEnum

    foreign = str(market.foreign.variant.product_id)
    assert foreign in recommended(rec_api, market)[1]
    market.foreign.tenant.status = TenantStatusEnum.suspended
    api_db.commit()
    assert foreign not in recommended(rec_api, market)[1]


def test_customer_only_reads_own_recommendations_in_spanish(rec_api, api_db, market):
    rejected(rec_api, api_db, market.customer, "GET", f"/recommendations/collaborative/user/{market.other.id}", 403,
             "Solo puedes consultar tus propias recomendaciones")


def test_paying_two_sizes_of_the_same_garment_records_one_purchase_signal(rec_api, api_db, market):
    from app.models.inventory import Inventory
    from app.models.product_variant import ProductVariant
    from test_marketplace_transactions import checkout, pay

    own = market.own.variant
    other_size = ProductVariant(tenant_id=own.tenant_id, product_id=own.product_id, sku=own.sku + "-XL",
                                price=own.price, status=own.status)
    api_db.add(other_size)
    api_db.flush()
    api_db.add(Inventory(tenant_id=own.tenant_id, variant_id=other_size.id, branch_id=market.branches[0].id, quantity=5))
    api_db.commit()
    for variant in (own, other_size):
        call(rec_api, market.customer, "POST", "/cart/items", 201, json={
            "variant_id": str(variant.id), "branch_id": str(market.branches[0].id), "quantity": 1})
    order = checkout(rec_api, market)
    pay(rec_api, market, order)  # used to fail on the unique (order, product, type) signal
    assert call(rec_api, market.customer, "GET", f"/orders/{order['id']}")["payment_status"] == "paid"
    assert [s for s in signals(api_db, market.customer) if s[0] == "completed_order"] == [("completed_order", 5)]
