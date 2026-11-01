"""Unit & Integration tests for Cart Branch Persistence and Coupon Scoping (CU15).

Exercises:
- Setting and persisting branch_id in Cart.
- PATCH /cart/branch logic in cart_service.set_cart_branch.
- Validation that branch belongs to the cart's tenant.
- Global coupons (branch_id=None) applying to any cart.
- Branch-specific coupons (branch_id=UUID) applying only when cart.branch_id matches.
- Branch-specific coupons failing when cart.branch_id is None.
- Invalidation / removal of branch-specific coupons when cart branch changes.
- Retention of global coupons when cart branch changes.
- Resetting tenant_id and branch_id when the cart is cleared.
"""
from datetime import datetime, timezone
from decimal import Decimal
import importlib
import os
from pathlib import Path
from unittest.mock import patch
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

# Initialize config before model imports
with patch.dict(
    os.environ,
    {"DATABASE_URL": "sqlite://", "SECRET_KEY": "test-key", "ACCESS_TOKEN_EXPIRE_MINUTES": "60"},
    clear=True,
):
    import app.core.config
    from app.core.database import Base
    for p in sorted(Path(__file__).parents[1].joinpath("app/models").glob("*.py")):
        importlib.import_module("app.models." + p.stem)

    from app.models.tenant import Tenant
    from app.models.branch import Branch
    from app.models.user import User
    from app.models.product import Product
    from app.models.product_variant import ProductVariant
    from app.models.inventory import Inventory
    from app.models.cart import Cart
    from app.models.cart_item import CartItem
    from app.models.promotion_code import PromotionCode
    from app.models.promotion_code_usage import PromotionCodeUsage
    from app.schemas.cart_schema import CartItemCreate, CartStatusEnum
    from app.schemas.promotion_schema import PromotionCodeApply
    from app.services.cart_service import (
        add_cart_item,
        apply_coupon,
        clear_cart,
        get_current_cart,
        set_cart_branch,
    )


@pytest.fixture
def test_db():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    needed = [
        "tenants", "branches", "users", "categories", "products", "product_variants",
        "inventory", "carts", "cart_items", "promotion_codes",
        "promotion_code_usages", "reservations", "sizes", "colors",
        "user_product_interactions", "wishlist_items",
        "orders",  # reading/changing the cart first expires overdue unpaid orders
    ]
    Base.metadata.create_all(engine, tables=[Base.metadata.tables[name] for name in needed if name in Base.metadata.tables])
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def env(test_db):
    tenant = Tenant(id=uuid.uuid4(), name="Moda Test", slug="moda-test", contact_email="test@moda.bo")
    foreign_tenant = Tenant(id=uuid.uuid4(), name="Otra Empresa", slug="otra-empresa", contact_email="otra@moda.bo")
    test_db.add_all([tenant, foreign_tenant])
    test_db.flush()

    branch_a = Branch(id=uuid.uuid4(), tenant_id=tenant.id, name="Sucursal Central", city="La Paz")
    branch_b = Branch(id=uuid.uuid4(), tenant_id=tenant.id, name="Sucursal Sur", city="La Paz")
    foreign_branch = Branch(id=uuid.uuid4(), tenant_id=foreign_tenant.id, name="Sucursal Ajena", city="Cochabamba")
    test_db.add_all([branch_a, branch_b, foreign_branch])
    test_db.flush()

    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email="cliente@test.bo",
        hashed_password="hash",
        name="Cliente Test",
        gender="femenino",
        rol="cliente",
    )
    admin = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email="admin@test.bo",
        hashed_password="hash",
        name="Admin Test",
        gender="masculino",
        rol="administrador",
    )
    test_db.add_all([user, admin])
    test_db.flush()

    from app.models.category import Category
    cat = Category(id=uuid.uuid4(), tenant_id=tenant.id, name="Ropa")
    test_db.add(cat)
    test_db.flush()

    product = Product(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        category_id=cat.id,
        name="Remera Clásica",
    )
    test_db.add(product)
    test_db.flush()

    from app.schemas.catalog_enums import ProductStatusEnum

    variant = ProductVariant(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        product_id=product.id,
        sku="REM-001",
        price=Decimal("100.00"),
        status=ProductStatusEnum.active,
    )
    test_db.add(variant)
    test_db.flush()

    # Inventory on branch_a and branch_b
    inv_a = Inventory(id=uuid.uuid4(), tenant_id=tenant.id, branch_id=branch_a.id, variant_id=variant.id, quantity=10, reserved_quantity=0)
    inv_b = Inventory(id=uuid.uuid4(), tenant_id=tenant.id, branch_id=branch_b.id, variant_id=variant.id, quantity=10, reserved_quantity=0)
    test_db.add_all([inv_a, inv_b])
    test_db.flush()

    # Coupons: 1 Global, 1 Branch A, 1 Branch B
    c_global = PromotionCode(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        code="GLOBAL10",
        discount_type="fixed",
        discount_value=Decimal("15.00"),
        branch_id=None,
        created_by=admin.id,
        is_active=True,
    )
    c_branch_a = PromotionCode(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        code="SUCA10",
        discount_type="fixed",
        discount_value=Decimal("20.00"),
        branch_id=branch_a.id,
        created_by=admin.id,
        is_active=True,
    )
    c_branch_b = PromotionCode(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        code="SUCB10",
        discount_type="fixed",
        discount_value=Decimal("25.00"),
        branch_id=branch_b.id,
        created_by=admin.id,
        is_active=True,
    )
    test_db.add_all([c_global, c_branch_a, c_branch_b])
    test_db.commit()

    return {
        "tenant": tenant,
        "foreign_tenant": foreign_tenant,
        "branch_a": branch_a,
        "branch_b": branch_b,
        "foreign_branch": foreign_branch,
        "user": user,
        "product": product,
        "variant": variant,
        "coupons": {"global": c_global, "branch_a": c_branch_a, "branch_b": c_branch_b},
    }


def test_add_cart_item_sets_branch_and_serializes(test_db, env):
    user_id = env["user"].id
    variant_id = env["variant"].id
    branch_a_id = env["branch_a"].id

    cart_read = add_cart_item(test_db, user_id, CartItemCreate(variant_id=variant_id, quantity=1, branch_id=branch_a_id))
    assert cart_read.branch_id == branch_a_id
    assert cart_read.branch_name == "Sucursal Central"
    assert cart_read.tenant_id == env["tenant"].id

    fetched = get_current_cart(test_db, user_id)
    assert fetched.branch_id == branch_a_id
    assert fetched.branch_name == "Sucursal Central"


def test_set_cart_branch_updates_and_validates_tenant(test_db, env):
    user_id = env["user"].id
    variant_id = env["variant"].id
    branch_a_id = env["branch_a"].id
    branch_b_id = env["branch_b"].id
    foreign_branch_id = env["foreign_branch"].id

    # Add item with branch A
    add_cart_item(test_db, user_id, CartItemCreate(variant_id=variant_id, quantity=1, branch_id=branch_a_id))

    # Update to branch B -> empties items because inventory is branch-specific
    updated, warning = set_cart_branch(test_db, user_id, branch_b_id)
    assert updated.branch_id == branch_b_id
    assert updated.branch_name == "Sucursal Sur"
    assert updated.items == []
    assert "el carrito se reinició" in warning

    # Setting same branch again produces no wipe or warning
    same, warn_same = set_cart_branch(test_db, user_id, branch_b_id)
    assert same.branch_id == branch_b_id
    assert warn_same is None

    # Update to foreign branch -> raises ValueError
    with pytest.raises(ValueError, match="La sucursal no pertenece a la empresa"):
        set_cart_branch(test_db, user_id, foreign_branch_id)


def test_global_coupon_applies_with_or_without_branch(test_db, env):
    user_id = env["user"].id
    variant_id = env["variant"].id
    branch_a_id = env["branch_a"].id

    # Add item
    add_cart_item(test_db, user_id, CartItemCreate(variant_id=variant_id, quantity=1, branch_id=branch_a_id))

    # Apply global coupon
    cart = apply_coupon(test_db, user_id, PromotionCodeApply(code="GLOBAL10"))
    assert cart.promotion_code == "GLOBAL10"
    assert cart.discount_amount == Decimal("15.00")
    assert cart.total_amount == Decimal("85.00")


def test_branch_coupon_requires_matching_branch(test_db, env):
    user_id = env["user"].id
    variant_id = env["variant"].id
    branch_a_id = env["branch_a"].id
    branch_b_id = env["branch_b"].id

    # Cart in branch A
    add_cart_item(test_db, user_id, CartItemCreate(variant_id=variant_id, quantity=1, branch_id=branch_a_id))

    # Applying branch B coupon fails immediately
    with pytest.raises(ValueError, match="El código promocional no aplica a esta sucursal"):
        apply_coupon(test_db, user_id, PromotionCodeApply(code="SUCB10"))

    # Applying branch A coupon succeeds
    cart = apply_coupon(test_db, user_id, PromotionCodeApply(code="SUCA10"))
    assert cart.promotion_code == "SUCA10"
    assert cart.discount_amount == Decimal("20.00")
    assert cart.total_amount == Decimal("80.00")


def test_branch_coupon_fails_when_cart_has_no_branch(test_db, env):
    user_id = env["user"].id
    variant_id = env["variant"].id

    # Add item without branch -> cart has item but branch_id is None
    cart = add_cart_item(test_db, user_id, CartItemCreate(variant_id=variant_id, quantity=1, branch_id=None))
    assert cart.branch_id is None

    with pytest.raises(ValueError, match="Selecciona la sucursal antes de aplicarlo"):
        apply_coupon(test_db, user_id, PromotionCodeApply(code="SUCA10"))


def test_switching_branch_removes_incompatible_branch_coupon_and_resets_cart(test_db, env):
    user_id = env["user"].id
    variant_id = env["variant"].id
    branch_a_id = env["branch_a"].id
    branch_b_id = env["branch_b"].id

    # Cart in branch A with branch A coupon
    add_cart_item(test_db, user_id, CartItemCreate(variant_id=variant_id, quantity=1, branch_id=branch_a_id))
    apply_coupon(test_db, user_id, PromotionCodeApply(code="SUCA10"))

    # Switch to branch B -> cart items wiped and coupon removed
    switched, warning = set_cart_branch(test_db, user_id, branch_b_id)
    assert switched.branch_id == branch_b_id
    assert switched.items == []
    assert switched.promotion_code is None
    assert switched.discount_amount == Decimal("0.00")
    assert switched.total_amount == Decimal("0.00")
    assert "el carrito se reinició" in warning


def test_switching_branch_resets_cart_items_and_coupons(test_db, env):
    user_id = env["user"].id
    variant_id = env["variant"].id
    branch_a_id = env["branch_a"].id
    branch_b_id = env["branch_b"].id

    # Cart in branch A with global coupon
    add_cart_item(test_db, user_id, CartItemCreate(variant_id=variant_id, quantity=1, branch_id=branch_a_id))
    apply_coupon(test_db, user_id, PromotionCodeApply(code="GLOBAL10"))

    # Switch to branch B -> cart resets to 0 items and 0 total in branch B
    switched, warning = set_cart_branch(test_db, user_id, branch_b_id)
    assert switched.branch_id == branch_b_id
    assert switched.items == []
    assert switched.total_amount == Decimal("0.00")
    assert "el carrito se reinició" in warning


def test_clear_cart_resets_tenant_and_branch(test_db, env):
    user_id = env["user"].id
    variant_id = env["variant"].id
    branch_a_id = env["branch_a"].id

    add_cart_item(test_db, user_id, CartItemCreate(variant_id=variant_id, quantity=1, branch_id=branch_a_id))
    cleared = clear_cart(test_db, user_id)
    assert cleared.items == []
    assert cleared.tenant_id is None
    assert cleared.branch_id is None
    assert cleared.branch_name is None


def test_wishlist_move_all_to_cart_by_branch(test_db, env):
    from app.services.wishlist_service import add_item, move_all_to_cart

    user_id = env["user"].id
    product = env["product"]
    tenant_id = env["tenant"].id
    branch_a_id = env["branch_a"].id

    # Add product to wishlist
    add_item(test_db, user_id, product.id)

    # Move all items of this tenant and branch to cart
    cart, count = move_all_to_cart(test_db, user_id, tenant_id, branch_a_id)
    assert count == 1
    assert cart.branch_id == branch_a_id
    assert len(cart.items) == 1
    assert cart.items[0].product_id == product.id
