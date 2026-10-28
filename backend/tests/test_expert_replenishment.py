import uuid
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.database import SessionLocal
from app.models.branch import Branch
from app.models.category import Category
from app.models.expert_replenishment import (
    ExpertReplenishmentRule,
    ExpertTransferSuggestion,
    SuggestionStatusEnum,
)
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.catalog_enums import ProductStatusEnum
from app.schemas.enums import GenderEnum, RolEnum, TenantStatusEnum
from app.schemas.expert_replenishment_schema import (
    ApplyTransfersRequest,
    ExpertRuleUpdate,
)
from app.services.expert_replenishment_service import (
    apply_transfers,
    evaluate,
    get_or_create_rules,
    list_suggestions,
    update_rules,
)


# These tests use SessionLocal on the guarded test DB, so they need its migrated schema.
pytestmark = pytest.mark.usefixtures("seeded_db")

def _create_test_tenant(db, prefix="tenant_expert"):
    t_id = uuid.uuid4()
    tenant = Tenant(
        id=t_id,
        name=f"{prefix}_{t_id.hex[:6]}",
        slug=f"slug_{t_id.hex[:6]}",
        contact_email=f"contact_{t_id.hex[:6]}@example.com",
        status=TenantStatusEnum.active,
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def _create_branch(db, tenant_id, name="Sucursal"):
    branch = Branch(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name=f"{name}_{uuid.uuid4().hex[:4]}",
        city="Santa Cruz",
        is_active=True,
    )
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


def _create_catalog_item(db, tenant_id):
    category = Category(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name=f"Cat_{uuid.uuid4().hex[:4]}",
    )
    db.add(category)
    db.flush()

    product = Product(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        category_id=category.id,
        name=f"Camisa_{uuid.uuid4().hex[:4]}",
    )
    db.add(product)
    db.flush()

    variant = ProductVariant(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        product_id=product.id,
        sku=f"SKU-{uuid.uuid4().hex[:6]}",
        price=100.0,
        status=ProductStatusEnum.active,
    )
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return product, variant


def _clean_tenant(db, tenant):
    try:
        db.rollback()
        db.query(ExpertTransferSuggestion).filter(ExpertTransferSuggestion.tenant_id == tenant.id).delete()
        db.query(ExpertReplenishmentRule).filter(ExpertReplenishmentRule.tenant_id == tenant.id).delete()
        db.query(Inventory).filter(Inventory.tenant_id == tenant.id).delete()
        db.query(ProductVariant).filter(ProductVariant.tenant_id == tenant.id).delete()
        db.query(Product).filter(Product.tenant_id == tenant.id).delete()
        db.query(Category).filter(Category.tenant_id == tenant.id).delete()
        db.query(Branch).filter(Branch.tenant_id == tenant.id).delete()
        db.delete(tenant)
        db.commit()
    except Exception:
        db.rollback()


def test_rules_get_and_update():
    with SessionLocal() as db:
        tenant = _create_test_tenant(db, "rules_test")
        try:
            # 1. Defaults
            rules = get_or_create_rules(db, tenant.id)
            assert rules.lookback_days == 7
            assert rules.coverage_days == 14
            assert rules.is_auto_enabled is False

            # 2. Update
            updated = update_rules(
                db,
                tenant.id,
                ExpertRuleUpdate(lookback_days=10, coverage_days=21, is_auto_enabled=True),
            )
            assert updated.lookback_days == 10
            assert updated.coverage_days == 21
            assert updated.is_auto_enabled is True
        finally:
            _clean_tenant(db, tenant)


def test_evaluate_critical_stock_generates_suggestion():
    with SessionLocal() as db:
        tenant = _create_test_tenant(db, "eval_test")
        try:
            branch_target = _create_branch(db, tenant.id, "Destino")
            branch_source = _create_branch(db, tenant.id, "Origen")
            product, variant = _create_catalog_item(db, tenant.id)

            # Target branch has critical stock: quantity 2 < minimum_stock 10
            inv_target = Inventory(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                variant_id=variant.id,
                branch_id=branch_target.id,
                quantity=2,
                reserved_quantity=0,
                minimum_stock=10,
            )
            # Source branch has surplus stock: quantity 25, minimum_stock 5 -> surplus 20
            inv_source = Inventory(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                variant_id=variant.id,
                branch_id=branch_source.id,
                quantity=25,
                reserved_quantity=0,
                minimum_stock=5,
            )
            db.add(inv_target)
            db.add(inv_source)
            db.commit()

            # Run evaluation
            suggestions = evaluate(db, tenant.id)
            assert len(suggestions) == 1
            sug = suggestions[0]
            assert sug.variant_id == variant.id
            assert sug.source_branch_id == branch_source.id
            assert sug.target_branch_id == branch_target.id
            # Need: 10 - 2 = 8. Surplus: 25 - 5 = 20. Suggested: min(8, 20) = 8
            assert sug.suggested_quantity == 8
            assert sug.status == SuggestionStatusEnum.pending.value
            assert "Stock crítico" in sug.reason
            assert branch_target.name in sug.reason
            assert branch_source.name in sug.reason
        finally:
            _clean_tenant(db, tenant)


def test_apply_transfers_moves_stock_and_marks_applied():
    with SessionLocal() as db:
        tenant = _create_test_tenant(db, "apply_test")
        try:
            branch_target = _create_branch(db, tenant.id, "Destino")
            branch_source = _create_branch(db, tenant.id, "Origen")
            product, variant = _create_catalog_item(db, tenant.id)

            inv_target = Inventory(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                variant_id=variant.id,
                branch_id=branch_target.id,
                quantity=2,
                reserved_quantity=0,
                minimum_stock=10,
            )
            inv_source = Inventory(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                variant_id=variant.id,
                branch_id=branch_source.id,
                quantity=25,
                reserved_quantity=0,
                minimum_stock=5,
            )
            db.add(inv_target)
            db.add(inv_source)
            db.commit()

            suggestions = evaluate(db, tenant.id)
            assert len(suggestions) == 1
            sug_id = suggestions[0].id

            # Apply transfer
            count = apply_transfers(db, tenant.id, [sug_id])
            assert count == 1

            # Refresh inventories
            db.refresh(inv_target)
            db.refresh(inv_source)
            assert inv_target.quantity == 10  # 2 + 8
            assert inv_source.quantity == 17  # 25 - 8

            # Verify suggestion updated
            s = db.query(ExpertTransferSuggestion).filter(ExpertTransferSuggestion.id == sug_id).first()
            assert s.status == SuggestionStatusEnum.applied.value
            assert s.applied_at is not None

            # Double apply -> 404
            with pytest.raises(HTTPException) as exc_info:
                apply_transfers(db, tenant.id, [sug_id])
            assert exc_info.value.status_code == 404
        finally:
            _clean_tenant(db, tenant)


def test_apply_transfers_insufficient_stock_raises_400():
    with SessionLocal() as db:
        tenant = _create_test_tenant(db, "deplete_test")
        try:
            branch_target = _create_branch(db, tenant.id, "Destino")
            branch_source = _create_branch(db, tenant.id, "Origen")
            product, variant = _create_catalog_item(db, tenant.id)

            inv_target = Inventory(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                variant_id=variant.id,
                branch_id=branch_target.id,
                quantity=2,
                reserved_quantity=0,
                minimum_stock=10,
            )
            inv_source = Inventory(
                id=uuid.uuid4(),
                tenant_id=tenant.id,
                variant_id=variant.id,
                branch_id=branch_source.id,
                quantity=25,
                reserved_quantity=0,
                minimum_stock=5,
            )
            db.add(inv_target)
            db.add(inv_source)
            db.commit()

            suggestions = evaluate(db, tenant.id)
            assert len(suggestions) == 1
            sug_id = suggestions[0].id

            # Now manually deplete source inventory to simulate race condition
            inv_source.quantity = 0
            db.commit()

            with pytest.raises(HTTPException) as exc_info:
                apply_transfers(db, tenant.id, [sug_id])
            assert exc_info.value.status_code == 400
            assert "No hay stock disponible" in exc_info.value.detail
        finally:
            _clean_tenant(db, tenant)


def test_tenant_isolation_in_expert_replenishment():
    with SessionLocal() as db:
        tenant1 = _create_test_tenant(db, "t1")
        tenant2 = _create_test_tenant(db, "t2")
        try:
            b1_target = _create_branch(db, tenant1.id, "T1_Destino")
            b1_source = _create_branch(db, tenant1.id, "T1_Origen")
            p1, v1 = _create_catalog_item(db, tenant1.id)

            inv1_target = Inventory(
                id=uuid.uuid4(),
                tenant_id=tenant1.id,
                variant_id=v1.id,
                branch_id=b1_target.id,
                quantity=1,
                reserved_quantity=0,
                minimum_stock=10,
            )
            inv1_source = Inventory(
                id=uuid.uuid4(),
                tenant_id=tenant1.id,
                variant_id=v1.id,
                branch_id=b1_source.id,
                quantity=30,
                reserved_quantity=0,
                minimum_stock=5,
            )
            db.add(inv1_target)
            db.add(inv1_source)
            db.commit()

            # Evaluate tenant 1
            sug1 = evaluate(db, tenant1.id)
            assert len(sug1) == 1

            # List suggestions for tenant 2 -> must be completely empty
            sug2 = list_suggestions(db, tenant2.id)
            assert len(sug2) == 0

            # Tenant 2 trying to apply tenant 1's suggestion -> 404
            with pytest.raises(HTTPException) as exc:
                apply_transfers(db, tenant2.id, [sug1[0].id])
            assert exc.value.status_code == 404
        finally:
            _clean_tenant(db, tenant1)
            _clean_tenant(db, tenant2)


def _stock(db, tenant_id, variant_id, branch_id, quantity, minimum):
    db.add(Inventory(id=uuid.uuid4(), tenant_id=tenant_id, variant_id=variant_id, branch_id=branch_id,
                     quantity=quantity, reserved_quantity=0, minimum_stock=minimum))
    db.commit()


def _quantity(db, variant_id, branch_id):
    db.expire_all()
    return db.query(Inventory.quantity).filter(Inventory.variant_id == variant_id, Inventory.branch_id == branch_id).scalar()


def test_source_surplus_is_not_promised_twice():
    """Two branches short of the same garment cannot both receive the whole surplus."""
    with SessionLocal() as db:
        tenant = _create_test_tenant(db, "surplus_once")
        try:
            source = _create_branch(db, tenant.id, "Origen")
            first, second = _create_branch(db, tenant.id, "DestinoA"), _create_branch(db, tenant.id, "DestinoB")
            _, variant = _create_catalog_item(db, tenant.id)
            _stock(db, tenant.id, variant.id, source.id, 15, 5)  # surplus 10
            _stock(db, tenant.id, variant.id, first.id, 0, 8)     # needs 8
            _stock(db, tenant.id, variant.id, second.id, 0, 8)    # needs 8

            suggestions = evaluate(db, tenant.id)
            assert sum(s.suggested_quantity for s in suggestions if s.source_branch_id == source.id) == 10
        finally:
            _clean_tenant(db, tenant)


def test_inactive_branches_are_ignored():
    with SessionLocal() as db:
        tenant = _create_test_tenant(db, "inactive_branch")
        try:
            target, closed = _create_branch(db, tenant.id, "Destino"), _create_branch(db, tenant.id, "Cerrada")
            closed.is_active = False
            db.commit()
            _, variant = _create_catalog_item(db, tenant.id)
            _stock(db, tenant.id, variant.id, target.id, 0, 8)
            _stock(db, tenant.id, variant.id, closed.id, 30, 0)
            assert evaluate(db, tenant.id) == []
        finally:
            _clean_tenant(db, tenant)


def test_applying_a_batch_is_all_or_nothing():
    """Each suggestion fits alone, the batch does not: no transfer of the batch may be kept."""
    with SessionLocal() as db:
        tenant = _create_test_tenant(db, "atomic_batch")
        try:
            source = _create_branch(db, tenant.id, "Origen")
            first, second = _create_branch(db, tenant.id, "DestinoA"), _create_branch(db, tenant.id, "DestinoB")
            _, variant = _create_catalog_item(db, tenant.id)
            _stock(db, tenant.id, variant.id, source.id, 15, 5)  # surplus 10
            _stock(db, tenant.id, variant.id, first.id, 0, 8)
            _stock(db, tenant.id, variant.id, second.id, 0, 8)
            suggestions = evaluate(db, tenant.id)
            assert sorted(s.suggested_quantity for s in suggestions) == [2, 8]
            # Sales leave 9 units at the source: 8 and 2 each fit alone, but not together.
            db.query(Inventory).filter(Inventory.variant_id == variant.id, Inventory.branch_id == source.id).update({"quantity": 9})
            db.commit()

            with pytest.raises(HTTPException) as failed:
                apply_transfers(db, tenant.id, [s.id for s in suggestions])
            assert failed.value.status_code == 400
            assert (_quantity(db, variant.id, source.id), _quantity(db, variant.id, first.id),
                    _quantity(db, variant.id, second.id)) == (9, 0, 0)
            assert {s.status for s in list_suggestions(db, tenant.id)} == {SuggestionStatusEnum.pending.value}
        finally:
            _clean_tenant(db, tenant)
