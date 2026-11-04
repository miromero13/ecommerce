"""CU21 & CU24: Tests for RMA schemas, PDF slip generation, and business rules."""
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.rma import RmaRequest, RmaRequestItem
from app.schemas.rma_schema import (
    EligibleOrderItemRead,
    EligibleOrderRead,
    RmaItemCreate,
    RmaItemRead,
    RmaItemReview,
    RmaRequestCreate,
    RmaRequestRead,
    SameProductVariant,
)
from app.services.rma_pdf_service import generate_rma_pdf
from app.services.rma_service import get_month_end_date


def test_rma_schemas_validation():
    item_create = RmaItemCreate(
        order_item_id=uuid4(),
        quantity=1,
        reason="wrong_size",
        preferred_resolution="exchange",
        requested_variant_id=uuid4(),
        customer_notes="Me quedó chico de hombros",
    )
    assert item_create.reason == "wrong_size"
    assert item_create.preferred_resolution == "exchange"

    req_create = RmaRequestCreate(
        order_id=uuid4(),
        customer_notes="Solicitud de cambio de talle",
        items=[item_create],
    )
    assert len(req_create.items) == 1

    review = RmaItemReview(
        status="approved",
        item_condition="intact",
        action="restock_available",
        resolution="exchange",
        replacement_variant_id=uuid4(),
        inspection_notes="Prenda con etiquetas intactas",
    )
    assert review.status == "approved"
    assert review.item_condition == "intact"


def test_get_month_end_date():
    end_date = get_month_end_date()
    now = datetime.now(timezone.utc)
    assert end_date.tzinfo is not None
    assert end_date.year >= now.year
    assert end_date.hour == 23
    assert end_date.minute == 59
    assert end_date.second == 59


def test_generate_rma_pdf():
    # Mock RMA hierarchy
    mock_db = MagicMock()
    mock_user = MagicMock(
        first_name="María",
        last_name="Quispe",
        email="maria.quispe@demo.bo",
    )
    mock_order = MagicMock(
        created_at=datetime(2026, 3, 20, 10, 0, tzinfo=timezone.utc),
    )
    mock_tenant = MagicMock(name="Ayni Moda")

    mock_rma = MagicMock(
        id=uuid4(),
        tenant_id=uuid4(),
        order_id=uuid4(),
        user_id=uuid4(),
        rma_number="RMA-2026-0001",
        status="approved",
        customer_notes="Solicito cambio",
        created_at=datetime(2026, 3, 25, 14, 30, tzinfo=timezone.utc),
        tenant=mock_tenant,
        order=mock_order,
        user=mock_user,
    )

    mock_variant = MagicMock(
        size=MagicMock(name="L"),
        color=MagicMock(name="Azul"),
    )
    mock_order_item = MagicMock(
        product_name="Camisa Popelín",
        variant_sku="CAM-POP-AZUL-M",
        unit_price=Decimal("140.00"),
        variant=mock_variant,
    )

    mock_item = MagicMock(
        id=uuid4(),
        order_item=mock_order_item,
        quantity=1,
        reason="wrong_size",
        preferred_resolution="exchange",
        requested_variant=mock_variant,
        replacement_variant=mock_variant,
        customer_notes="Cambio por talle L",
        item_condition="intact",
        action="restock_available",
        status="approved_exchange",
        quarantine_record=None,
        refund_amount=None,
        wallet_settlement_date=None,
        inspection_notes="Prenda intacta",
    )
    mock_rma.items = [mock_item]

    pdf_bytes = generate_rma_pdf(mock_db, mock_rma)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")


def test_customer_damaged_in_non_defect_claim_is_rejected():
    from app.services.rma_service import review_rma_item

    mock_db = MagicMock()
    tenant_id = uuid4()
    rma_id = uuid4()
    item_id = uuid4()

    mock_user = MagicMock(email="maria@demo.bo")
    mock_user.name = "María Quispe"
    mock_order = MagicMock(created_at=datetime.now(timezone.utc))
    order_id = uuid4()
    user_id = uuid4()
    mock_rma = MagicMock(
        id=rma_id,
        tenant_id=tenant_id,
        order_id=order_id,
        user_id=user_id,
        rma_number="RMA-2026-0001",
        status="pending_inspection",
        customer_notes="Nota de prueba",
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        user=mock_user,
        order=mock_order,
    )
    mock_order_item = MagicMock(
        id=uuid4(),
        product_name="Pantalón Chino",
        variant_sku="PAN-01",
        unit_price=Decimal("200.00"),
        variant=None,
        image_url=None,
    )
    mock_item = MagicMock(
        id=item_id,
        rma_id=rma_id,
        order_item_id=mock_order_item.id,
        status="pending",
        reason="wrong_size",  # Not factory defect
        preferred_resolution="exchange",
        quantity=1,
        order_item=mock_order_item,
        requested_variant=None,
        requested_variant_id=None,
        replacement_variant=None,
        replacement_variant_id=None,
        branch=None,
        branch_id=None,
        customer_notes=None,
        item_condition=None,
        action=None,
        inspection_notes=None,
        quarantine_record=None,
        refund_amount=None,
        wallet_settlement_date=None,
        settlement_status=None,
    )
    mock_rma.items = [mock_item]

    mock_db.query().filter().first.side_effect = [mock_rma, mock_item, None]
    mock_db.query().filter().all.return_value = [mock_item]

    payload = RmaItemReview(
        status="approved",  # reviewer attempted to approve
        item_condition="customer_damaged",  # but marked customer damaged
        action="return_to_customer",
        resolution="exchange",
    )
    reviewer = MagicMock(id=uuid4(), branch_id=uuid4())

    # Should override to rejected because it's customer_damaged on a wrong_size claim
    review_rma_item(mock_db, rma_id, item_id, payload, reviewer, tenant_id)

    assert mock_item.status == "rejected"
    assert mock_item.action == "return_to_customer"
    assert "Rechazado automáticamente" in mock_item.inspection_notes


def test_factory_defect_creates_quarantine_record_and_programs_wallet():
    from app.services.rma_service import review_rma_item

    mock_db = MagicMock()
    tenant_id = uuid4()
    rma_id = uuid4()
    item_id = uuid4()

    mock_user = MagicMock(email="maria@demo.bo")
    mock_user.name = "María Quispe"
    mock_order = MagicMock(created_at=datetime.now(timezone.utc))
    order_id = uuid4()
    user_id = uuid4()
    mock_rma = MagicMock(
        id=rma_id,
        tenant_id=tenant_id,
        order_id=order_id,
        user_id=user_id,
        rma_number="RMA-2026-0002",
        status="pending_inspection",
        customer_notes="Falla",
        created_at=datetime.now(timezone.utc),
        updated_at=None,
        user=mock_user,
        order=mock_order,
    )
    mock_order_item = MagicMock(
        id=uuid4(),
        product_name="Vestido Seda",
        variant_sku="VES-01",
        unit_price=Decimal("350.00"),
        variant=None,
        image_url=None,
    )
    mock_item = MagicMock(
        id=item_id,
        rma_id=rma_id,
        order_item_id=mock_order_item.id,
        status="pending",
        reason="factory_defect",
        preferred_resolution="store_credit",
        quantity=1,
        order_item=mock_order_item,
        requested_variant=None,
        requested_variant_id=None,
        replacement_variant=None,
        replacement_variant_id=None,
        branch=None,
        branch_id=None,
        customer_notes=None,
        item_condition=None,
        action=None,
        inspection_notes=None,
        quarantine_record=None,
        refund_amount=None,
        wallet_settlement_date=None,
        settlement_status=None,
    )
    mock_rma.items = [mock_item]

    mock_db.query().filter().first.side_effect = [mock_rma, mock_item, None]
    mock_db.query().filter().all.return_value = [mock_item]

    payload = RmaItemReview(
        status="approved",
        item_condition="factory_damaged",
        action="scrap_quarantine",
        resolution="store_credit",
        inspection_notes="Defecto comprobado",
    )
    reviewer = MagicMock(id=uuid4(), branch_id=uuid4())

    review_rma_item(mock_db, rma_id, item_id, payload, reviewer, tenant_id)

    assert mock_item.status == "approved_refund"
    assert mock_item.action == "scrap_quarantine"
    assert mock_item.quarantine_record is not None
    assert mock_item.quarantine_record.startswith("QR-")
    assert mock_item.refund_amount == Decimal("350.00")
    assert mock_item.settlement_status == "pending_month_end"
    assert mock_item.wallet_settlement_date is not None


def test_settle_monthly_wallets():
    from app.services.rma_service import settle_monthly_wallets

    mock_db = MagicMock()
    user_id = uuid4()
    mock_rma = MagicMock(id=uuid4(), rma_number="RMA-2026-0003", user_id=user_id)
    mock_item = MagicMock(
        id=uuid4(),
        rma=mock_rma,
        refund_amount=Decimal("150.00"),
        settlement_status="pending_month_end",
    )
    mock_db.query().join().filter().all.return_value = [mock_item]

    mock_wallet = MagicMock(id=uuid4(), user_id=user_id, balance=Decimal("50.00"))
    mock_db.query().filter().with_for_update().first.return_value = mock_wallet

    result = settle_monthly_wallets(mock_db)

    assert result["settled_count"] == 1
    assert result["total_amount"] == 150.0
    assert mock_wallet.balance == Decimal("200.00")
    assert mock_item.settlement_status == "settled"


