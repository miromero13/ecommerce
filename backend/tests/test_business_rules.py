from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.database import SessionLocal
from app.models.user import User  # noqa: F401 - registers SQLAlchemy relationships
from app.schemas.order_schema import PaymentMethodEnum
from app.schemas.reservation_schema import ReservationStatusEnum
from app.schemas.sales_schema import SaleCreate
from app.schemas.catalog_schema import ProductCreate, ProductVariantCreate, ProductVariantGarmentPointsUpdate
from app.schemas.catalog_enums import ProductStatusEnum
from app.services.catalog_service import _normalized_variants
from app.services.inventory_service import _inventory_available, get_consolidated_stock
from app.services.pricing_service import discounted_price
from app.services.reservation_service import transition_reservation
from app.schemas.replenishment_schema import ReplenishmentStatusEnum, ReplenishmentItemCreate
from app.schemas.inventory_schema import InventoryThresholdUpdate
from app.services.replenishment_service import validate_transition


def test_available_quantity_never_consumes_reserved_stock():
    assert _inventory_available(SimpleNamespace(quantity=10, reserved_quantity=3)) == 7
    assert _inventory_available(SimpleNamespace(quantity=2, reserved_quantity=5)) == 0
    assert _inventory_available(SimpleNamespace(quantity=None, reserved_quantity=None)) == 0


def test_inventory_minimum_stock_cannot_be_negative():
    with pytest.raises(ValidationError):
        InventoryThresholdUpdate(variant_id=uuid4(), branch_id=uuid4(), minimum_stock=-1)


def test_consolidated_inventory_matches_branch_breakdown():
    with SessionLocal() as db:
        rows = get_consolidated_stock(db)

    assert rows
    for row in rows:
        assert row["quantity"] == sum(branch["quantity"] for branch in row["branches"])
        assert row["reserved_quantity"] == sum(branch["reserved_quantity"] for branch in row["branches"])
        assert row["available_quantity"] == sum(branch["available_quantity"] for branch in row["branches"])
        assert row["available_quantity"] >= 0
        assert all(branch["available_quantity"] >= 0 for branch in row["branches"])


def test_product_discounts_are_capped_and_never_negative():
    assert discounted_price("100", "percentage", "25") == 75
    assert discounted_price("100", "percentage", "150") == 0
    assert discounted_price("100", "fixed", "125") == 0


def test_reservation_transitions_follow_business_flow():
    reservation = SimpleNamespace(status=ReservationStatusEnum.attended)
    transition_reservation(reservation, ReservationStatusEnum.purchase_pending)
    assert reservation.status == ReservationStatusEnum.purchase_pending

    with pytest.raises(ValueError):
        transition_reservation(reservation, ReservationStatusEnum.attended)


def test_direct_sale_requires_cash_and_items():
    payload = SaleCreate(
        branch_id=uuid4(),
        payment_method=PaymentMethodEnum.cash,
        items=[{"variant_id": uuid4(), "quantity": 1}],
    )
    assert payload.reservation_id is None

    with pytest.raises(ValidationError):
        SaleCreate(branch_id=uuid4(), payment_method=PaymentMethodEnum.stripe, items=payload.items)

    with pytest.raises(ValidationError):
        SaleCreate(branch_id=uuid4(), reservation_id=uuid4(), items=payload.items)


def test_product_variant_update_payload_preserves_variant_id():
    variant_id = uuid4()
    payload = ProductCreate(
        name="Product",
        category_id=uuid4(),
        variants=[ProductVariantCreate(id=variant_id, sku="SKU-1", price="10.00")],
    )

    assert _normalized_variants(payload, ProductStatusEnum.active)[0]["id"] == variant_id


def test_variant_garment_points_validate_normalized_coordinates_and_nullability():
    payload = ProductVariantGarmentPointsUpdate(garment_points=[{"x": 0, "y": 1}] * 17)
    dress_payload = ProductVariantGarmentPointsUpdate(garment_points=[{"x": 0, "y": 1}] * 19)
    assert payload.garment_points[0].model_dump() == {"x": 0, "y": 1}
    assert len(dress_payload.garment_points) == 19
    assert ProductVariantGarmentPointsUpdate(garment_points=None).garment_points is None

    for count in (0, 1, 18, 20):
        with pytest.raises(ValidationError):
            ProductVariantGarmentPointsUpdate(garment_points=[{"x": 0, "y": 1}] * count)

    with pytest.raises(ValidationError):
        ProductVariantGarmentPointsUpdate(garment_points=[{"x": 1.1, "y": 0.5}] * 17)


def test_replenishment_status_transition_requires_provider_ownership_and_order():
    validate_transition(ReplenishmentStatusEnum.requested, ReplenishmentStatusEnum.accepted, "proveedor", owns_provider=True)
    with pytest.raises(PermissionError):
        validate_transition(ReplenishmentStatusEnum.requested, ReplenishmentStatusEnum.accepted, "proveedor", owns_provider=False)
    with pytest.raises(ValueError):
        validate_transition(ReplenishmentStatusEnum.accepted, ReplenishmentStatusEnum.awaiting_receipt, "proveedor", owns_provider=True)


def test_replenishment_receive_is_only_allowed_once_and_quantities_are_positive():
    validate_transition(ReplenishmentStatusEnum.awaiting_receipt, ReplenishmentStatusEnum.delivered, "encargado", owns_branch=True)
    with pytest.raises(ValueError):
        validate_transition(ReplenishmentStatusEnum.delivered, ReplenishmentStatusEnum.delivered, "encargado", owns_branch=True)
    with pytest.raises(ValidationError):
        ReplenishmentItemCreate(variant_id=uuid4(), requested_quantity=0)
