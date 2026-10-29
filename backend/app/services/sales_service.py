from collections import defaultdict
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.branch import Branch
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.models.order import Order
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.reservation import Reservation
from app.models.reservation_item import ReservationItem
from app.models.sale import Sale
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.enums import RolEnum
from app.models.sale_item import SaleItem
from app.models.size import Size
from app.models.color import Color
from app.schemas.order_schema import PaymentMethodEnum, PaymentStatusEnum
from app.schemas.sales_schema import SaleCreate, SaleItemRead, SaleRead, SaleStatusEnum, SaleTypeEnum
from app.schemas.catalog_enums import ProductStatusEnum
from app.schemas.inventory_schema import InventoryMovementTypeEnum
from app.schemas.reservation_schema import ReservationStatusEnum
from app.services.reservation_service import transition_reservation
from app.services.pricing_service import discounted_price, discount_amount
from app.services.promotion_service import add_usage, calculate_discount, validate_for_user
from app.services.notification_service import notify_low_stock, notify_reservation_event


def _get_inventory_for_update(db: Session, variant_id, branch_id) -> Inventory | None:
    return (
        db.query(Inventory)
        .filter(Inventory.variant_id == variant_id, Inventory.branch_id == branch_id)
        .with_for_update()
        .first()
    )


def _get_sale_for_branch(db: Session, sale_id: UUID, branch_id: UUID) -> Sale | None:
    return db.query(Sale).filter(Sale.id == sale_id, Sale.branch_id == branch_id).first()


def _get_reservation_for_branch(db: Session, reservation_id: UUID, branch_id: UUID) -> Reservation | None:
    return (
        db.query(Reservation)
        .filter(Reservation.id == reservation_id, Reservation.branch_id == branch_id)
        .with_for_update()
        .first()
    )


def _sale_items_query(db: Session, sale_id: UUID):
    return (
        db.query(
            SaleItem.id.label("id"),
            SaleItem.sale_id.label("sale_id"),
            SaleItem.variant_id.label("variant_id"),
            SaleItem.quantity.label("quantity"),
            SaleItem.unit_price.label("unit_price"),
            ProductVariant.price.label("original_unit_price"),
            Product.discount_type.label("discount_type"),
            Product.discount_value.label("discount_value"),
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            ProductVariant.sku.label("variant_sku"),
            ProductVariant.size_id.label("size_id"),
            ProductVariant.color_id.label("color_id"),
            ProductVariant.image_url.label("image_url"),
            ProductVariant.image_public_id.label("image_public_id"),
            Size.name.label("size_name"),
            Color.name.label("color_name"),
        )
        .join(ProductVariant, ProductVariant.id == SaleItem.variant_id)
        .join(Product, Product.id == ProductVariant.product_id)
        .outerjoin(Size, Size.id == ProductVariant.size_id)
        .outerjoin(Color, Color.id == ProductVariant.color_id)
        .filter(SaleItem.sale_id == sale_id)
        .order_by(SaleItem.id.asc())
        .all()
    )


def _serialize_sale(db: Session, sale: Sale) -> SaleRead:
    item_rows = _sale_items_query(db, sale.id)
    items = []
    for row in item_rows:
        data = row._mapping
        line_total = Decimal(str(data["unit_price"])) * int(data["quantity"])
        original_price = Decimal(str(data["original_unit_price"]))
        line_discount = discount_amount(original_price, data["discount_type"], data["discount_value"])
        items.append(
            SaleItemRead.model_validate(
                {
                    **data,
                    "discount_amount": line_discount,
                    "line_total": line_total,
                }
            ).model_dump()
        )

    branch_name = db.query(Branch.name).filter(Branch.id == sale.branch_id).scalar() or str(sale.branch_id)

    return SaleRead.model_validate(
        {
            "id": sale.id,
            "branch_id": sale.branch_id,
            "branch_name": branch_name,
            "type": SaleTypeEnum.in_person,
            "user_id": sale.user_id,
            "reservation_id": sale.reservation_id,
            "status": sale.status,
            "payment_method": sale.payment_method,
            "payment_status": sale.payment_status,
            "cash_reference": sale.cash_reference,
            "customer_id": sale.customer_id,
            "promotion_code_id": sale.promotion_code_id,
            "subtotal": sale.subtotal,
            "discount_amount": sale.discount_amount,
            "total_amount": sale.total_amount,
            "currency": sale.currency,
            "created_at": sale.created_at,
            "updated_at": sale.updated_at,
            "items": items,
        }
    )


def _resolve_items(db: Session, payload: SaleCreate, branch_id: UUID):
    normalized_items: dict[UUID, int] = defaultdict(int)

    if payload.reservation_id:
        reservation = _get_reservation_for_branch(db, payload.reservation_id, branch_id)
        if not reservation:
            raise ValueError("Reserva no encontrada para esta sucursal")
        if reservation.status in {ReservationStatusEnum.cancelled, ReservationStatusEnum.expired}:
            raise ValueError("La reserva no puede convertirse en venta")

        for item in reservation.items:
            normalized_items[item.variant_id] += item.quantity
    else:
        for item in payload.items:
            normalized_items[item.variant_id] += item.quantity

    if not normalized_items:
        raise ValueError("La venta no tiene items")

    return normalized_items


def _registered_customer(db: Session, email: str) -> User:
    customer = db.query(User).filter(User.email == email.strip().lower(), User.rol == RolEnum.cliente,
                                     User.is_active.is_(True)).first()
    if not customer:
        raise ValueError("No existe un cliente registrado con ese correo")
    return customer


def _apply_cashier_coupon(db: Session, sale: Sale, payload: SaleCreate, branch_id: UUID, tenant_id: UUID | None) -> None:
    """CU15 in store: same rules as the web cart (one use per customer, not combined with
    products on sale), so the customer must be identified by a registered email."""
    if payload.customer_email:
        sale.customer_id = _registered_customer(db, payload.customer_email).id
    if not payload.promotion_code:
        return
    if not sale.customer_id:
        raise ValueError("Ingresa el correo del cliente registrado para aplicar el cupón")
    if sale.discount_amount > 0:
        raise ValueError("El cupón no se puede combinar con productos en oferta")
    code = validate_for_user(db, payload.promotion_code.strip().upper(), sale.customer_id, branch_id, tenant_id=tenant_id)
    coupon_discount = calculate_discount(code, sale.subtotal)
    sale.promotion_code_id = code.id
    sale.discount_amount = coupon_discount
    sale.total_amount = max(sale.subtotal - coupon_discount, Decimal("0.00"))
    add_usage(db, code.id, sale.customer_id)


def _apply_loyalty(db: Session, sale: Sale, payload: SaleCreate, tenant_id: UUID | None) -> None:
    """CU17 at the till: redeem points of the identified customer, then earn on what is paid."""
    from app.services import loyalty_service

    if payload.points_to_redeem:
        if not sale.customer_id:
            raise ValueError("Ingresa el correo del cliente registrado para canjear puntos")
        points_discount = loyalty_service.redeem(db, tenant_id, sale.customer_id, payload.points_to_redeem,
                                                 sale.total_amount, "sale", sale.id)
        sale.discount_amount += points_discount
        sale.total_amount -= points_discount
    if sale.customer_id:
        loyalty_service.earn(db, tenant_id, sale.customer_id, sale.total_amount, "sale", sale.id)


def _create_sale_from_items(
    db: Session,
    branch_id: UUID,
    user_id: UUID,
    payload: SaleCreate,
    normalized_items: dict[UUID, int],
    tenant_id: UUID | None = None,
):
    reservation = None
    reservation_should_adjust_inventory = False
    if payload.reservation_id:
        reservation = _get_reservation_for_branch(db, payload.reservation_id, branch_id)
        if not reservation:
            raise ValueError("Reserva no encontrada para esta sucursal")
        reservation_should_adjust_inventory = reservation.status in {ReservationStatusEnum.pending, ReservationStatusEnum.confirmed}

    sale = Sale(
        tenant_id=tenant_id,
        branch_id=branch_id,
        user_id=user_id,
        reservation_id=payload.reservation_id,
        status=SaleStatusEnum.completed,
        payment_method=payload.payment_method,
        payment_status=PaymentStatusEnum.paid,
        cash_reference=payload.cash_reference,
        subtotal=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("0.00"),
        currency=db.query(Tenant.currency).filter(Tenant.id == tenant_id).scalar().lower(),
    )
    db.add(sale)
    db.flush()

    subtotal = Decimal("0.00")
    discount_total = Decimal("0.00")
    for variant_id, quantity in normalized_items.items():
        inventory = _get_inventory_for_update(db, variant_id, branch_id)
        if not inventory:
            raise ValueError("No existe inventario para la variante seleccionada")

        variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
        if not variant or variant.status != ProductStatusEnum.active:
            raise ValueError("Variante no disponible para la venta")

        if payload.reservation_id and reservation_should_adjust_inventory:
            reserved_quantity = int(inventory.reserved_quantity or 0)
            stock_quantity = int(inventory.quantity or 0)
            if stock_quantity < quantity:
                raise ValueError("No hay stock suficiente para completar la venta")
            if reserved_quantity < quantity:
                raise ValueError("La reserva ya no tiene stock suficiente")
            inventory.reserved_quantity = reserved_quantity - quantity
            inventory.quantity = stock_quantity - quantity
            movement_note = f"Venta presencial desde reserva {payload.reservation_id}"
        elif payload.reservation_id:
            movement_note = f"Venta presencial desde reserva {payload.reservation_id}"
        else:
            available = max((inventory.quantity or 0) - (inventory.reserved_quantity or 0), 0)
            if quantity > available:
                raise ValueError("No hay stock suficiente para completar la venta")
            inventory.quantity = (inventory.quantity or 0) - quantity
            movement_note = "Venta presencial"

        original_price = Decimal(str(variant.price))
        unit_price = discounted_price(original_price, variant.product.discount_type, variant.product.discount_value)
        discount_total += discount_amount(original_price, variant.product.discount_type, variant.product.discount_value) * quantity
        line_total = unit_price * quantity
        subtotal += original_price * quantity
        db.add(
            SaleItem(
                sale_id=sale.id,
                variant_id=variant_id,
                quantity=quantity,
                unit_price=unit_price,
                line_total=line_total,
                product_id=variant.product_id,
                product_name=variant.product.name if variant.product else str(variant.product_id),
                variant_sku=variant.sku,
                size_id=variant.size_id,
                color_id=variant.color_id,
                image_url=variant.image_url,
                image_public_id=variant.image_public_id,
            )
        )
        if not payload.reservation_id or reservation_should_adjust_inventory:
            db.add(
                InventoryMovement(
                    tenant_id=tenant_id or (inventory.tenant_id if inventory else None),
                    variant_id=variant_id,
                    branch_id=branch_id,
                    movement_type=InventoryMovementTypeEnum.outcome,
                    quantity=quantity,
                    note=movement_note,
                    created_by=user_id,
                )
            )

    sale.subtotal = subtotal
    sale.discount_amount = discount_total
    sale.total_amount = max(subtotal - discount_total, Decimal("0.00"))
    _apply_cashier_coupon(db, sale, payload, branch_id, tenant_id)
    _apply_loyalty(db, sale, payload, tenant_id)

    if reservation:
        if reservation.status in {ReservationStatusEnum.pending, ReservationStatusEnum.confirmed}:
            transition_reservation(reservation, ReservationStatusEnum.attended)

    return sale


def quote_sale_total(db: Session, user_id: UUID, payload: SaleCreate, branch_id: UUID, tenant_id: UUID) -> Decimal:
    """Exact total of a would-be sale (same rules as create_sale), computed and rolled back."""
    normalized_items = _resolve_items(db, payload, branch_id)
    savepoint = db.begin_nested()
    try:
        return _create_sale_from_items(db, branch_id, user_id, payload, normalized_items, tenant_id=tenant_id).total_amount
    finally:
        savepoint.rollback()


def create_sale(db: Session, user_id: UUID, payload: SaleCreate, branch_id: UUID, tenant_id: UUID | None = None):
    from app.services.payout_service import record_payment
    from app.services.qr_payment_service import consume_sale_qr

    from app.services import cash_session_service

    if payload.payment_method == PaymentMethodEnum.qr and not payload.qr_reference:
        raise ValueError("Genera y cobra el código QR antes de registrar la venta")
    try:
        # 1P-CU18: every till sale belongs to the cashier's open drawer of this branch.
        drawer = cash_session_service.require_open_session(db, user_id, branch_id, tenant_id)
        normalized_items = _resolve_items(db, payload, branch_id)
        with db.begin_nested():
            sale = _create_sale_from_items(db, branch_id, user_id, payload, normalized_items, tenant_id=tenant_id)
            cash = cash_session_service.record_sale(db, drawer, sale, payload.cash_received)
            if payload.payment_method == PaymentMethodEnum.qr:
                # QR money lands in the platform account and reaches the company in the settlement.
                consume_sale_qr(db, payload.qr_reference, tenant_id=tenant_id, branch_id=branch_id,
                                amount=sale.total_amount, sale_id=sale.id)
                record_payment(db, tenant_id, "sale", sale.id, "qr", sale.total_amount, sale.currency, payload.qr_reference)
            from app.services.receipt_service import issue_sale_receipt
            sold = _serialize_sale(db, sale).model_dump()
            receipt = issue_sale_receipt(db, sale, sold["items"], cash)
            from app.services.recommendation_service import record_sale_interactions
            record_sale_interactions(db, sale, sold["items"])  # CU6: in-store purchases also teach the model
        db.commit()
        db.refresh(sale)
        for variant_id in normalized_items:
            inventory = _get_inventory_for_update(db, variant_id, branch_id)
            if inventory:
                notify_low_stock(db, inventory)
        if payload.reservation_id:
            reservation = db.query(Reservation).filter(Reservation.id == payload.reservation_id).first()
            if reservation and reservation.status == ReservationStatusEnum.attended:
                notify_reservation_event(db, reservation.id, reservation.user_id, reservation.status.value)
        # The receipt shows what the customer paid and the change returned.
        return {**_serialize_sale(db, sale).model_dump(), "cash_received": cash.cash_received,
                "change_given": cash.change_given, "receipt_id": receipt.id}
    except Exception:
        db.rollback()
        raise


def list_sales_by_branch(
    db: Session,
    branch_id: UUID | None = None,
    user_id: UUID | None = None,
    tenant_id: UUID | None = None,
):
    query = db.query(Sale)
    if tenant_id is not None:
        query = query.filter(Sale.tenant_id == tenant_id)
    if branch_id is not None:
        query = query.filter(Sale.branch_id == branch_id)
    if user_id is not None:
        query = query.filter(Sale.user_id == user_id)
    sales = [_serialize_sale(db, sale).model_dump() for sale in query.order_by(Sale.created_at.desc()).all()]

    orders_query = db.query(Order).filter(Order.status == "paid", Order.pickup_branch_id.is_not(None))
    if tenant_id is not None:
        orders_query = orders_query.filter(Order.tenant_id == tenant_id)
    if branch_id is not None:
        orders_query = orders_query.filter(Order.pickup_branch_id == branch_id)
    orders = []
    for order in orders_query.order_by(Order.created_at.desc()).all():
        branch_name = db.query(Branch.name).filter(Branch.id == order.pickup_branch_id).scalar() or str(order.pickup_branch_id)
        orders.append(SaleRead.model_validate({
            "id": order.id,
            "branch_id": order.pickup_branch_id,
            "branch_name": branch_name,
            "type": SaleTypeEnum.online,
            "user_id": order.user_id,
            "reservation_id": None,
            "status": SaleStatusEnum.completed,
            "payment_method": order.payment_method,
            "payment_status": order.payment_status,
            "cash_reference": order.cash_reference,
            "subtotal": order.subtotal,
            "discount_amount": order.discount_amount,
            "total_amount": order.total_amount,
            "currency": order.currency,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "items": [{
                "id": item.id, "sale_id": order.id, "variant_id": item.variant_id, "quantity": item.quantity,
                "unit_price": item.unit_price, "original_unit_price": item.unit_price, "discount_amount": Decimal("0.00"),
                "line_total": item.line_total, "product_id": item.product_id, "product_name": item.product_name,
                "variant_sku": item.variant_sku, "size_id": item.size_id, "color_id": item.color_id,
                "size_name": item.size_id and db.query(Size.name).filter(Size.id == item.size_id).scalar(),
                "color_name": item.color_id and db.query(Color.name).filter(Color.id == item.color_id).scalar(),
                "image_url": item.image_url, "image_public_id": item.image_public_id,
            } for item in order.items],
        }).model_dump())
    return sorted(sales + orders, key=lambda sale: sale["created_at"], reverse=True)


def get_sale(
    db: Session,
    branch_id: UUID | None,
    sale_id: UUID,
    user_id: UUID | None = None,
    tenant_id: UUID | None = None,
):
    query = db.query(Sale).filter(Sale.id == sale_id)
    if tenant_id is not None:
        query = query.filter(Sale.tenant_id == tenant_id)
    if branch_id is not None:
        query = query.filter(Sale.branch_id == branch_id)
    if user_id is not None:
        query = query.filter(Sale.user_id == user_id)
    sale = query.first()
    if not sale:
        return None
    return _serialize_sale(db, sale).model_dump()
