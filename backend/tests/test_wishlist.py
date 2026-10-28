"""CU16: customer wishlist (favorites) with move-to-cart."""
import pytest

from test_catalog_tenant_isolation import catalog  # noqa: F401 (shared fixture)
from test_marketplace_transactions import add, call, market, market_api, rejected  # noqa: F401


@pytest.fixture
def wishlist_api(market_api):
    from app.routes import wishlist_routes

    market_api.app.include_router(wishlist_routes.router, prefix="/api")
    return market_api


def save(api, market, product_id=None):
    return call(api, market.customer, "POST", "/wishlist/items", 201,
                expected_message="Prenda añadida a tu lista de deseos",
                json={"product_id": str(product_id or market.own.variant.product_id)})


def test_customer_saves_lists_and_removes_favorites(wishlist_api, api_db, market):
    save(wishlist_api, market)
    items = call(wishlist_api, market.customer, "GET", "/wishlist", expected_message="Lista de deseos obtenida exitosamente")
    assert [(i["product_id"], i["tenant_name"], i["in_stock"]) for i in items] == [
        (str(market.own.variant.product_id), market.own.tenant.name, True)]
    assert items[0]["variants"][0]["id"] == str(market.own.variant.id)
    assert call(wishlist_api, market.other, "GET", "/wishlist") == []  # favorites are private
    call(wishlist_api, market.customer, "DELETE", f"/wishlist/items/{market.own.variant.product_id}",
         expected_message="Prenda eliminada de tu lista de deseos")
    assert call(wishlist_api, market.customer, "GET", "/wishlist") == []


def test_duplicate_and_unknown_products_are_rejected(wishlist_api, api_db, market):
    import uuid

    save(wishlist_api, market)
    rejected(wishlist_api, api_db, market.customer, "POST", "/wishlist/items", 409,
             "La prenda ya se encuentra en tu lista de deseos", json={"product_id": str(market.own.variant.product_id)})
    rejected(wishlist_api, api_db, market.customer, "POST", "/wishlist/items", 404,
             "La prenda seleccionada no existe en el catálogo", json={"product_id": str(uuid.uuid4())})


def test_move_to_cart_adds_the_variant_and_removes_the_favorite(wishlist_api, api_db, market):
    save(wishlist_api, market)
    call(wishlist_api, market.customer, "POST", f"/wishlist/items/{market.own.variant.product_id}/move-to-cart",
         expected_message="Prenda movida al carrito de compras con éxito",
         json={"variant_id": str(market.own.variant.id), "branch_id": str(market.branches[0].id)})
    cart = call(wishlist_api, market.customer, "GET", "/cart/current")
    assert [i["variant_id"] for i in cart["items"]] == [str(market.own.variant.id)]
    assert call(wishlist_api, market.customer, "GET", "/wishlist") == []


def test_move_to_cart_without_stock_keeps_the_favorite(wishlist_api, api_db, market):
    from app.models.inventory import Inventory

    save(wishlist_api, market)
    api_db.query(Inventory).filter(Inventory.variant_id == market.own.variant.id).update({"quantity": 2})  # all reserved
    api_db.commit()
    rejected(wishlist_api, api_db, market.customer, "POST", f"/wishlist/items/{market.own.variant.product_id}/move-to-cart",
             400, "No hay stock disponible para mover la prenda al carrito",
             json={"variant_id": str(market.own.variant.id)})


def test_move_to_cart_requires_a_variant_of_that_product(wishlist_api, api_db, market):
    save(wishlist_api, market)
    rejected(wishlist_api, api_db, market.customer, "POST", f"/wishlist/items/{market.own.variant.product_id}/move-to-cart",
             400, "La talla o color elegido no pertenece a esta prenda",
             json={"variant_id": str(market.foreign.variant.id)})


def test_move_to_cart_respects_one_cart_per_company(wishlist_api, api_db, market):
    add(wishlist_api, market)  # cart already holds the own company's garment
    save(wishlist_api, market, market.foreign.variant.product_id)
    rejected(wishlist_api, api_db, market.customer, "POST", f"/wishlist/items/{market.foreign.variant.product_id}/move-to-cart",
             400, f"Ya tienes un carrito pendiente en {market.own.tenant.name}. Págalo o vacíalo antes de comprar en otra empresa.",
             json={"variant_id": str(market.foreign.variant.id), "branch_id": str(market.branches[2].id)})


def test_only_customers_have_a_wishlist(wishlist_api, api_db, market):
    rejected(wishlist_api, api_db, market.staff[0, "cajero"], "GET", "/wishlist", 403)
