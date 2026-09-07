from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.branch import Branch
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.inventory import Inventory
from app.models.inventory_movement import InventoryMovement
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product_variant import ProductVariant
from app.models.product import Product
from app.models.size import Size
from app.models.color import Color
from app.schemas.cart_schema import CartStatusEnum
from app.schemas.order_schema import OrderRead, OrderItemRead, OrderStatusEnum, PaymentMethodEnum, PaymentStatusEnum
from app.schemas.catalog_enums import ProductStatusEnum
from app.schemas.inventory_schema import InventoryMovementTypeEnum


def _get_active_cart(db: Session, user_id: UUID) -> Cart | None:
    return db.query(Cart).filter(Cart.user_id == user_id, Cart.status == CartStatusEnum.active).first()


def _cart_rows(db: Session, cart_id: UUID):
    return (
        db.query(
            CartItem.id.label("cart_item_id"),
            CartItem.variant_id.label("variant_id"),
            CartItem.quantity.label("quantity"),
            CartItem.unit_price.label("unit_price"),
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
        .join(ProductVariant, ProductVariant.id == CartItem.variant_id)
        .join(Product, Product.id == ProductVariant.product_id)
        .outerjoin(Size, Size.id == ProductVariant.size_id)
        .outerjoin(Color, Color.id == ProductVariant.color_id)
        .filter(CartItem.cart_id == cart_id)
        .all()
    )


def _serialize_order(db: Session, order: Order) -> OrderRead:
    item_rows = (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order.id)
        .order_by(OrderItem.id.asc())
        .all()
    )

    items = [
        OrderItemRead.model_validate(
            {
                "id": row.id,
                "order_id": row.order_id,
                "variant_id": row.variant_id,
                "quantity": row.quantity,
                "unit_price": row.unit_price,
                "line_total": row.line_total,
                "product_id": row.product_id,
                "product_name": row.product_name,
                "variant_sku": row.variant_sku,
                "size_id": row.size_id,
                "color_id": row.color_id,
                "size_name": row.size_id and db.query(Size.name).filter(Size.id == row.size_id).scalar(),
                "color_name": row.color_id and db.query(Color.name).filter(Color.id == row.color_id).scalar(),
                "image_url": row.image_url,
                "image_public_id": row.image_public_id,
            }
        ).model_dump()
        for row in item_rows
    ]

    return OrderRead.model_validate(
        {
            "id": order.id,
            "user_id": order.user_id,
            "status": order.status,
            "payment_method": order.payment_method,
            "payment_status": order.payment_status,
            "stripe_payment_intent_id": order.stripe_payment_intent_id,
            "cash_reference": order.cash_reference,
            "subtotal": order.subtotal,
            "discount_amount": order.discount_amount,
            "total_amount": order.total_amount,
            "currency": order.currency,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            "items": items,
        }
    )


def list_orders(db: Session, user_id: UUID):
    orders = db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()
    return [_serialize_order(db, order).model_dump() for order in orders]


def get_order(db: Session, user_id: UUID, order_id: UUID):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).first()
    if not order:
        return None
    return _serialize_order(db, order).model_dump()


def _find_inventory_rows(db: Session, variant_id: UUID):
    return (
        db.query(Inventory)
        .filter(Inventory.variant_id == variant_id)
        .join(Branch, Branch.id == Inventory.branch_id)
        .order_by(Branch.is_default.desc(), Inventory.quantity.desc(), Branch.name.asc())
        .with_for_update()
        .all()
    )


def _allocate_inventory(db: Session, variant_id: UUID, quantity: int):
    rows = _find_inventory_rows(db, variant_id)
    remaining = quantity
    for inventory in rows:
        available = max((inventory.quantity or 0) - (inventory.reserved_quantity or 0), 0)
        if available <= 0:
            continue
        take = min(available, remaining)
        inventory.quantity -= take
        db.add(
            InventoryMovement(
                variant_id=variant_id,
                branch_id=inventory.branch_id,
                movement_type=InventoryMovementTypeEnum.outcome,
                quantity=take,
                note="Checkout de carrito",
            )
        )
        remaining -= take
        if remaining == 0:
            break
    if remaining > 0:
        raise ValueError("No hay stock suficiente para completar la orden")


def _create_order_from_cart(db: Session, cart: Cart, user_id: UUID, payment_method: PaymentMethodEnum, payment_status: PaymentStatusEnum, cash_reference: str | None = None, stripe_payment_intent_id: str | None = None) -> Order:
    cart_rows = _cart_rows(db, cart.id)
    if not cart_rows:
        raise ValueError("El carrito está vacío")

    subtotal = sum(Decimal(str(row.unit_price)) * int(row.quantity) for row in cart_rows)
    discount_amount = Decimal(str(cart.discount_amount or 0))
    total_amount = max(subtotal - discount_amount, Decimal("0.00"))

    order = Order(
        user_id=user_id,
        status=OrderStatusEnum.paid if payment_status == PaymentStatusEnum.paid else OrderStatusEnum.pending,
        payment_method=payment_method,
        payment_status=payment_status,
        stripe_payment_intent_id=stripe_payment_intent_id,
        cash_reference=cash_reference,
        subtotal=subtotal,
        discount_amount=discount_amount,
        total_amount=total_amount,
        currency="usd",
    )
    db.add(order)
    db.flush()

    for row in cart_rows:
        line_total = Decimal(str(row.unit_price)) * int(row.quantity)
        db.add(
            OrderItem(
                order_id=order.id,
                variant_id=row.variant_id,
                quantity=row.quantity,
                unit_price=row.unit_price,
                line_total=line_total,
                product_id=row.product_id,
                product_name=row.product_name,
                variant_sku=row.variant_sku,
                size_id=row.size_id,
                color_id=row.color_id,
                image_url=row.image_url,
                image_public_id=row.image_public_id,
            )
        )

    return order


def checkout_cash(db: Session, user_id: UUID, cash_reference: str | None = None):
    cart = _get_active_cart(db, user_id)
    if not cart:
        raise ValueError("No tienes un carrito activo")

    try:
        order = _create_order_from_cart(
            db,
            cart,
            user_id,
            payment_method=PaymentMethodEnum.cash,
            payment_status=PaymentStatusEnum.paid,
            cash_reference=cash_reference,
        )
        for row in _cart_rows(db, cart.id):
            _allocate_inventory(db, row.variant_id, int(row.quantity))
        cart.status = CartStatusEnum.active
        cart.subtotal = Decimal("0.00")
        cart.discount_amount = Decimal("0.00")
        cart.total_amount = Decimal("0.00")
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(synchronize_session=False)
        db.commit()
        db.refresh(order)
        return _serialize_order(db, order).model_dump()
    except Exception:
        db.rollback()
        raise


def create_stripe_payment(db: Session, user_id: UUID, currency: str = "usd"):
    cart = _get_active_cart(db, user_id)
    if not cart:
        raise ValueError("No tienes un carrito activo")

    cart_rows = _cart_rows(db, cart.id)
    if not cart_rows:
        raise ValueError("El carrito está vacío")

    subtotal = sum(Decimal(str(row.unit_price)) * int(row.quantity) for row in cart_rows)
    discount_amount = Decimal(str(cart.discount_amount or 0))
    total_amount = max(subtotal - discount_amount, Decimal("0.00"))
    order = None

    order = _create_order_from_cart(
        db,
        cart,
        user_id,
        payment_method=PaymentMethodEnum.stripe,
        payment_status=PaymentStatusEnum.pending,
    )
    db.commit()

    try:
        import stripe

        from app.core.config import settings

        if not settings.stripe_secret_key:
            raise ValueError("Stripe no está configurado")
        stripe.api_key = settings.stripe_secret_key
        stripe_currency = (currency or settings.stripe_currency or "usd").lower()
        payment_intent = stripe.PaymentIntent.create(
            amount=int(total_amount * 100),
            currency=stripe_currency,
            metadata={"order_id": str(order.id), "user_id": str(user_id)},
        )
        order.stripe_payment_intent_id = payment_intent["id"]
        order.currency = stripe_currency
        cart.status = CartStatusEnum.active
        cart.subtotal = Decimal("0.00")
        cart.discount_amount = Decimal("0.00")
        cart.total_amount = Decimal("0.00")
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(synchronize_session=False)
        db.commit()
        db.refresh(order)
        return _serialize_order(db, order).model_dump(), payment_intent["client_secret"]
    except Exception as exc:
        if order is not None:
            order.payment_status = PaymentStatusEnum.failed
            order.status = OrderStatusEnum.failed
            db.commit()
        raise ValueError(f"No se pudo iniciar el pago con Stripe: {exc}") from exc


def confirm_stripe_payment(db: Session, payment_intent_id: str, succeeded: bool):
    order = db.query(Order).filter(Order.stripe_payment_intent_id == payment_intent_id).first()
    if not order:
        return None

    try:
        if not succeeded:
            order.payment_status = PaymentStatusEnum.failed
            order.status = OrderStatusEnum.failed
            db.commit()
            db.refresh(order)
            return _serialize_order(db, order).model_dump()

        for item in order.items:
            _allocate_inventory(db, item.variant_id, item.quantity)
        order.payment_status = PaymentStatusEnum.paid
        order.status = OrderStatusEnum.paid
        db.commit()
        db.refresh(order)
        return _serialize_order(db, order).model_dump()
    except Exception:
        db.rollback()
        raise
