import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.payment_attempt import PaymentAttempt
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.promotion_code import PromotionCode
from app.models.reservation import Reservation
from app.models.size import Size
from app.models.color import Color
from app.models.stripe_event import StripeEvent
from app.schemas.cart_schema import CartStatusEnum
from app.schemas.inventory_schema import InventoryMovementTypeEnum
from app.schemas.order_schema import FulfillmentStatusEnum, OrderItemRead, OrderRead, OrderStatusEnum, PaymentMethodEnum, PaymentStatusEnum
from app.schemas.reservation_schema import ReservationStatusEnum
from app.services.pricing_service import discounted_price, discount_amount
from app.services.cart_service import refresh_cart_totals
from app.services.promotion_service import add_usage, validate_for_user
from app.services.reservation_service import transition_reservation
from app.services.recommendation_service import record_completed_order_interactions


STRIPE_RESERVATION_MINUTES = 30
CASH_RESERVATION_HOURS = 24


def _cart_rows(db: Session, cart_id: UUID):
    return db.query(
        CartItem.variant_id.label("variant_id"), CartItem.quantity.label("quantity"), CartItem.reservation_id.label("reservation_id"), ProductVariant.price.label("original_unit_price"),
        Product.discount_type.label("discount_type"), Product.discount_value.label("discount_value"),
        Product.id.label("product_id"), Product.name.label("product_name"), ProductVariant.sku.label("variant_sku"),
        ProductVariant.size_id.label("size_id"), ProductVariant.color_id.label("color_id"), ProductVariant.image_url.label("image_url"),
        ProductVariant.image_public_id.label("image_public_id"),
    ).join(ProductVariant, ProductVariant.id == CartItem.variant_id).join(Product, Product.id == ProductVariant.product_id).filter(CartItem.cart_id == cart_id).all()


def _row_unit_price(row) -> Decimal:
    return discounted_price(row.original_unit_price, row.discount_type, row.discount_value)


def _serialize_order(db: Session, order: Order) -> OrderRead:
    items = [OrderItemRead.model_validate({
        "id": row.id, "order_id": row.order_id, "variant_id": row.variant_id, "quantity": row.quantity,
        "unit_price": row.unit_price, "line_total": row.line_total, "product_id": row.product_id,
        "product_name": row.product_name, "variant_sku": row.variant_sku, "size_id": row.size_id,
        "color_id": row.color_id, "size_name": row.size_id and db.query(Size.name).filter(Size.id == row.size_id).scalar(),
        "color_name": row.color_id and db.query(Color.name).filter(Color.id == row.color_id).scalar(),
        "image_url": row.image_url, "image_public_id": row.image_public_id,
    }).model_dump() for row in order.items]
    return OrderRead.model_validate({
        "id": order.id, "user_id": order.user_id, "status": order.status, "payment_method": order.payment_method,
        "payment_status": order.payment_status, "stripe_payment_intent_id": order.stripe_payment_intent_id,
        "cash_reference": order.cash_reference, "pickup_branch_id": order.pickup_branch_id,
        "pickup_expires_at": order.pickup_expires_at, "pickup_code": order.pickup_code,
        "fulfillment_status": order.fulfillment_status, "subtotal": order.subtotal,
        "discount_amount": order.discount_amount, "promotion_code_id": order.promotion_code_id,
        "total_amount": order.total_amount, "currency": order.currency,
        "created_at": order.created_at, "updated_at": order.updated_at, "items": items,
    })


def list_orders(db: Session, user_id: UUID):
    expire_due_orders(db)
    return [_serialize_order(db, order).model_dump() for order in db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()]


def list_orders_by_branch(db: Session, branch_id: UUID):
    expire_due_orders(db)
    orders = db.query(Order).filter(Order.pickup_branch_id == branch_id).order_by(Order.created_at.desc()).all()
    return [_serialize_order(db, order).model_dump() for order in orders]


def get_order(db: Session, user_id: UUID, order_id: UUID):
    expire_due_orders(db)
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).first()
    return _serialize_order(db, order).model_dump() if order else None


def mark_order_ready(db: Session, order_id: UUID, branch_id: UUID):
    order = db.query(Order).filter(Order.id == order_id, Order.pickup_branch_id == branch_id).with_for_update().first()
    if not order:
        return None
    if order.payment_status != PaymentStatusEnum.paid:
        raise ValueError("El pedido debe estar pagado antes de marcarlo como listo")
    if order.fulfillment_status != FulfillmentStatusEnum.pending_pickup:
        raise ValueError("El pedido no está en preparación")
    order.fulfillment_status = FulfillmentStatusEnum.ready_for_pickup
    db.commit()
    db.refresh(order)
    return _serialize_order(db, order).model_dump()


def _locked_cart(db: Session, user_id: UUID) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id).with_for_update().first()
    if not cart:
        raise ValueError("No tienes un carrito activo")
    return cart


def _reserve_inventory(db: Session, rows, branch_id: UUID, user_id: UUID) -> None:
    for row in rows:
        inventory = db.query(Inventory).filter(Inventory.variant_id == row.variant_id, Inventory.branch_id == branch_id).with_for_update().first()
        if not inventory:
            raise ValueError("No hay stock suficiente en la sucursal seleccionada")
        if row.reservation_id:
            reservation = db.query(Reservation).filter(Reservation.id == row.reservation_id, Reservation.user_id == user_id).with_for_update().first()
            if not reservation or reservation.status != ReservationStatusEnum.purchase_pending or reservation.branch_id != branch_id:
                raise ValueError("La reserva ya no está disponible para este checkout")
            if (inventory.reserved_quantity or 0) < row.quantity:
                raise ValueError("La reserva ya no tiene stock suficiente")
        else:
            if inventory.quantity - inventory.reserved_quantity < row.quantity:
                raise ValueError("No hay stock suficiente en la sucursal seleccionada")
            inventory.reserved_quantity += row.quantity


def _new_order(db: Session, cart: Cart, user_id: UUID, branch_id: UUID, method: PaymentMethodEnum) -> Order:
    if cart.promotion_code_id:
        code = db.query(PromotionCode).filter(PromotionCode.id == cart.promotion_code_id).first()
        if not code:
            raise ValueError("El código promocional ya no existe")
        validate_for_user(db, code.code, user_id, branch_id)
    refresh_cart_totals(db, cart)
    rows = _cart_rows(db, cart.id)
    if not rows:
        raise ValueError("El carrito está vacío")
    _reserve_inventory(db, rows, branch_id, user_id)
    subtotal = sum(Decimal(str(row.original_unit_price)) * row.quantity for row in rows)
    discount = Decimal(str(cart.discount_amount or 0))
    expires = datetime.now(timezone.utc) + timedelta(minutes=STRIPE_RESERVATION_MINUTES if method == PaymentMethodEnum.stripe else CASH_RESERVATION_HOURS * 60)
    order = Order(user_id=user_id, status=OrderStatusEnum.pending, payment_method=method,
                   payment_status=PaymentStatusEnum.pending, pickup_branch_id=branch_id, pickup_expires_at=expires,
                   promotion_code_id=cart.promotion_code_id,
                  pickup_code=secrets.token_urlsafe(9), fulfillment_status=FulfillmentStatusEnum.pending_pickup,
                  subtotal=subtotal, discount_amount=discount, total_amount=max(subtotal - discount, Decimal("0.00")),
                  currency=settings.stripe_currency.lower())
    db.add(order)
    db.flush()
    for row in rows:
        unit_price = _row_unit_price(row)
        db.add(OrderItem(order_id=order.id, variant_id=row.variant_id, quantity=row.quantity, unit_price=unit_price,
                         reservation_id=row.reservation_id,
                         line_total=unit_price * row.quantity, product_id=row.product_id,
                         product_name=row.product_name, variant_sku=row.variant_sku, size_id=row.size_id, color_id=row.color_id,
                         image_url=row.image_url, image_public_id=row.image_public_id))
    cart.status = CartStatusEnum.checkout_pending
    return order


def checkout_cash(db: Session, user_id: UUID, pickup_branch_id: UUID):
    try:
        expire_due_orders(db)
        cart = _locked_cart(db, user_id)
        if cart.status == CartStatusEnum.checkout_pending:
            raise ValueError("El carrito tiene un checkout pendiente")
        order = _new_order(db, cart, user_id, pickup_branch_id, PaymentMethodEnum.cash)
        db.commit()
        db.refresh(order)
        return _serialize_order(db, order).model_dump()
    except Exception:
        db.rollback()
        raise


def create_stripe_payment(db: Session, user_id: UUID, pickup_branch_id: UUID):
    try:
        expire_due_orders(db)
        cart = _locked_cart(db, user_id)
        existing = db.query(PaymentAttempt).join(Order).filter(PaymentAttempt.cart_id == cart.id, PaymentAttempt.status == "pending").with_for_update().first()
        if existing:
            order = db.query(Order).filter(Order.id == existing.order_id).one()
            attempt = existing
            db.commit()
        elif cart.status == CartStatusEnum.checkout_pending:
            raise ValueError("El carrito tiene un checkout pendiente")
        else:
            order = _new_order(db, cart, user_id, pickup_branch_id, PaymentMethodEnum.stripe)
            attempt = PaymentAttempt(order_id=order.id, cart_id=cart.id, status="pending", idempotency_key=secrets.token_urlsafe(24))
            db.add(attempt)
            db.commit()
    except Exception:
        db.rollback()
        raise
    try:
        import stripe
        if not settings.stripe_secret_key:
            raise ValueError("Stripe no está configurado")
        stripe.api_key = settings.stripe_secret_key
        amount = int((order.total_amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        intent = stripe.PaymentIntent.create(amount=amount, currency=settings.stripe_currency.lower(),
            metadata={"order_id": str(order.id)}, automatic_payment_methods={"enabled": True, "allow_redirects": "never"}, idempotency_key=attempt.idempotency_key)
        attempt.stripe_payment_intent_id = intent.id
        order.stripe_payment_intent_id = intent.id
        db.commit()
        return _serialize_order(db, order).model_dump(), intent.client_secret, intent.id
    except Exception as exc:
        _release_order(db, order, PaymentStatusEnum.failed, FulfillmentStatusEnum.cancelled)
        attempt.status = "failed"
        db.commit()
        raise ValueError(f"No se pudo iniciar el pago con Stripe: {exc}") from exc


def create_stripe_payment_for_order(db: Session, user_id: UUID, order_id: UUID):
    try:
        expire_due_orders(db)
        order = (
            db.query(Order)
            .filter(Order.id == order_id, Order.user_id == user_id)
            .with_for_update()
            .first()
        )
        if not order:
            raise ValueError("Pedido no encontrado")
        if (
            order.payment_status != PaymentStatusEnum.pending
            or order.fulfillment_status != FulfillmentStatusEnum.pending_pickup
        ):
            raise ValueError("El pedido no está pendiente de pago")

        attempt = (
            db.query(PaymentAttempt)
            .filter(PaymentAttempt.order_id == order.id, PaymentAttempt.status == "pending")
            .with_for_update()
            .first()
        )
        if not attempt and not order.stripe_payment_intent_id:
            cart = db.query(Cart).filter(Cart.user_id == order.user_id).first()
            if not cart:
                raise ValueError("El pedido no tiene un intento de pago reutilizable")
            attempt = PaymentAttempt(
                order_id=order.id,
                cart_id=cart.id,
                status="pending",
                idempotency_key=secrets.token_urlsafe(24),
            )
            db.add(attempt)
            order.payment_method = PaymentMethodEnum.stripe
            db.flush()
        db.commit()
    except Exception:
        db.rollback()
        raise

    try:
        import stripe

        if not settings.stripe_secret_key:
            raise ValueError("Stripe no está configurado")
        stripe.api_key = settings.stripe_secret_key

        existing_intent_id = order.stripe_payment_intent_id or (
            attempt.stripe_payment_intent_id if attempt else None
        )
        if existing_intent_id:
            intent = stripe.PaymentIntent.retrieve(existing_intent_id)
            if order.stripe_payment_intent_id != intent.id:
                order.stripe_payment_intent_id = intent.id
                db.commit()
        else:
            amount = int((order.total_amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=order.currency.lower(),
                metadata={"order_id": str(order.id)},
                automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
                idempotency_key=attempt.idempotency_key,
            )
            attempt.stripe_payment_intent_id = intent.id
            order.stripe_payment_intent_id = intent.id
            db.commit()

        return _serialize_order(db, order).model_dump(), intent.client_secret, intent.id
    except Exception as exc:
        db.rollback()
        raise ValueError(f"No se pudo iniciar el pago con Stripe: {exc}") from exc


def _release_order(db: Session, order: Order, payment_status: PaymentStatusEnum, fulfillment_status: FulfillmentStatusEnum) -> None:
    reservation_ids = {item.reservation_id for item in order.items if item.reservation_id}
    for item in order.items:
        inventory = db.query(Inventory).filter(Inventory.variant_id == item.variant_id, Inventory.branch_id == order.pickup_branch_id).with_for_update().one()
        inventory.reserved_quantity -= item.quantity
    cart = db.query(Cart).filter(Cart.user_id == order.user_id).with_for_update().first()
    for reservation_id in reservation_ids:
        reservation = db.query(Reservation).filter(Reservation.id == reservation_id).with_for_update().first()
        if reservation and reservation.status == ReservationStatusEnum.purchase_pending:
            transition_reservation(reservation, ReservationStatusEnum.not_sold)
            reservation.cart_id = None
        if cart:
            db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.reservation_id == reservation_id).delete(synchronize_session=False)
    order.payment_status = payment_status
    order.status = OrderStatusEnum.failed if payment_status == PaymentStatusEnum.failed else OrderStatusEnum.cancelled
    order.fulfillment_status = fulfillment_status
    if cart:
        cart.status = CartStatusEnum.active
    attempt = db.query(PaymentAttempt).filter(PaymentAttempt.order_id == order.id).first()
    if attempt:
        attempt.status = "failed"


def expire_due_orders(db: Session) -> None:
    expired = db.query(Order).filter(
        Order.payment_status == PaymentStatusEnum.pending,
        Order.fulfillment_status == FulfillmentStatusEnum.pending_pickup,
        Order.pickup_expires_at <= datetime.now(timezone.utc),
    ).with_for_update(skip_locked=True).all()
    if not expired:
        return

    intent_ids = [order.stripe_payment_intent_id for order in expired if order.stripe_payment_intent_id]
    for order in expired:
        _release_order(db, order, PaymentStatusEnum.failed, FulfillmentStatusEnum.expired)
    db.commit()

    if not intent_ids or not settings.stripe_secret_key:
        return
    try:
        import stripe

        stripe.api_key = settings.stripe_secret_key
        for intent_id in intent_ids:
            try:
                stripe.PaymentIntent.cancel(intent_id)
            except Exception:
                # A completed or already-cancelled PaymentIntent is safe to ignore.
                pass
    except Exception:
        pass


def _consume_order(db: Session, order: Order, collected_by: UUID | None = None) -> None:
    reservation_ids = {item.reservation_id for item in order.items if item.reservation_id}
    for item in order.items:
        inventory = db.query(Inventory).filter(Inventory.variant_id == item.variant_id, Inventory.branch_id == order.pickup_branch_id).with_for_update().one()
        inventory.quantity -= item.quantity
        inventory.reserved_quantity -= item.quantity
        db.add(InventoryMovement(variant_id=item.variant_id, branch_id=order.pickup_branch_id,
               movement_type=InventoryMovementTypeEnum.outcome, quantity=item.quantity, created_by=collected_by,
               note=f"Pedido {order.id}"))
    order.payment_status = PaymentStatusEnum.paid
    order.status = OrderStatusEnum.paid
    order.fulfillment_status = FulfillmentStatusEnum.collected if collected_by else FulfillmentStatusEnum.pending_pickup
    for reservation_id in reservation_ids:
        reservation = db.query(Reservation).filter(Reservation.id == reservation_id).with_for_update().first()
        if reservation and reservation.status == ReservationStatusEnum.purchase_pending:
            transition_reservation(reservation, ReservationStatusEnum.sold)
            reservation.cart_id = None
    cart = db.query(Cart).filter(Cart.user_id == order.user_id).with_for_update().first()
    if cart:
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(synchronize_session=False)
        cart.status = CartStatusEnum.active
        cart.promotion_code_id = None
        cart.subtotal = cart.discount_amount = cart.total_amount = Decimal("0.00")
    attempt = db.query(PaymentAttempt).filter(PaymentAttempt.order_id == order.id).first()
    if attempt:
        attempt.status = "succeeded"
    if order.promotion_code_id:
        add_usage(db, order.promotion_code_id, order.user_id)
    record_completed_order_interactions(db, order)


def cancel_order(db: Session, user_id: UUID, order_id: UUID):
    try:
        order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).with_for_update().first()
        if not order:
            return None
        if order.payment_status != PaymentStatusEnum.pending or order.fulfillment_status != FulfillmentStatusEnum.pending_pickup:
            raise ValueError("El pedido no se puede cancelar")
        if order.payment_method == PaymentMethodEnum.stripe and order.stripe_payment_intent_id:
            import stripe
            if not settings.stripe_secret_key:
                raise ValueError("Stripe no está configurado")
            stripe.api_key = settings.stripe_secret_key
            stripe.PaymentIntent.cancel(order.stripe_payment_intent_id)
        _release_order(db, order, PaymentStatusEnum.failed, FulfillmentStatusEnum.cancelled)
        db.commit()
        return _serialize_order(db, order).model_dump()
    except Exception:
        db.rollback()
        raise


def collect_cash(db: Session, order_id: UUID, pickup_code: str, cashier_branch_id: UUID | None, cashier_id: UUID):
    try:
        order = db.query(Order).filter(Order.id == order_id).with_for_update().first()
        if not order or cashier_branch_id != order.pickup_branch_id:
            raise ValueError("Pedido no encontrado")
        if order.payment_method != PaymentMethodEnum.cash or order.pickup_code != pickup_code:
            raise ValueError("Código de retiro inválido")
        if order.payment_status != PaymentStatusEnum.pending or order.pickup_expires_at < datetime.now(timezone.utc):
            raise ValueError("El pedido no está disponible para cobro")
        _consume_order(db, order, cashier_id)
        db.commit()
        return _serialize_order(db, order).model_dump()
    except Exception:
        db.rollback()
        raise


def process_stripe_event(db: Session, event) -> None:
    event_id = event["id"]
    try:
        with db.begin_nested():
            db.add(StripeEvent(stripe_event_id=event_id))
            db.flush()
    except IntegrityError:
        return
    data = event["data"]["object"]
    order = db.query(Order).filter(Order.stripe_payment_intent_id == data.get("id")).with_for_update().first()
    if order and order.payment_method == PaymentMethodEnum.stripe and order.payment_status == PaymentStatusEnum.pending:
        if event["type"] == "payment_intent.succeeded":
            expected_amount = int((order.total_amount * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            if data.get("amount") != expected_amount or data.get("currency", "").lower() != order.currency or data.get("metadata", {}).get("order_id") != str(order.id):
                raise ValueError("El PaymentIntent no coincide con el pedido")
            _consume_order(db, order)
        elif event["type"] in {"payment_intent.payment_failed", "payment_intent.canceled"}:
            _release_order(db, order, PaymentStatusEnum.failed, FulfillmentStatusEnum.cancelled)
    db.commit()
