import math
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.branch import Branch
from app.models.expert_replenishment import (
    ExpertReplenishmentRule,
    ExpertTransferSuggestion,
    SuggestionStatusEnum,
)
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.tenant import Tenant
from app.schemas.catalog_enums import ProductStatusEnum
from app.schemas.expert_replenishment_schema import (
    ExpertRuleUpdate,
    ExpertSuggestionRead,
)
from app.schemas.inventory_schema import InventoryTransferCreate
from app.schemas.sales_schema import SaleStatusEnum
from app.services.inventory_service import (
    _inventory_available,
    _move_stock,
)


def get_or_create_rules(db: Session, tenant_id: UUID) -> ExpertReplenishmentRule:
    rule = (
        db.query(ExpertReplenishmentRule)
        .filter(ExpertReplenishmentRule.tenant_id == tenant_id)
        .first()
    )
    if not rule:
        rule = ExpertReplenishmentRule(
            tenant_id=tenant_id,
            lookback_days=7,
            coverage_days=14,
            is_auto_enabled=False,
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
    return rule


def update_rules(
    db: Session, tenant_id: UUID, data: ExpertRuleUpdate
) -> ExpertReplenishmentRule:
    rule = get_or_create_rules(db, tenant_id)
    if data.lookback_days is not None:
        rule.lookback_days = data.lookback_days
    if data.coverage_days is not None:
        rule.coverage_days = data.coverage_days
    if data.is_auto_enabled is not None:
        rule.is_auto_enabled = data.is_auto_enabled
    db.commit()
    db.refresh(rule)
    return rule


def evaluate(db: Session, tenant_id: UUID) -> list[ExpertSuggestionRead]:
    rules = get_or_create_rules(db, tenant_id)
    lookback_days = max(rules.lookback_days or 7, 1)
    coverage_days = max(rules.coverage_days or 14, 1)

    # 1. Discard previous pending suggestions for this tenant
    db.query(ExpertTransferSuggestion).filter(
        ExpertTransferSuggestion.tenant_id == tenant_id,
        ExpertTransferSuggestion.status == SuggestionStatusEnum.pending.value,
    ).update(
        {"status": SuggestionStatusEnum.discarded.value},
        synchronize_session=False,
    )
    db.commit()

    # 2. Pre-calculate sales velocity for each (variant_id, branch_id) in the lookback window
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    sales_query = (
        db.query(
            SaleItem.variant_id,
            Sale.branch_id,
            func.coalesce(func.sum(SaleItem.quantity), 0).label("units_sold"),
        )
        .join(Sale, Sale.id == SaleItem.sale_id)
        .filter(
            Sale.tenant_id == tenant_id,
            Sale.status == SaleStatusEnum.completed,
            Sale.created_at >= cutoff_date,
        )
        .group_by(SaleItem.variant_id, Sale.branch_id)
        .all()
    )

    # sales_velocity map: (variant_id, branch_id) -> units_per_day
    sales_velocity: dict[tuple[UUID, UUID], float] = {}
    for row in sales_query:
        sales_velocity[(row.variant_id, row.branch_id)] = float(row.units_sold) / float(lookback_days)

    # 3. Load all branches in this tenant
    branches_map = {
        b.id: b for b in db.query(Branch).filter(Branch.tenant_id == tenant_id, Branch.is_active.is_(True)).all()
    }

    # 4. Load all active variants and their inventories in this tenant
    inventories = (
        db.query(Inventory)
        .join(ProductVariant, ProductVariant.id == Inventory.variant_id)
        .join(Product, Product.id == ProductVariant.product_id)
        .join(Branch, Branch.id == Inventory.branch_id)
        .filter(
            Inventory.tenant_id == tenant_id,
            ProductVariant.status == ProductStatusEnum.active,
            Product.tenant_id == tenant_id,
            Branch.tenant_id == tenant_id,
            Branch.is_active.is_(True),  # closed branches neither send nor receive stock
        )
        .options(
            joinedload(Inventory.variant).joinedload(ProductVariant.product),
        )
        .all()
    )

    # Group inventory records by variant_id
    variant_inventories: dict[UUID, list[Inventory]] = {}
    for inv in inventories:
        variant_inventories.setdefault(inv.variant_id, []).append(inv)

    new_suggestions: list[ExpertTransferSuggestion] = []
    # Units already promised from each source in this run: a surplus is never promised twice.
    promised: dict[tuple[UUID, UUID], int] = {}

    # 5. Forward-chaining inference engine
    for variant_id, inv_list in variant_inventories.items():
        if len(inv_list) < 2:
            # Need at least two branches to perform transfers
            continue

        for target_inv in inv_list:
            target_avail = _inventory_available(target_inv)
            target_min = target_inv.minimum_stock or 0

            # R1: Reorder Point Check
            if target_avail >= target_min:
                continue

            target_vel = sales_velocity.get((variant_id, target_inv.branch_id), 0.0)
            # R2: Calculate replenishment need
            expected_consumption = target_vel * coverage_days
            need = math.ceil(expected_consumption + target_min - target_avail)
            if need <= 0:
                continue

            # R3: Evaluate source branches with surplus
            best_source_inv: Inventory | None = None
            max_surplus = 0

            for source_inv in inv_list:
                if source_inv.branch_id == target_inv.branch_id:
                    continue

                source_avail = _inventory_available(source_inv)
                source_min = source_inv.minimum_stock or 0
                source_vel = sales_velocity.get((variant_id, source_inv.branch_id), 0.0)
                source_expected_consumption = source_vel * coverage_days

                surplus = math.floor(source_avail - source_min - source_expected_consumption) - promised.get(
                    (variant_id, source_inv.branch_id), 0)
                if surplus > max_surplus:
                    max_surplus = surplus
                    best_source_inv = source_inv

            # R4: Determine suggested transfer quantity and reason
            if best_source_inv and max_surplus > 0:
                transfer_qty = min(need, max_surplus)
                if transfer_qty > 0:
                    target_branch = branches_map.get(target_inv.branch_id)
                    source_branch = branches_map.get(best_source_inv.branch_id)
                    target_branch_name = target_branch.name if target_branch else "Sucursal destino"
                    source_branch_name = source_branch.name if source_branch else "Sucursal origen"
                    product_title = (
                        target_inv.variant.product.name
                        if target_inv.variant and target_inv.variant.product
                        else "Producto"
                    )
                    variant_sku = target_inv.variant.sku if target_inv.variant else ""

                    reason = (
                        f"Stock crítico en {target_branch_name} ({target_avail} disp. < mín. {target_min}). "
                        f"Velocidad de venta: {target_vel:.2f} u/día con necesidad calculada de {need} u. "
                        f"La sucursal {source_branch_name} presenta un excedente de {max_surplus} u. "
                        f"Se sugiere traspaso de {transfer_qty} u para cobertura de {coverage_days} días."
                    )

                    suggestion = ExpertTransferSuggestion(
                        tenant_id=tenant_id,
                        variant_id=variant_id,
                        source_branch_id=best_source_inv.branch_id,
                        target_branch_id=target_inv.branch_id,
                        suggested_quantity=transfer_qty,
                        reason=reason,
                        status=SuggestionStatusEnum.pending.value,
                    )
                    db.add(suggestion)
                    new_suggestions.append(suggestion)
                    key = (variant_id, best_source_inv.branch_id)
                    promised[key] = promised.get(key, 0) + transfer_qty

    db.commit()
    for s in new_suggestions:
        db.refresh(s)

    return list_suggestions(db, tenant_id, status=SuggestionStatusEnum.pending.value)


def list_suggestions(
    db: Session, tenant_id: UUID, status: str | None = None
) -> list[ExpertSuggestionRead]:
    query = (
        db.query(
            ExpertTransferSuggestion,
            Product.name.label("product_name"),
            ProductVariant.sku.label("variant_sku"),
            Branch.name.label("source_branch_name"),
        )
        .join(ProductVariant, ProductVariant.id == ExpertTransferSuggestion.variant_id)
        .join(Product, Product.id == ProductVariant.product_id)
        .join(Branch, Branch.id == ExpertTransferSuggestion.source_branch_id)
        .filter(ExpertTransferSuggestion.tenant_id == tenant_id)
    )

    if status:
        query = query.filter(ExpertTransferSuggestion.status == status)

    rows = query.order_by(ExpertTransferSuggestion.created_at.desc()).all()

    # Pre-fetch target branch names for display
    target_branch_ids = {row[0].target_branch_id for row in rows}
    target_branches = {
        b.id: b.name
        for b in db.query(Branch).filter(Branch.id.in_(target_branch_ids)).all()
    } if target_branch_ids else {}

    results = []
    for suggestion, product_name, variant_sku, source_branch_name in rows:
        results.append(
            ExpertSuggestionRead(
                id=suggestion.id,
                tenant_id=suggestion.tenant_id,
                variant_id=suggestion.variant_id,
                source_branch_id=suggestion.source_branch_id,
                target_branch_id=suggestion.target_branch_id,
                suggested_quantity=suggestion.suggested_quantity,
                reason=suggestion.reason,
                status=suggestion.status,
                created_at=suggestion.created_at,
                applied_at=suggestion.applied_at,
                product_name=product_name,
                variant_sku=variant_sku,
                source_branch_name=source_branch_name,
                target_branch_name=target_branches.get(suggestion.target_branch_id),
            )
        )
    return results


def apply_transfers(
    db: Session,
    tenant_id: UUID,
    transfer_ids: list[UUID],
    user_id: UUID | None = None,
) -> int:
    suggestions = (
        db.query(ExpertTransferSuggestion)
        .filter(
            ExpertTransferSuggestion.tenant_id == tenant_id,
            ExpertTransferSuggestion.id.in_(transfer_ids),
        )
        .all()
    )

    # Validation: all requested suggestions must exist and be pending
    if len(suggestions) != len(transfer_ids) or any(
        s.status != SuggestionStatusEnum.pending.value for s in suggestions
    ):
        raise HTTPException(
            status_code=404,
            detail="Una o más sugerencias de traspaso ya no son válidas o fueron procesadas",
        )

    # Validation: source inventories must have sufficient stock
    for s in suggestions:
        source_inv = (
            db.query(Inventory)
            .filter(
                Inventory.variant_id == s.variant_id,
                Inventory.branch_id == s.source_branch_id,
                Inventory.tenant_id == tenant_id,
            )
            .first()
        )
        if not source_inv or _inventory_available(source_inv) < s.suggested_quantity:
            raise HTTPException(
                status_code=400,
                detail="No hay stock disponible en el depósito de origen para realizar el traspaso sugerido",
            )

    # Apply the whole batch in ONE transaction: either every transfer is kept or none
    # (each suggestion may fit alone while the batch exceeds the source stock).
    applied_count = 0
    try:
        for s in suggestions:
            _move_stock(
                db,
                InventoryTransferCreate(
                    from_branch_id=s.source_branch_id,
                    to_branch_id=s.target_branch_id,
                    variant_id=s.variant_id,
                    quantity=s.suggested_quantity,
                    note=f"Traspaso experto automático: {s.reason[:150]}",
                ),
                user_id,
                tenant_id=tenant_id,
            )
            s.status = SuggestionStatusEnum.applied.value
            s.applied_at = datetime.now(timezone.utc)
            applied_count += 1
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="No hay stock disponible en el depósito de origen para realizar el traspaso sugerido",
        ) from exc
    except Exception:
        db.rollback()
        raise

    return applied_count


def run_auto_evaluation_all_tenants(db: Session) -> int:
    """Evaluates replenishment for all tenants that have is_auto_enabled == True."""
    active_rules = (
        db.query(ExpertReplenishmentRule)
        .filter(ExpertReplenishmentRule.is_auto_enabled == True)  # noqa: E712
        .all()
    )
    evaluated_count = 0
    for rule in active_rules:
        try:
            evaluate(db, rule.tenant_id)
            evaluated_count += 1
        except Exception:
            db.rollback()
            continue
    return evaluated_count
