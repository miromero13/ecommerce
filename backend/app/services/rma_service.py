"""CU21 & CU24: Service for RMA requests, item evaluations, inventory stock/merma, and monthly wallet settlements."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import validate_tenant_access
from app.models.branch import Branch
from app.models.color import Color
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product_variant import ProductVariant
from app.models.rma import RmaRequest, RmaRequestItem
from app.models.size import Size
from app.models.user import User
from app.models.wallet import UserWallet, WalletTransaction
from app.schemas.enums import RolEnum
from app.schemas.inventory_schema import InventoryMovementTypeEnum
from app.schemas.order_schema import FulfillmentStatusEnum, OrderStatusEnum, PaymentStatusEnum
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
from app.services.inventory_service import _get_or_create_inventory, _inventory_available
from app.services.notification_service import create_notification, _notify_rma_event


def get_month_end_date() -> datetime:
    """Returns the last second of the current UTC month."""
    now = datetime.now(timezone.utc)
    year = now.year + (1 if now.month == 12 else 0)
    month = 1 if now.month == 12 else now.month + 1
    next_month_start = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)
    return next_month_start - timedelta(seconds=1)


def _format_rma_number(db: Session, tenant_id: UUID) -> str:
    year = datetime.now(timezone.utc).year
    prefix = f"RMA-{year}-"
    count = (
        db.query(func.count(RmaRequest.id))
        .filter(RmaRequest.tenant_id == tenant_id, RmaRequest.rma_number.like(f"{prefix}%"))
        .scalar()
        or 0
    )
    return f"{prefix}{count + 1:04d}"


def _serialize_rma_item(item: RmaRequestItem) -> RmaItemRead:
    prod_name = item.order_item.product_name if item.order_item else "Prenda"
    sku = item.order_item.variant_sku if item.order_item else ""
    unit_price = float(item.order_item.unit_price) if item.order_item else 0.0
    image_url = item.order_item.image_url if item.order_item else None

    # Original size / color
    orig_size = None
    orig_color = None
    if item.order_item and item.order_item.variant:
        if item.order_item.variant.size:
            orig_size = item.order_item.variant.size.name
        if item.order_item.variant.color:
            orig_color = item.order_item.variant.color.name

    # Requested variant label
    req_label = None
    if item.requested_variant:
        s_name = item.requested_variant.size.name if item.requested_variant.size else ""
        c_name = item.requested_variant.color.name if item.requested_variant.color else ""
        req_label = f"Talle {s_name} · {c_name}".strip(" ·")

    # Replacement variant label
    rep_label = None
    if item.replacement_variant:
        s_name = item.replacement_variant.size.name if item.replacement_variant.size else ""
        c_name = item.replacement_variant.color.name if item.replacement_variant.color else ""
        rep_label = f"Talle {s_name} · {c_name}".strip(" ·")

    branch_name = item.branch.name if item.branch else None

    return RmaItemRead(
        id=item.id,
        order_item_id=item.order_item_id,
        product_name=prod_name,
        original_sku=sku,
        original_size=orig_size,
        original_color=orig_color,
        unit_price=unit_price,
        quantity=item.quantity,
        image_url=image_url,
        reason=item.reason,
        preferred_resolution=item.preferred_resolution,
        requested_variant_id=item.requested_variant_id,
        requested_variant_label=req_label,
        customer_notes=item.customer_notes,
        item_condition=item.item_condition,
        action=item.action,
        status=item.status,
        replacement_variant_id=item.replacement_variant_id,
        replacement_variant_label=rep_label,
        branch_id=item.branch_id,
        branch_name=branch_name,
        inspection_notes=item.inspection_notes,
        quarantine_record=item.quarantine_record,
        refund_amount=float(item.refund_amount) if item.refund_amount is not None else None,
        wallet_settlement_date=item.wallet_settlement_date,
        settlement_status=item.settlement_status,
    )


# [CU21 - Secuencia: Pasos 2.6, 2.12, 3.4, 4.12, 4.18, 5.12] rma_routes invoca _serialize_rma_request(rma) sobre la entidad SolicitudDevolucion
# [CU21 - Secuencia: Pasos 2.7, 2.13, 3.5, 4.13, 4.19, 5.13] SolicitudDevolucion retorna _serialize_rma_request(rma): RmaRequestRead a rma_routes
# [CU24 - Secuencia: Paso 1.12] rma_routes invoca _serialize_rma_request(rma) sobre la entidad SolicitudDevolucion
# [CU24 - Secuencia: Paso 1.13] SolicitudDevolucion retorna _serialize_rma_request(rma): RmaRequestRead a rma_routes
def _serialize_rma_request(rma: RmaRequest) -> RmaRequestRead:
    cust_name = rma.user.name if rma.user and rma.user.name else rma.user.email
    order_num = f"PED-{str(rma.order_id)[:8].upper()}"
    return RmaRequestRead(
        id=rma.id,
        tenant_id=rma.tenant_id,
        order_id=rma.order_id,
        order_number=order_num,
        user_id=rma.user_id,
        customer_name=cust_name,
        customer_email=rma.user.email,
        rma_number=rma.rma_number,
        status=rma.status,
        customer_notes=rma.customer_notes,
        pdf_url=f"/api/rma/requests/{rma.id}/pdf",
        created_at=rma.created_at,
        updated_at=rma.updated_at,
        items=[_serialize_rma_item(item) for item in rma.items],
    )


# [CU21 - Secuencia: Paso 1.2] rma_routes invoca list_eligible_orders(user, tenant_id) sobre la entidad Pedido
# [CU21 - Secuencia: Paso 1.3] Pedido retorna list_eligible_orders(user, tenant_id): list[EligibleOrderRead] a rma_routes
def list_eligible_orders(db: Session, user: User, tenant_id: UUID | None = None) -> list[EligibleOrderRead]:
    """List orders delivered within the last 30 days and itemize eligible garments with exchange options."""
    now = datetime.now(timezone.utc)
    cutoff_date = now - timedelta(days=30)

    query = (
        db.query(Order)
        .filter(
            Order.user_id == user.id,
            (Order.payment_status == PaymentStatusEnum.paid) | (Order.status == OrderStatusEnum.paid),
        )
    )
    if tenant_id is not None:
        query = query.filter(Order.tenant_id == tenant_id)

    orders = query.order_by(Order.created_at.desc()).all()

    eligible_orders = []
    for order in orders:
        delivery_dt = order.delivered_at or order.created_at
        if delivery_dt < cutoff_date:
            continue

        days_since = (now - delivery_dt).days
        item_tenant_id = order.tenant_id or tenant_id

        items_list = []
        for item in order.items:
            # Check if this item is in an existing active RMA
            existing_active = (
                db.query(RmaRequestItem)
                .join(RmaRequest, RmaRequest.id == RmaRequestItem.rma_id)
                .filter(
                    RmaRequestItem.order_item_id == item.id,
                    RmaRequestItem.status != "rejected",
                )
                .first()
            )

            is_eligible = existing_active is None
            ineligible_reason = "Ya cuenta con una solicitud de devolución en trámite" if existing_active else None

            # Get sister variants of the same product
            same_variants_query = db.query(ProductVariant).filter(
                ProductVariant.product_id == item.product_id,
                ProductVariant.id != item.variant_id,
            )
            if item_tenant_id:
                same_variants_query = same_variants_query.filter(ProductVariant.tenant_id == item_tenant_id)

            same_variants = same_variants_query.all()

            sister_options = []
            for sv in same_variants:
                stock_query = db.query(func.coalesce(func.sum(Inventory.quantity - Inventory.reserved_quantity), 0)).filter(
                    Inventory.variant_id == sv.id
                )
                if item_tenant_id:
                    stock_query = stock_query.filter(Inventory.tenant_id == item_tenant_id)
                stock_avail = stock_query.scalar() or 0
                sister_options.append(
                    SameProductVariant(
                        variant_id=sv.id,
                        sku=sv.sku,
                        size_name=sv.size.name if sv.size else None,
                        color_name=sv.color.name if sv.color else None,
                        stock=max(int(stock_avail), 0),
                    )
                )

            size_name = item.variant.size.name if item.variant and item.variant.size else None
            color_name = item.variant.color.name if item.variant and item.variant.color else None

            items_list.append(
                EligibleOrderItemRead(
                    order_item_id=item.id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    variant_id=item.variant_id,
                    sku=item.variant_sku,
                    size_name=size_name,
                    color_name=color_name,
                    unit_price=float(item.unit_price),
                    quantity=item.quantity,
                    image_url=item.image_url,
                    eligible_for_rma=is_eligible,
                    ineligible_reason=ineligible_reason,
                    same_product_variants=sister_options,
                )
            )

        if items_list:
            order_num = f"PED-{str(order.id)[:8].upper()}"
            eligible_orders.append(
                EligibleOrderRead(
                    order_id=order.id,
                    order_number=order_num,
                    delivered_at=order.delivered_at,
                    created_at=order.created_at,
                    days_since_delivery=days_since,
                    items=items_list,
                )
            )

    return eligible_orders


# [CU21 - Secuencia: Paso 2.2] rma_routes invoca create_rma_request(user, payload, tenant_id) sobre la entidad SolicitudDevolucion
# [CU21 - Secuencia: Paso 2.3] SolicitudDevolucion retorna create_rma_request(user, payload, tenant_id): RmaRequestRead a rma_routes
# [CU21 - Secuencia: Paso 2.4] rma_routes invoca create_rma_request(user, payload, tenant_id) sobre la entidad DetalleSolicitudDevolucion
# [CU21 - Secuencia: Paso 2.5] DetalleSolicitudDevolucion retorna create_rma_request(user, payload, tenant_id): RmaRequestRead a rma_routes
def create_rma_request(db: Session, user: User, payload: RmaRequestCreate, tenant_id: UUID | None = None) -> RmaRequestRead:
    query = db.query(Order).filter(Order.id == payload.order_id, Order.user_id == user.id)
    if tenant_id is not None:
        query = query.filter(Order.tenant_id == tenant_id)
    order = query.first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La orden indicada no existe")

    effective_tenant_id = order.tenant_id or tenant_id
    if not effective_tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo determinar la empresa asociada a la orden")

    # 30-day window check
    delivery_dt = order.delivered_at or order.created_at
    if (datetime.now(timezone.utc) - delivery_dt).days > 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La orden supera el plazo máximo permitido de 30 días para cambios y devoluciones",
        )

    # Process items
    rma_number = _format_rma_number(db, effective_tenant_id)
    rma = RmaRequest(
        tenant_id=effective_tenant_id,
        order_id=order.id,
        user_id=user.id,
        rma_number=rma_number,
        status="pending_inspection",
        customer_notes=payload.customer_notes,
    )
    db.add(rma)
    db.flush()

    for item_data in payload.items:
        order_item = (
            db.query(OrderItem)
            .filter(OrderItem.id == item_data.order_item_id, OrderItem.order_id == order.id)
            .first()
        )
        if not order_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El ítem {item_data.order_item_id} no pertenece a esta orden",
            )

        # Check existing active RMA item
        existing = (
            db.query(RmaRequestItem)
            .join(RmaRequest, RmaRequest.id == RmaRequestItem.rma_id)
            .filter(
                RmaRequestItem.order_item_id == order_item.id,
                RmaRequestItem.status != "rejected",
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El ítem '{order_item.product_name}' ya tiene una solicitud de devolución en trámite",
            )

        # If resolution is exchange, ensure requested variant belongs to the same product
        if item_data.preferred_resolution == "exchange" and item_data.requested_variant_id:
            req_var = (
                db.query(ProductVariant)
                .filter(ProductVariant.id == item_data.requested_variant_id)
                .first()
            )
            if not req_var or req_var.product_id != order_item.product_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El cambio de prenda solo está permitido por variantes del mismo producto (otra talla o color)",
                )

        rma_item = RmaRequestItem(
            rma_id=rma.id,
            order_item_id=order_item.id,
            quantity=item_data.quantity,
            reason=item_data.reason,
            preferred_resolution=item_data.preferred_resolution,
            requested_variant_id=item_data.requested_variant_id,
            customer_notes=item_data.customer_notes,
            status="pending",
        )
        db.add(rma_item)
    db.commit()
    db.refresh(rma)
    _notify_rma_event(db, rma.id, "requested")
    return _serialize_rma_request(rma)


# [CU21 - Secuencia: Pasos 2.10, 3.2, 4.16, 5.10] rma_routes invoca list_rma_requests(user, tenant_id, status_filter) sobre la entidad SolicitudDevolucion
# [CU21 - Secuencia: Pasos 2.11, 3.3, 4.17, 5.11] SolicitudDevolucion retorna list_rma_requests(user, tenant_id, status_filter): list[RmaRequestRead] a rma_routes
def list_rma_requests(
    db: Session,
    user: User,
    tenant_id: UUID | None = None,
    status_filter: str | None = None,
) -> list[RmaRequestRead]:
    query = db.query(RmaRequest)
    if tenant_id is not None:
        query = query.filter(RmaRequest.tenant_id == tenant_id)

    # Cliente only sees their own; Encargado/Admin sees all for the tenant
    if user.rol == RolEnum.cliente:
        query = query.filter(RmaRequest.user_id == user.id)

    if status_filter:
        query = query.filter(RmaRequest.status == status_filter)

    rmas = query.order_by(RmaRequest.created_at.desc()).all()
    return [_serialize_rma_request(rma) for rma in rmas]


def get_rma_request(db: Session, rma_id: UUID, user: User, tenant_id: UUID | None = None) -> RmaRequestRead:
    query = db.query(RmaRequest).filter(RmaRequest.id == rma_id)
    if tenant_id is not None:
        query = query.filter(RmaRequest.tenant_id == tenant_id)
    if user.rol == RolEnum.cliente:
        query = query.filter(RmaRequest.user_id == user.id)

    rma = query.first()
    if not rma:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud de devolución no encontrada")

    return _serialize_rma_request(rma)


# [CU21 - Secuencia: Paso 4.2] rma_routes invoca review_rma_item(rma_id, item_id, payload, reviewer, tenant_id) sobre la entidad MovimientoInventario
# [CU21 - Secuencia: Paso 4.3] MovimientoInventario retorna review_rma_item(rma_id, item_id, payload, reviewer, tenant_id): RmaRequestRead a rma_routes
# [CU24 - Secuencia: Paso 1.2] rma_routes invoca review_rma_item(rma_id, item_id, payload, reviewer, tenant_id) sobre la entidad MovimientoInventario
# [CU24 - Secuencia: Paso 1.3] MovimientoInventario retorna review_rma_item(rma_id, item_id, payload, reviewer, tenant_id): RmaRequestRead a rma_routes
def review_rma_item(
    db: Session,
    rma_id: UUID,
    item_id: UUID,
    payload: RmaItemReview,
    reviewer: User,
    tenant_id: UUID,
) -> RmaRequestRead:
    rma = db.query(RmaRequest).filter(RmaRequest.id == rma_id, RmaRequest.tenant_id == tenant_id).first()
    if not rma:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud de devolución no encontrada")

    item = (
        db.query(RmaRequestItem)
        .filter(RmaRequestItem.id == item_id, RmaRequestItem.rma_id == rma.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ítem de devolución no encontrado")

    if item.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este ítem ya fue dictaminado previamente")

    # Determine branch
    target_branch_id = payload.branch_id or reviewer.branch_id
    if not target_branch_id:
        branch = db.query(Branch).filter(Branch.tenant_id == tenant_id).first()
        target_branch_id = branch.id if branch else None

    item.branch_id = target_branch_id
    item.inspected_by = reviewer.id
    item.inspected_at = datetime.now(timezone.utc)
    item.inspection_notes = payload.inspection_notes
    item.item_condition = payload.item_condition

    # Business rule: Customer damaged in non-factory defect claims must be rejected
    if payload.status == "approved" and payload.item_condition == "customer_damaged" and item.reason != "factory_defect":
        payload.status = "rejected"
        item.inspection_notes = (item.inspection_notes or "") + " [Rechazado automáticamente: daño atribuible al cliente]."

    if payload.status == "approved":
        if payload.resolution == "exchange":
            # 1. Prenda devuelta intacta reingresa al stock
            if target_branch_id:
                inv_in = _get_or_create_inventory(db, item.order_item.variant_id, target_branch_id, tenant_id)
                inv_in.quantity += item.quantity
                m_in = InventoryMovement(
                    variant_id=item.order_item.variant_id,
                    branch_id=target_branch_id,
                    tenant_id=tenant_id,
                    movement_type=InventoryMovementTypeEnum.rma_restock,
                    quantity=item.quantity,
                    note=f"Reingreso por RMA {rma.rma_number}",
                    created_by=reviewer.id,
                )
                db.add(m_in)
                db.flush()
                item.restock_movement_id = m_in.id

            # 2. Despacho en el acto de la nueva variante entregada
            rep_variant_id = payload.replacement_variant_id or item.requested_variant_id
            if rep_variant_id and target_branch_id:
                inv_out = _get_or_create_inventory(db, rep_variant_id, target_branch_id, tenant_id)
                inv_out.quantity = max(inv_out.quantity - item.quantity, 0)
                m_out = InventoryMovement(
                    variant_id=rep_variant_id,
                    branch_id=target_branch_id,
                    tenant_id=tenant_id,
                    movement_type=InventoryMovementTypeEnum.exchange_dispatch,
                    quantity=item.quantity,
                    note=f"Despacho por cambio en mostrador RMA {rma.rma_number}",
                    created_by=reviewer.id,
                )
                db.add(m_out)
                db.flush()
                item.dispatch_movement_id = m_out.id

            item.replacement_variant_id = rep_variant_id
            item.status = "approved_exchange"
            item.action = "restock_available"

        elif payload.resolution == "store_credit":
            # Si fue falla de fábrica, la prenda va a merma técnica (CU24)
            if payload.item_condition == "factory_damaged":
                quarantine_code = f"QR-{datetime.now(timezone.utc).year}-{uuid4().hex[:6].upper()}"
                item.quarantine_record = quarantine_code
                item.action = "scrap_quarantine"
                if target_branch_id:
                    m_scrap = InventoryMovement(
                        variant_id=item.order_item.variant_id,
                        branch_id=target_branch_id,
                        tenant_id=tenant_id,
                        movement_type=InventoryMovementTypeEnum.scrap_quarantine,
                        quantity=item.quantity,
                        note=f"Baja a merma/cuarentena {quarantine_code} por defecto de fábrica RMA {rma.rma_number}",
                        created_by=reviewer.id,
                    )
                    db.add(m_scrap)
                    db.flush()
            else:
                # Prenda intacta reingresa a stock vendible
                item.action = "restock_available"
                if target_branch_id:
                    inv_in = _get_or_create_inventory(db, item.order_item.variant_id, target_branch_id, tenant_id)
                    inv_in.quantity += item.quantity
                    m_in = InventoryMovement(
                        variant_id=item.order_item.variant_id,
                        branch_id=target_branch_id,
                        tenant_id=tenant_id,
                        movement_type=InventoryMovementTypeEnum.rma_restock,
                        quantity=item.quantity,
                        note=f"Reingreso por devolución a crédito RMA {rma.rma_number}",
                        created_by=reviewer.id,
                    )
                    db.add(m_in)
                    db.flush()
                    item.restock_movement_id = m_in.id

            # Programar acreditación en billetera a fin de mes
            refund_total = Decimal(str(item.order_item.unit_price)) * Decimal(str(item.quantity))
            settlement_dt = get_month_end_date()
            item.refund_amount = refund_total
            item.wallet_settlement_date = settlement_dt
            item.settlement_status = "pending_month_end"
            item.status = "approved_refund"

            # Enviar notificación automática al cliente
            create_notification(
                db=db,
                user_id=rma.user_id,
                title="Devolución aprobada",
                body=(
                    f"Tu devolución para '{item.order_item.product_name}' fue aprobada por Bs. {float(refund_total):.2f}. "
                    f"El saldo se acreditará en tu Billetera Digital al cierre del mes ({settlement_dt.strftime('%d/%m/%Y')})."
                ),
                data={"rma_id": str(rma.id), "rma_number": rma.rma_number, "type": "rma_approval"},
            )

    else:
        item.status = "rejected"
        item.action = "return_to_customer"
    # Update parent RMA status
    all_items = db.query(RmaRequestItem).filter(RmaRequestItem.rma_id == rma.id).all()
    statuses = [it.status for it in all_items]
    if all(s in ("approved_exchange", "approved_refund") for s in statuses):
        rma.status = "approved"
    elif all(s == "rejected" for s in statuses):
        rma.status = "rejected"
    elif any(s in ("approved_exchange", "approved_refund") for s in statuses) and any(s == "rejected" for s in statuses):
        rma.status = "partially_approved"
    elif any(s == "pending" for s in statuses):
        rma.status = "pending_inspection"

    db.commit()
    db.refresh(rma)
    if item.status == "rejected": _notify_rma_event(db, rma.id, "rejected", item.id)  # noqa: E701 (keeps diagram line refs)
    return _serialize_rma_request(rma)


# [CU21 - Secuencia: Paso 5.2] rma_routes invoca settle_monthly_wallets() sobre la entidad BilleteraUsuario
# [CU21 - Secuencia: Paso 5.3] BilleteraUsuario retorna settle_monthly_wallets(): dict a rma_routes
# [CU21 - Secuencia: Paso 5.4] rma_routes invoca settle_monthly_wallets() sobre la entidad MovimientoBilletera
# [CU21 - Secuencia: Paso 5.5] MovimientoBilletera retorna settle_monthly_wallets(): dict a rma_routes
def settle_monthly_wallets(db: Session) -> dict:
    """Processes pending month-end wallet refunds whose settlement date has arrived."""
    now = datetime.now(timezone.utc)
    pending_items = (
        db.query(RmaRequestItem)
        .join(RmaRequest, RmaRequest.id == RmaRequestItem.rma_id)
        .filter(
            RmaRequestItem.status == "approved_refund",
            RmaRequestItem.settlement_status == "pending_month_end",
            RmaRequestItem.wallet_settlement_date <= now,
        )
        .all()
    )

    settled_count = 0
    total_amount = Decimal("0.00")

    for item in pending_items:
        user_id = item.rma.user_id
        amount = item.refund_amount or Decimal("0.00")
        if amount <= 0:
            continue

        wallet = db.query(UserWallet).filter(UserWallet.user_id == user_id).with_for_update().first()
        if not wallet:
            wallet = UserWallet(user_id=user_id, balance=Decimal("0.00"), currency="BOB")
            db.add(wallet)
            db.flush()

        wallet.balance += amount
        tx = WalletTransaction(
            wallet_id=wallet.id,
            type="credit",
            amount=amount,
            balance_after=wallet.balance,
            concept="rma_refund",
            source_type="rma",
            source_id=item.id,
            description=f"Reembolso por devolución {item.rma.rma_number}",
            created_at=now,
        )
        db.add(tx)
        item.settlement_status = "settled"

        # Notificación al cliente de saldo disponible
        create_notification(
            db=db,
            user_id=user_id,
            title="¡Saldo disponible en tu Billetera!",
            body=(
                f"Se acreditaron Bs. {float(amount):.2f} en tu Billetera Digital correspondientes a la devolución "
                f"{item.rma.rma_number}. ¡Ya podés usarlo en tus compras!"
            ),
            data={"rma_id": str(item.rma.id), "rma_number": item.rma.rma_number, "type": "wallet_credited"},
        )

        settled_count += 1
        total_amount += amount

    db.commit()
    return {
        "settled_count": settled_count,
        "total_amount": float(total_amount),
    }
