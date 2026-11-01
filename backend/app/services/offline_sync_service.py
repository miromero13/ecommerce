"""CU25/CU29/CU30: offline cash sales, batch sync and conflict resolution.

Rules:
- Offline the till only takes cash (card/QR gateways need internet) and the customer leaves with a
  provisional receipt. The money is real from that moment, so every cent is recorded on sync.
- Who keeps the last unit: an OFFLINE QUEUE ordered by the time each operation happened on its
  device (cashier charged at the till / customer pressed "Comprar" in the app without internet),
  not by who reconnects first. When an earlier operation arrives and the unit is gone, it takes it
  back from a LATER offline holder: a later offline till sale becomes a conflict (its cashier
  refunds or compensates) and a later offline phone order that is still unpaid is cancelled (the
  customer is never charged and is notified). Inventory rows are locked (SELECT ... FOR UPDATE).
- Online purchases paid in real time with Stripe are final: they never lose their unit.
- Device times are only trusted within [now - 2 days, now + 5 min]; outside that the operation
  keeps no priority (it can still take free stock, it just cannot displace anyone).
- A sale that cannot be confirmed becomes a persisted conflict. Its cash enters the drawer as a
  'held' movement, so the cash count matches the physical drawer while it waits for a decision.
- Resolution (once, by a person): cash_refund (drawer withdrawal + refund receipt), wallet_credit
  (110 % to the customer's wallet; the cash stays), exchange (another garment; the difference is
  charged or returned) or delivered (the garment already left: the sale stands and inventory is
  adjusted, admins are told to count the shelf).
- Idempotency: the client operation_id is unique on sales and on conflicts; re-sending a batch
  never duplicates anything. Each operation commits on its own, so one bad sale never blocks the rest.
"""
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.cash_session import CashMovement, CashSession
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.models.offline_conflict import OfflineSaleConflict
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.catalog_enums import ProductStatusEnum
from app.schemas.enums import RolEnum
from app.schemas.inventory_schema import InventoryMovementTypeEnum
from app.schemas.offline_schema import ConflictResolveRequest, OfflineOperationIn
from app.schemas.order_schema import FulfillmentStatusEnum, OrderStatusEnum, PaymentMethodEnum, PaymentStatusEnum
from app.schemas.sales_schema import SaleStatusEnum
from app.services import cash_session_service
from app.services.pricing_service import discounted_price

CENT = Decimal("0.01")
WALLET_BONUS = Decimal("1.10")  # +10 % courtesy for waiting
MAX_OFFLINE_AGE = timedelta(days=2)
CLOCK_SKEW = timedelta(minutes=5)


class ConflictStateError(Exception):
    """The conflict was already resolved (HTTP 409)."""


def _money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(CENT)


# ---------------------------------------------------------------- helpers

def _variants(db: Session, tenant_id: UUID, variant_ids) -> dict[UUID, ProductVariant]:
    rows = (
        db.query(ProductVariant)
        .join(Product, Product.id == ProductVariant.product_id)
        .filter(ProductVariant.id.in_(list(variant_ids)), Product.tenant_id == tenant_id)
        .all()
    )
    return {row.id: row for row in rows}


def _lock_inventories(db: Session, branch_id: UUID, variant_ids) -> dict[UUID, Inventory | None]:
    # Always lock in the same order: two syncs touching the same garments can never deadlock.
    locked = {}
    for variant_id in sorted(variant_ids, key=str):
        locked[variant_id] = (
            db.query(Inventory)
            .filter(Inventory.variant_id == variant_id, Inventory.branch_id == branch_id)
            .with_for_update()
            .first()
        )
    return locked


def _available(inventory: Inventory | None) -> int:
    return max((inventory.quantity or 0) - (inventory.reserved_quantity or 0), 0) if inventory else 0


def _group_lines(lines):
    """[(variant_id, qty, unit_price)] -> {variant_id: (qty, line_total)}; one sale line per garment."""
    grouped = defaultdict(lambda: [0, Decimal("0")])
    for variant_id, quantity, unit_price in lines:
        grouped[variant_id][0] += quantity
        grouped[variant_id][1] += _money(unit_price) * quantity
    return {vid: (qty, _money(total)) for vid, (qty, total) in grouped.items()}


def _create_sale(db: Session, *, tenant_id: UUID, branch_id: UUID, cashier_id: UUID, operation_id: str,
                 reference: str, grouped: dict, variants: dict, subtotal, discount, total,
                 offline_created_at=None, offline_details=None) -> Sale:
    currency = (db.query(Tenant.currency).filter(Tenant.id == tenant_id).scalar() or "BOB").lower()
    sale = Sale(
        tenant_id=tenant_id, branch_id=branch_id, user_id=cashier_id,
        status=SaleStatusEnum.completed, payment_method=PaymentMethodEnum.cash,
        payment_status=PaymentStatusEnum.paid, cash_reference=reference,
        offline_operation_id=operation_id, subtotal=_money(subtotal),
        discount_amount=_money(discount), total_amount=_money(total), currency=currency,
        offline_created_at=offline_created_at, offline_details=offline_details,
    )
    db.add(sale)
    db.flush()
    for variant_id, (quantity, line_total) in grouped.items():
        variant = variants[variant_id]
        db.add(SaleItem(
            sale_id=sale.id, variant_id=variant_id, quantity=quantity,
            unit_price=_money(line_total / quantity), line_total=line_total,
            product_id=variant.product_id,
            product_name=variant.product.name if variant.product else str(variant.product_id),
            variant_sku=variant.sku, size_id=variant.size_id, color_id=variant.color_id,
            image_url=variant.image_url, image_public_id=variant.image_public_id,
        ))
    return sale


def _move_stock(db: Session, tenant_id: UUID, branch_id: UUID, variant_id: UUID, quantity: int,
                movement_type: InventoryMovementTypeEnum, note: str, user_id: UUID) -> None:
    db.add(InventoryMovement(tenant_id=tenant_id, variant_id=variant_id, branch_id=branch_id,
                             movement_type=movement_type, quantity=quantity, note=note, created_by=user_id))


def _sync_drawer(db: Session, cashier: User, session_id: UUID | None, branch_id: UUID, tenant_id: UUID):
    """The drawer that holds this offline cash: the one open when the sale happened, else the current one."""
    def usable(session):
        return session if (session and session.status == "open" and session.branch_id == branch_id
                           and session.tenant_id == tenant_id) else None

    if session_id:
        found = usable(db.query(CashSession).filter(CashSession.id == session_id).with_for_update().first())
        if found:
            return found
    return usable(cash_session_service.get_open_session(db, cashier.id, lock=True))


def _resolver_drawer(db: Session, user: User, conflict: OfflineSaleConflict) -> CashSession:
    """Cash moves (refunds, extra charges) only through the resolver's open drawer in the sale's branch."""
    session = cash_session_service.get_open_session(db, user.id, lock=True)
    if session is None:
        raise ValueError("Abre tu caja para mover efectivo en esta resolución")
    if session.branch_id != conflict.branch_id or session.tenant_id != conflict.tenant_id:
        raise ValueError("El efectivo se devuelve o cobra en la caja de la sucursal donde se hizo la venta")
    return session


def _withdraw(db: Session, session: CashSession, amount: Decimal, reason: str, source_id: UUID) -> None:
    available = cash_session_service.expected_cash(session)
    if amount > available:
        raise ValueError(f"No hay efectivo suficiente en caja para devolver {amount} Bs. (la caja tiene {available} Bs.)")
    db.add(CashMovement(session_id=session.id, type="withdrawal", method="cash", amount=amount,
                        reason=reason[:255], source_id=source_id))
    db.flush()


def _customer(db: Session, email: str | None) -> User:
    email = (email or "").strip().lower()
    if not email:
        raise ValueError("Indica el correo del cliente para acreditar su billetera")
    customer = db.query(User).filter(User.email == email, User.rol == RolEnum.cliente,
                                     User.is_active.is_(True)).first()
    if not customer:
        raise LookupError(f"No existe una cuenta de cliente con el correo {email}. "
                          "Pide al cliente que se registre o elige otra solución.")
    return customer


def _notify_staff(db: Session, tenant_id: UUID, branch_id: UUID, title: str, body: str, key: str) -> None:
    from sqlalchemy import or_

    from app.services.notification_service import create_notification

    staff = db.query(User.id).filter(
        User.tenant_id == tenant_id, User.is_active.is_(True),
        or_(User.rol == RolEnum.administrador, (User.rol == RolEnum.encargado) & (User.branch_id == branch_id)),
    ).all()
    for (user_id,) in staff:
        create_notification(db, user_id, title, body, {"type": "offline_conflict"}, dedupe_key=f"{key}:{user_id}")


def serialize_conflict(conflict: OfflineSaleConflict, cashier_name: str | None = None) -> dict:
    return {
        "id": conflict.id, "operation_id": conflict.operation_id, "receipt_number": conflict.receipt_number,
        "branch_id": conflict.branch_id, "cashier_id": conflict.cashier_id, "cashier_name": cashier_name,
        "reason": conflict.reason, "items": conflict.items, "subtotal": conflict.subtotal,
        "discount": conflict.discount, "total": conflict.total, "cash_received": conflict.cash_received,
        "change_returned": conflict.change_returned, "customer_name": conflict.customer_name,
        "customer_phone": conflict.customer_phone, "customer_email": conflict.customer_email,
        "offline_created_at": conflict.offline_created_at, "status": conflict.status,
        "resolution": conflict.resolution, "refund_amount": conflict.refund_amount,
        "wallet_credit_amount": conflict.wallet_credit_amount, "extra_charged": conflict.extra_charged,
        "sale_id": conflict.sale_id, "refund_receipt_number": conflict.refund_receipt_number,
        "resolution_notes": conflict.resolution_notes, "resolved_at": conflict.resolved_at,
        "created_at": conflict.created_at,
    }


# ---------------------------------------------------------------- offline queue by time (CU30)

def trusted_time(value: datetime | None) -> datetime | None:
    """The device time of an offline operation, or None when it cannot be trusted for priority."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    # ponytail: device clocks can be wrong or tampered with; this window bounds the damage.
    return value if now - MAX_OFFLINE_AGE <= value <= now + CLOCK_SKEW else None


def _later_offline_sale(db: Session, tenant_id: UUID, branch_id: UUID, variant_id: UUID, after: datetime):
    return (
        db.query(Sale)
        .join(SaleItem, SaleItem.sale_id == Sale.id)
        .filter(Sale.tenant_id == tenant_id, Sale.branch_id == branch_id, Sale.status == SaleStatusEnum.completed,
                Sale.offline_operation_id.is_not(None), Sale.offline_created_at > after,
                SaleItem.variant_id == variant_id)
        .order_by(Sale.offline_created_at.desc())
        .with_for_update(of=Sale)
        .first()
    )


def _later_offline_order(db: Session, tenant_id: UUID, branch_id: UUID, variant_id: UUID, after: datetime,
                         exclude_order_id=None):
    query = (
        db.query(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(Order.tenant_id == tenant_id, Order.pickup_branch_id == branch_id,
                Order.payment_status == PaymentStatusEnum.pending,  # paid online = final
                Order.fulfillment_status == FulfillmentStatusEnum.pending_pickup,
                Order.offline_requested_at > after, OrderItem.variant_id == variant_id)
    )
    if exclude_order_id:
        query = query.filter(Order.id != exclude_order_id)
    return query.order_by(Order.offline_requested_at.desc()).with_for_update(of=Order).first()


def _displace_sale(db: Session, sale: Sale, winner: str) -> OfflineSaleConflict:
    """A confirmed offline till sale loses its unit to an earlier offline operation: it becomes a conflict."""
    details = sale.offline_details or {}
    receipt = details.get("receipt_number") or sale.cash_reference or str(sale.id)
    movement = db.query(CashMovement).filter(CashMovement.source_id == sale.id, CashMovement.type == "sale").first()
    operation_id = sale.offline_operation_id
    # Free the operation id first (a later 'delivered'/'exchange' resolution creates a new sale with it).
    sale.offline_operation_id = None
    sale.status = SaleStatusEnum.cancelled
    db.flush()
    conflict = OfflineSaleConflict(
        tenant_id=sale.tenant_id, branch_id=sale.branch_id, cashier_id=sale.user_id,
        cash_session_id=movement.session_id if movement else None, operation_id=operation_id,
        receipt_number=receipt[:40],
        reason=f"Desplazada: la operación offline {winner} se hizo antes y tiene prioridad sobre la prenda.",
        items=[{"variant_id": str(item.variant_id), "quantity": item.quantity, "unit_price": str(_money(item.unit_price)),
                "sku": item.variant_sku, "product_name": item.product_name} for item in sale.items],
        subtotal=_money(sale.subtotal), discount=_money(sale.discount_amount), total=_money(sale.total_amount),
        cash_received=details.get("cash_received"), change_returned=details.get("change_returned"),
        customer_name=details.get("customer_name"), customer_phone=details.get("customer_phone"),
        customer_email=details.get("customer_email"), offline_created_at=sale.offline_created_at, status="pending",
    )
    db.add(conflict)
    db.flush()
    if movement:  # the cash is still in that drawer: from sale to held, the expected cash does not change
        movement.type = "held"
        movement.source_id = conflict.id
        movement.reason = f"Cobro offline en conflicto {receipt} (desplazado por una operación anterior)"
    for item in sale.items:
        inventory = (db.query(Inventory).filter(Inventory.variant_id == item.variant_id,
                                                Inventory.branch_id == sale.branch_id).with_for_update().first())
        if inventory:
            inventory.quantity += item.quantity
        _move_stock(db, sale.tenant_id, sale.branch_id, item.variant_id, item.quantity, InventoryMovementTypeEnum.income,
                    f"Reversión: venta offline {receipt} desplazada por {winner}", sale.user_id)
    db.flush()
    db.info.setdefault("offline_displaced_sales", []).append(conflict)
    return conflict


def _displace_order(db: Session, order: Order, winner: str) -> None:
    """An unpaid phone order made offline later than `winner` loses the unit: cancelled, never charged."""
    from app.services.order_service import _release_order

    _release_order(db, order, PaymentStatusEnum.failed, FulfillmentStatusEnum.cancelled)
    order.status = OrderStatusEnum.cancelled  # lost its place in the queue: cancelled, never charged
    db.flush()
    db.info.setdefault("offline_displaced_orders", []).append((order.id, order.user_id, order.stripe_payment_intent_id))


def make_room(db: Session, tenant_id: UUID, branch_id: UUID, needed: dict, inventories: dict,
              happened_at: datetime, winner: str, exclude_order_id=None) -> None:
    """Frees stock for an offline operation that happened at `happened_at`, taking it back from LATER
    offline holders (latest first). Online purchases already paid are never touched."""
    for variant_id, quantity in needed.items():
        inventory = inventories.get(variant_id)
        while inventory is not None and _available(inventory) < quantity:
            sale = _later_offline_sale(db, tenant_id, branch_id, variant_id, happened_at)
            order = _later_offline_order(db, tenant_id, branch_id, variant_id, happened_at, exclude_order_id)
            if sale is None and order is None:
                break
            if order is None or (sale is not None and sale.offline_created_at >= order.offline_requested_at):
                _displace_sale(db, sale, winner)
            else:
                _displace_order(db, order, winner)


def notify_displaced(db: Session) -> None:
    """After commit: tell the losers. Cashiers/admins resolve the conflict; customers were never charged."""
    from app.core.config import settings
    from app.services.notification_service import create_notification

    for conflict in db.info.pop("offline_displaced_sales", []):
        _notify_staff(db, conflict.tenant_id, conflict.branch_id, "Venta offline desplazada",
                      f"La venta {conflict.receipt_number} ({conflict.total} Bs.) perdió la prenda frente a una operación "
                      "offline anterior. Devuelve o compensa al cliente en la consola de conflictos.",
                      f"offline-displaced:{conflict.id}")
        create_notification(db, conflict.cashier_id, "Venta offline desplazada",
                            f"Tu venta {conflict.receipt_number} quedó en conflicto: alguien la pidió o pagó antes.",
                            {"type": "offline_conflict"}, dedupe_key=f"offline-displaced:{conflict.id}:cashier")
    displaced_orders = db.info.pop("offline_displaced_orders", [])
    for order_id, user_id, _ in displaced_orders:
        create_notification(db, user_id, "Otra persona compró antes que tú",
                            "La prenda de tu pedido sin conexión fue comprada antes por otra persona. "
                            "Tu pedido se canceló y no se te cobró nada.",
                            {"type": "order", "order_id": str(order_id), "status": "cancelled"},
                            dedupe_key=f"offline-displaced-order:{order_id}")
    intents = [intent for _, _, intent in displaced_orders if intent]
    if intents and settings.stripe_secret_key:
        try:
            import stripe

            stripe.api_key = settings.stripe_secret_key
            for intent in intents:
                try:
                    stripe.PaymentIntent.cancel(intent)  # a lost garment can no longer be paid
                except Exception:
                    pass
        except Exception:
            pass


# ---------------------------------------------------------------- sync (CU30)

def _check_operation(op: OfflineOperationIn, variants: dict) -> str | None:
    """Why this sale cannot be confirmed, or None when it can."""
    missing = [str(item.variant_id) for item in op.items if item.variant_id not in variants]
    if missing:
        return "Prenda no encontrada en el catálogo de la empresa"
    lines_total = sum((_money(item.unit_price) * item.quantity for item in op.items), Decimal("0"))
    if abs(lines_total - _money(op.total)) > CENT:
        return f"Montos inconsistentes: total {_money(op.total)} Bs. y suma de prendas {_money(lines_total)} Bs."
    if op.cash_received is not None and _money(op.cash_received) < _money(op.total):
        return f"Efectivo recibido ({_money(op.cash_received)} Bs.) menor al total ({_money(op.total)} Bs.)"
    return None


def _shortage(needed: dict, variants: dict, inventories: dict) -> str | None:
    for variant_id, quantity in needed.items():
        available = _available(inventories.get(variant_id))
        if available < quantity:
            return (f"Sin stock para SKU {variants[variant_id].sku}: disponible {available}, requerido {quantity}. "
                    "Una compra en línea o una operación offline anterior se quedó con la prenda.")
    return None


def _sync_one(db: Session, op: OfflineOperationIn, cashier: User, tenant_id: UUID, branch_id: UUID):
    """Returns (result, sale, conflict, has_drawer); result is 'synced' or 'conflict'. Runs in the caller's savepoint."""
    variant_ids = {item.variant_id for item in op.items}
    variants = _variants(db, tenant_id, variant_ids)
    inventories = _lock_inventories(db, branch_id, variant_ids)
    drawer = _sync_drawer(db, cashier, op.cash_session_id, branch_id, tenant_id)
    reason = _check_operation(op, variants)
    if reason is None:
        needed = defaultdict(int)
        for item in op.items:
            needed[item.variant_id] += item.quantity
        reason = _shortage(needed, variants, inventories)
        happened_at = trusted_time(op.created_at)
        if reason and happened_at:
            # Queue by time: take the unit back from a later offline holder, if any.
            make_room(db, tenant_id, branch_id, needed, inventories, happened_at, op.receipt_number)
            reason = _shortage(needed, variants, inventories)

    if reason is None:
        grouped = _group_lines((item.variant_id, item.quantity, item.unit_price) for item in op.items)
        sale = _create_sale(db, tenant_id=tenant_id, branch_id=branch_id, cashier_id=cashier.id,
                            operation_id=op.operation_id, reference=f"OFFLINE:{op.receipt_number}",
                            grouped=grouped, variants=variants, subtotal=op.subtotal,
                            discount=op.discount, total=op.total,
                            offline_created_at=trusted_time(op.created_at),
                            offline_details={
                                "receipt_number": op.receipt_number,
                                "customer_name": (op.customer_name or "").strip() or None,
                                "customer_phone": (op.customer_phone or "").strip() or None,
                                "customer_email": (op.customer_email or "").strip().lower() or None,
                                "cash_received": str(_money(op.cash_received)) if op.cash_received is not None else None,
                                "change_returned": str(_money(op.change_returned)) if op.change_returned is not None else None,
                            })
        for variant_id, (quantity, _) in grouped.items():
            inventories[variant_id].quantity -= quantity
            _move_stock(db, tenant_id, branch_id, variant_id, quantity, InventoryMovementTypeEnum.outcome,
                        f"Venta offline {op.receipt_number}", cashier.id)
        if drawer:
            cash_session_service.record_sale(db, drawer, sale, op.cash_received)
        return "synced", sale, None, drawer is not None

    items = [{
        "variant_id": str(item.variant_id), "quantity": item.quantity, "unit_price": str(_money(item.unit_price)),
        "sku": variants[item.variant_id].sku if item.variant_id in variants else item.variant_sku,
        "product_name": (variants[item.variant_id].product.name if item.variant_id in variants
                         and variants[item.variant_id].product else item.product_name),
    } for item in op.items]
    conflict = OfflineSaleConflict(
        tenant_id=tenant_id, branch_id=branch_id, cashier_id=cashier.id,
        cash_session_id=drawer.id if drawer else None, operation_id=op.operation_id,
        receipt_number=op.receipt_number, reason=reason[:255], items=items,
        subtotal=_money(op.subtotal), discount=_money(op.discount), total=_money(op.total),
        cash_received=_money(op.cash_received) if op.cash_received is not None else None,
        change_returned=_money(op.change_returned) if op.change_returned is not None else None,
        customer_name=(op.customer_name or "").strip() or None,
        customer_phone=(op.customer_phone or "").strip() or None,
        customer_email=(op.customer_email or "").strip().lower() or None,
        offline_created_at=op.created_at, status="pending",
    )
    db.add(conflict)
    db.flush()
    if drawer:
        # The customer's cash is physically in the drawer: count it, but as held until resolved.
        db.add(CashMovement(session_id=drawer.id, type="held", method="cash", amount=_money(op.total),
                            cash_received=conflict.cash_received, change_given=conflict.change_returned,
                            source_id=conflict.id,
                            reason=f"Cobro offline en conflicto {op.receipt_number} (pendiente de resolución)"))
        db.flush()
    return "conflict", None, conflict, drawer is not None


def sync_batch(db: Session, user: User, tenant_id: UUID, branch_id: UUID, operations: list[OfflineOperationIn]) -> dict:
    synced_ids, conflicts, rejected, without_drawer = [], [], [], []
    new_conflicts = []
    touched = set()
    # Oldest first: within one device, the customer who paid first keeps the garment.
    ordered = sorted(operations, key=lambda op: (op.created_at is None,
                                                 op.created_at or datetime.max.replace(tzinfo=timezone.utc)))
    for op in ordered:
        if op.type != "cash_sale":
            rejected.append({"operation_id": op.operation_id, "reason": "Tipo de operación no soportado"})
            continue
        if op.branch_id != branch_id:
            rejected.append({"operation_id": op.operation_id, "reason": "La venta pertenece a otra sucursal"})
            continue

        known_sale = db.query(Sale.tenant_id).filter(Sale.offline_operation_id == op.operation_id).first()
        if known_sale:  # re-sent batch: already confirmed
            if known_sale.tenant_id == tenant_id:
                synced_ids.append(op.operation_id)
            else:
                rejected.append({"operation_id": op.operation_id, "reason": "Operación desconocida"})
            continue
        known_conflict = db.query(OfflineSaleConflict).filter(OfflineSaleConflict.operation_id == op.operation_id).first()
        if known_conflict:
            if known_conflict.tenant_id == tenant_id:
                conflicts.append(serialize_conflict(known_conflict))
            else:
                rejected.append({"operation_id": op.operation_id, "reason": "Operación desconocida"})
            continue

        cashier = user
        if op.cashier_id and op.cashier_id != user.id:
            # Shared terminal: credit the cashier who made the sale when they belong to this branch.
            cashier = db.query(User).filter(User.id == op.cashier_id, User.tenant_id == tenant_id,
                                            User.branch_id == branch_id).first() or user
        try:
            with db.begin_nested():
                result, sale, conflict, has_drawer = _sync_one(db, op, cashier, tenant_id, branch_id)
            db.commit()  # release the inventory locks right away
            notify_displaced(db)
        except IntegrityError:
            db.rollback()  # the same operation was synced concurrently by another request
            db.info.pop("offline_displaced_sales", None)
            db.info.pop("offline_displaced_orders", None)
            if db.query(Sale.id).filter(Sale.offline_operation_id == op.operation_id).first():
                synced_ids.append(op.operation_id)
                continue
            raise
        if not has_drawer:
            without_drawer.append(op.operation_id)
        if result == "synced":
            synced_ids.append(op.operation_id)
            touched.update(item.variant_id for item in op.items)
        else:
            conflicts.append(serialize_conflict(conflict))
            new_conflicts.append(conflict)

    for conflict in new_conflicts:
        _notify_staff(db, tenant_id, branch_id, "Venta offline en conflicto",
                      f"El comprobante {conflict.receipt_number} ({conflict.total} Bs.) no pudo confirmarse: "
                      f"{conflict.reason} Resuélvelo en la consola de conflictos.", f"offline-conflict:{conflict.id}")
    if touched:
        from app.services.notification_service import notify_low_stock
        for inventory in db.query(Inventory).filter(Inventory.branch_id == branch_id,
                                                    Inventory.variant_id.in_(list(touched))).all():
            notify_low_stock(db, inventory)

    return {
        "synced_count": len(synced_ids), "conflicts_count": len(conflicts), "rejected_count": len(rejected),
        "synced_ids": synced_ids, "conflicts": conflicts, "rejected": rejected,
        "without_drawer": without_drawer,
    }


# ---------------------------------------------------------------- conflicts (CU30)

def _conflict_query(db: Session, user: User, tenant_id: UUID):
    query = db.query(OfflineSaleConflict).filter(OfflineSaleConflict.tenant_id == tenant_id)
    if user.rol != RolEnum.administrador:
        query = query.filter(OfflineSaleConflict.branch_id == user.branch_id)
    return query


def list_conflicts(db: Session, user: User, tenant_id: UUID, status: str = "pending") -> dict:
    query = _conflict_query(db, user, tenant_id)
    if status in {"pending", "resolved"}:
        query = query.filter(OfflineSaleConflict.status == status)
    rows = query.order_by(OfflineSaleConflict.created_at.desc()).limit(500).all()
    names = dict(db.query(User.id, User.name).filter(User.id.in_({row.cashier_id for row in rows})).all()) if rows else {}
    pending = [row for row in rows if row.status == "pending"]
    return {
        "items": [serialize_conflict(row, names.get(row.cashier_id)) for row in rows],
        "pending_count": len(pending),
        # Money customers paid and are still waiting for a decision on.
        "pending_total": _money(sum((row.total for row in pending), Decimal("0"))),
    }


def resolve_conflict(db: Session, user: User, tenant_id: UUID, conflict_id: UUID, payload: ConflictResolveRequest) -> dict:
    try:
        conflict = _conflict_query(db, user, tenant_id).filter(OfflineSaleConflict.id == conflict_id).with_for_update().first()
        if not conflict:
            raise LookupError("Conflicto no encontrado")
        if conflict.status != "pending":
            raise ConflictStateError("Este conflicto ya fue resuelto")

        paid = _money(conflict.total)
        receipt = conflict.receipt_number
        notify_count = None

        if payload.action == "cash_refund":
            drawer = _resolver_drawer(db, user, conflict)
            _withdraw(db, drawer, paid, f"Devolución venta offline {receipt}", conflict.id)
            conflict.refund_amount = paid
            conflict.refund_receipt_number = f"DEV-{receipt}"

        elif payload.action == "wallet_credit":
            from app.services.wallet_service import credit_wallet

            customer = _customer(db, payload.customer_email or conflict.customer_email)
            credit = (paid * WALLET_BONUS).quantize(CENT)
            credit_wallet(db, customer.id, credit, "offline_compensation", source_type="offline_conflict",
                          source_id=conflict.id, commit=False,
                          description=f"Compensación venta offline {receipt} (+10 %)")
            conflict.customer_email = customer.email
            conflict.wallet_credit_amount = credit

        elif payload.action == "exchange":
            _resolve_exchange(db, user, conflict, payload, paid)

        else:  # delivered: the garment already left the store, so a unit existed that the system did not count
            lines = [(UUID(item["variant_id"]), int(item["quantity"]), Decimal(item["unit_price"])) for item in conflict.items]
            grouped = _group_lines(lines)
            variants = _variants(db, tenant_id, grouped.keys())
            if len(variants) != len(grouped):
                raise ValueError("Alguna prenda de la venta ya no existe en el catálogo")
            sale = _create_sale(db, tenant_id=tenant_id, branch_id=conflict.branch_id, cashier_id=conflict.cashier_id,
                                operation_id=conflict.operation_id, reference=f"OFFLINE:{receipt}:ENTREGADA",
                                grouped=grouped, variants=variants, subtotal=conflict.subtotal,
                                discount=conflict.discount, total=paid)
            for variant_id, (quantity, _) in grouped.items():
                # Net zero on the counter: +unit found (adjustment) and -unit sold. Admins must count the shelf.
                _move_stock(db, tenant_id, conflict.branch_id, variant_id, quantity, InventoryMovementTypeEnum.income,
                            f"Ajuste: unidad física no registrada (conflicto offline {receipt})", user.id)
                _move_stock(db, tenant_id, conflict.branch_id, variant_id, quantity, InventoryMovementTypeEnum.outcome,
                            f"Venta offline entregada {receipt}", user.id)
            conflict.sale_id = sale.id
            notify_count = ", ".join(variants[vid].sku for vid in grouped)

        conflict.status = "resolved"
        conflict.resolution = payload.action
        conflict.resolution_notes = (payload.notes or "").strip() or None
        conflict.resolved_by = user.id
        conflict.resolved_at = datetime.now(timezone.utc)
        db.commit()
    except Exception:
        db.rollback()
        raise

    if notify_count:
        _notify_staff(db, tenant_id, conflict.branch_id, "Diferencia de inventario",
                      f"La venta offline {conflict.receipt_number} se entregó sin stock registrado (SKU {notify_count}). "
                      "Realiza un conteo físico de esas prendas.", f"offline-delivered:{conflict.id}")
    db.refresh(conflict)
    return serialize_conflict(conflict)


def _resolve_exchange(db: Session, user: User, conflict: OfflineSaleConflict, payload: ConflictResolveRequest,
                      paid: Decimal) -> None:
    if not payload.exchange_items:
        raise ValueError("Elige la prenda de reemplazo")
    needed = defaultdict(int)
    for item in payload.exchange_items:
        needed[item.variant_id] += item.quantity
    variants = _variants(db, conflict.tenant_id, needed.keys())
    if len(variants) != len(needed) or any(v.status != ProductStatusEnum.active for v in variants.values()):
        raise ValueError("Prenda de reemplazo no disponible")
    inventories = _lock_inventories(db, conflict.branch_id, needed.keys())
    lines, subtotal = [], Decimal("0")
    for variant_id, quantity in needed.items():
        if _available(inventories[variant_id]) < quantity:
            raise ValueError(f"Sin stock para SKU {variants[variant_id].sku} en esta sucursal")
        product = variants[variant_id].product
        price = discounted_price(variants[variant_id].price, product.discount_type, product.discount_value)
        subtotal += _money(variants[variant_id].price) * quantity
        lines.append((variant_id, quantity, price))
    grouped = _group_lines(lines)
    new_total = _money(sum((total for _, total in grouped.values()), Decimal("0")))
    sale = _create_sale(db, tenant_id=conflict.tenant_id, branch_id=conflict.branch_id, cashier_id=user.id,
                        operation_id=conflict.operation_id, reference=f"OFFLINE:{conflict.receipt_number}:CAMBIO",
                        grouped=grouped, variants=variants, subtotal=subtotal,
                        discount=max(_money(subtotal) - new_total, Decimal("0")), total=new_total)
    for variant_id, (quantity, _) in grouped.items():
        inventories[variant_id].quantity -= quantity
        _move_stock(db, conflict.tenant_id, conflict.branch_id, variant_id, quantity, InventoryMovementTypeEnum.outcome,
                    f"Cambio por venta offline en conflicto {conflict.receipt_number}", user.id)
    conflict.sale_id = sale.id

    difference = new_total - paid
    if difference > 0:  # pricier garment: the customer pays the difference in cash
        drawer = _resolver_drawer(db, user, conflict)
        received = difference if payload.cash_received is None else _money(payload.cash_received)
        if received < difference:
            raise ValueError(f"El cliente debe pagar la diferencia de {difference} Bs.")
        db.add(CashMovement(session_id=drawer.id, type="sale", method="cash", amount=difference,
                            cash_received=received, change_given=received - difference, source_id=sale.id))
        db.flush()
        conflict.extra_charged = difference
    elif difference < 0:  # cheaper garment: return the difference
        refund = -difference
        if payload.difference_method == "wallet":
            from app.services.wallet_service import credit_wallet

            customer = _customer(db, payload.customer_email or conflict.customer_email)
            credit_wallet(db, customer.id, refund, "offline_compensation", source_type="offline_conflict",
                          source_id=conflict.id, commit=False,
                          description=f"Diferencia por cambio, venta offline {conflict.receipt_number}")
            conflict.customer_email = customer.email
            conflict.wallet_credit_amount = refund
        else:
            drawer = _resolver_drawer(db, user, conflict)
            _withdraw(db, drawer, refund, f"Diferencia por cambio, venta offline {conflict.receipt_number}", conflict.id)
            conflict.refund_amount = refund
            conflict.refund_receipt_number = f"DEV-{conflict.receipt_number}"
