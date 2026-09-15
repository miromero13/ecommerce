from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.core.database import SessionLocal
from app.models.user import User  # noqa: F401 - registers SQLAlchemy relationships
from app.schemas.order_schema import PaymentMethodEnum
from app.schemas.reservation_schema import ReservationStatusEnum
from app.schemas.sales_schema import SaleCreate
from app.services.inventory_service import _inventory_available, get_consolidated_stock
from app.services.pricing_service import discounted_price
from app.services.reservation_service import transition_reservation


def test_available_quantity_never_consumes_reserved_stock():
    assert _inventory_available(SimpleNamespace(quantity=10, reserved_quantity=3)) == 7
    assert _inventory_available(SimpleNamespace(quantity=2, reserved_quantity=5)) == 0
    assert _inventory_available(SimpleNamespace(quantity=None, reserved_quantity=None)) == 0


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
