from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.branch import Branch
from app.models.reservation import Reservation
from app.models.reservation_item import ReservationItem
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.tenant import Tenant
from app.models.promotion_code import PromotionCode
from app.models.size import Size
from app.models.color import Color
from app.schemas.cart_schema import CartItemCreate, CartItemUpdate, CartRead, CartItemRead, CartStatusEnum
from app.schemas.promotion_schema import PromotionCodeApply
from app.services.pricing_service import discounted_price, discount_amount
from app.services.promotion_service import calculate_discount, cart_has_product_discount, get_code, validate_for_user
from app.services.recommendation_service import ADD_TO_CART, record_interaction


CART_LOCKED_MESSAGE = "Tienes un pedido pendiente de pago. Págalo o cancélalo para modificar el carrito."


# [CU19 - Secuencia: Paso 4.10] wallet_routes invoca pending_order(user_id, exclude_order_id) sobre la entidad Pedido
# [CU19 - Secuencia: Paso 4.11] Pedido retorna pending_order(user_id, exclude_order_id): Order | None a wallet_routes
def pending_order(db: Session, user_id: UUID, exclude_order_id: UUID | None = None) -> Order | None:
    """The customer's latest order still waiting for payment (it holds the cart lock)."""
    from app.schemas.order_schema import FulfillmentStatusEnum, PaymentStatusEnum

    query = db.query(Order).filter(Order.user_id == user_id, Order.payment_status == PaymentStatusEnum.pending,
                                   Order.fulfillment_status == FulfillmentStatusEnum.pending_pickup)
    if exclude_order_id is not None:
        query = query.filter(Order.id != exclude_order_id)
    return query.order_by(Order.created_at.desc()).first()


# [CU25 - Secuencia: Paso 2.13] cart_routes invoca _available_quantity(variant_id, tenant_id, branch_id) sobre la entidad Inventario
# [CU25 - Secuencia: Paso 2.14] Inventario retorna _available_quantity(variant_id, tenant_id, branch_id): int a cart_routes
# [CU30 - Secuencia: Paso 3.10] cart_routes invoca _available_quantity(variant_id, tenant_id, branch_id) sobre la entidad Inventario
# [CU30 - Secuencia: Paso 3.11] Inventario retorna _available_quantity(variant_id, tenant_id, branch_id): int a cart_routes
def _available_quantity(db: Session, variant_id: UUID, tenant_id: UUID, branch_id: UUID | None = None) -> int:
    query = db.query(Inventory.quantity, Inventory.reserved_quantity).join(Branch).filter(
        Inventory.variant_id == variant_id, Inventory.tenant_id == tenant_id,
        Branch.tenant_id == tenant_id,
    )
    if branch_id is not None:
        query = query.filter(Inventory.branch_id == branch_id)
    quantity = query.all()
    return sum(max((row.quantity or 0) - (row.reserved_quantity or 0), 0) for row in quantity)


def _get_active_cart(db: Session, user_id: UUID) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id).with_for_update().first()
    if cart:
        return cart

    cart = Cart(
        user_id=user_id,
        status=CartStatusEnum.active,
        subtotal=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        total_amount=Decimal("0.00"),
    )
    db.add(cart)
    db.flush()
    return cart


def _expire_due_orders(db: Session) -> None:
    # Before locking the cart row: an order past its 40 minutes must not keep the cart locked.
    from app.services.order_service import expire_due_orders

    expire_due_orders(db)


# [CU15 - Secuencia: Pasos 3.2, 4.2] cart_routes invoca _get_mutable_cart(user_id) sobre la entidad Carrito
# [CU15 - Secuencia: Pasos 3.3, 4.3] Carrito retorna _get_mutable_cart(user_id): Cart a cart_routes
# [CU16 - Secuencia: Paso 4.4] wishlist_routes invoca _get_mutable_cart(user_id) sobre la entidad Carrito
# [CU16 - Secuencia: Paso 4.5] Carrito retorna _get_mutable_cart(user_id): Cart a wishlist_routes
# [CU25 - Secuencia: Paso 2.7] cart_routes invoca _get_mutable_cart(user_id) sobre la entidad Carrito
# [CU25 - Secuencia: Paso 2.8] Carrito retorna _get_mutable_cart(user_id): Cart a cart_routes
# [CU30 - Secuencia: Paso 3.4] cart_routes invoca _get_mutable_cart(user_id) sobre la entidad Carrito
# [CU30 - Secuencia: Paso 3.5] Carrito retorna _get_mutable_cart(user_id): Cart a cart_routes
def _get_mutable_cart(db: Session, user_id: UUID) -> Cart:
    _expire_due_orders(db)
    cart = _get_active_cart(db, user_id)
    if cart.status == CartStatusEnum.checkout_pending:
        if pending_order(db, user_id):
            raise ValueError(CART_LOCKED_MESSAGE)
        cart.status = CartStatusEnum.active  # stale lock with no pending order: never lock a cart forever
    return cart


# [CU15 - Secuencia: Paso 3.6] cart_routes invoca validate_cart_company(cart, tenant_id) sobre la entidad Carrito
# [CU15 - Secuencia: Paso 3.7] Carrito retorna validate_cart_company(cart, tenant_id): None a cart_routes
# [CU25 - Secuencia: Paso 2.9] cart_routes invoca validate_cart_company(cart, tenant_id) sobre la entidad Carrito
# [CU25 - Secuencia: Paso 2.10] Carrito retorna validate_cart_company(cart, tenant_id): None a cart_routes
# [CU30 - Secuencia: Paso 3.6] cart_routes invoca validate_cart_company(cart, tenant_id) sobre la entidad Carrito
# [CU30 - Secuencia: Paso 3.7] Carrito retorna validate_cart_company(cart, tenant_id): None a cart_routes
def validate_cart_company(db: Session, cart: Cart, tenant_id: UUID) -> None:
    """Validate before binding an empty cart or mutating an existing one."""
    rows = db.query(ProductVariant, Product).select_from(ProductVariant).join(
        Product, Product.id == ProductVariant.product_id
    ).join(CartItem, CartItem.variant_id == ProductVariant.id).filter(CartItem.cart_id == cart.id).all()
    if rows and cart.tenant_id != tenant_id:
        company = db.query(Tenant.name).filter(Tenant.id == cart.tenant_id).scalar() or "otra empresa"
        raise ValueError(f"Ya tienes un carrito pendiente en {company}. Págalo o vacíalo antes de comprar en otra empresa.")
    if any(variant.tenant_id != tenant_id or product.tenant_id != tenant_id
           for variant, product in rows):
        raise ValueError("El carrito contiene productos de otra empresa")


def _load_cart_items(db: Session, cart_id: UUID):
    rows = (
        db.query(
            CartItem.id.label("id"),
            CartItem.cart_id.label("cart_id"),
            CartItem.variant_id.label("variant_id"),
             CartItem.quantity.label("quantity"),
             CartItem.reservation_id.label("reservation_id"),
            CartItem.unit_price.label("unit_price"),
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            ProductVariant.sku.label("variant_sku"),
            ProductVariant.size_id.label("size_id"),
            ProductVariant.color_id.label("color_id"),
            ProductVariant.image_url.label("image_url"),
             ProductVariant.image_public_id.label("image_public_id"),
             Product.discount_type.label("discount_type"), Product.discount_value.label("discount_value"),
            Size.name.label("size_name"),
            Color.name.label("color_name"),
        )
        .join(ProductVariant, ProductVariant.id == CartItem.variant_id)
        .join(Product, Product.id == ProductVariant.product_id)
        .outerjoin(Size, Size.id == ProductVariant.size_id)
        .outerjoin(Color, Color.id == ProductVariant.color_id)
        .filter(CartItem.cart_id == cart_id)
        .order_by(CartItem.id.asc())
        .all()
    )

    return [
        CartItemRead.model_validate(
            {
                **row._mapping,
                "original_unit_price": row._mapping["unit_price"],
                "unit_price": discounted_price(row._mapping["unit_price"], row._mapping["discount_type"], row._mapping["discount_value"]),
                "discount_amount": discount_amount(row._mapping["unit_price"], row._mapping["discount_type"], row._mapping["discount_value"]),
                "line_total": discounted_price(row._mapping["unit_price"], row._mapping["discount_type"], row._mapping["discount_value"]) * (row._mapping["quantity"] or 0),
            }
        ).model_dump()
        for row in rows
    ]


# [CU15 - Secuencia: Pasos 3.16, 4.6] cart_routes invoca _serialize_cart(cart) sobre la entidad Carrito
# [CU15 - Secuencia: Pasos 3.17, 4.7] Carrito retorna _serialize_cart(cart): CartRead a cart_routes
# [CU25 - Secuencia: Paso 2.19] cart_routes invoca _serialize_cart(cart) sobre la entidad Carrito
# [CU25 - Secuencia: Paso 2.20] Carrito retorna _serialize_cart(cart): CartRead a cart_routes
# [CU30 - Secuencia: Paso 3.16] cart_routes invoca _serialize_cart(cart) sobre la entidad Carrito
# [CU30 - Secuencia: Paso 3.17] Carrito retorna _serialize_cart(cart): CartRead a cart_routes
def _serialize_cart(db: Session, cart: Cart) -> CartRead:
    cart_items = _load_cart_items(db, cart.id)
    subtotal = sum(Decimal(str(item["original_unit_price"])) * int(item["quantity"]) for item in cart_items)
    item_discount = sum(Decimal(str(item["discount_amount"])) * int(item["quantity"]) for item in cart_items)
    coupon = db.query(PromotionCode).filter(PromotionCode.id == cart.promotion_code_id).first() if cart.promotion_code_id else None
    coupon_discount = Decimal("0.00")
    if coupon and item_discount:
        coupon = None
    elif coupon:
        try:
            coupon_discount = calculate_discount(coupon, subtotal)
        except ValueError:
            coupon = None
    discount_amount = item_discount + coupon_discount
    pending = pending_order(db, cart.user_id) if cart.status == CartStatusEnum.checkout_pending else None
    return CartRead.model_validate(
        {
            "id": cart.id,
            "user_id": cart.user_id,
            "tenant_id": cart.tenant_id,
            "tenant_name": db.query(Tenant.name).filter(Tenant.id == cart.tenant_id).scalar() if cart.tenant_id else None,
            "branch_id": cart.branch_id,
            "branch_name": db.query(Branch.name).filter(Branch.id == cart.branch_id).scalar() if cart.branch_id else None,
            "status": cart.status,
            "subtotal": subtotal,
            "discount_amount": discount_amount,
            "promotion_code_id": coupon.id if coupon else None,
            "promotion_code": coupon.code if coupon else None,
            "total_amount": max(subtotal - discount_amount, Decimal("0.00")),
            "item_count": sum(int(item["quantity"]) for item in cart_items),
            "created_at": cart.created_at,
            "updated_at": cart.updated_at,
            "items": cart_items,
            "pending_order_id": pending.id if pending else None,
            "pending_order_expires_at": pending.pickup_expires_at if pending else None,
        }
    )


def get_current_cart(db: Session, user_id: UUID) -> CartRead:
    _expire_due_orders(db)
    cart = _get_active_cart(db, user_id)
    db.commit()
    db.refresh(cart)
    return _serialize_cart(db, cart)


# [CU16 - Secuencia: Pasos 3.6, 4.10] wishlist_routes invoca add_cart_item(user_id, payload) sobre la entidad DetalleCarrito
# [CU16 - Secuencia: Pasos 3.7, 4.11] DetalleCarrito retorna add_cart_item(user_id, payload): CartRead a wishlist_routes
# [CU25 - Secuencia: Paso 2.5] cart_routes invoca add_cart_item(user_id, payload) sobre la entidad DetalleCarrito
# [CU25 - Secuencia: Paso 2.6] DetalleCarrito retorna add_cart_item(user_id, payload): CartRead a cart_routes
# [CU30 - Secuencia: Paso 3.2] cart_routes invoca add_cart_item(user_id, payload) sobre la entidad DetalleCarrito
# [CU30 - Secuencia: Paso 3.3] DetalleCarrito retorna add_cart_item(user_id, payload): CartRead a cart_routes
def add_cart_item(db: Session, user_id: UUID, payload: CartItemCreate) -> CartRead:
    cart = _get_mutable_cart(db, user_id)
    variant = db.query(ProductVariant).join(Product).filter(ProductVariant.id == payload.variant_id).first()
    if not variant:
        raise ValueError("No hay stock disponible suficiente para la variante")
    if not variant.product or variant.tenant_id != variant.product.tenant_id:
        raise ValueError("Variante no encontrada")
    validate_cart_company(db, cart, variant.tenant_id)
    if payload.branch_id is not None:
        branch = db.query(Branch).filter(Branch.id == payload.branch_id,
                                        Branch.tenant_id == variant.tenant_id).first()
        if not branch:
            raise ValueError("Sucursal no encontrada")
    if payload.reservation_id:
        reservation = db.query(Reservation).filter(
            Reservation.id == payload.reservation_id, Reservation.user_id == user_id,
            Reservation.tenant_id == variant.tenant_id,
        ).first()
        line = db.query(ReservationItem).filter(
            ReservationItem.reservation_id == payload.reservation_id,
            ReservationItem.variant_id == variant.id,
            ReservationItem.quantity == payload.quantity,
        ).first()
        if not reservation or not line or (payload.branch_id and reservation.branch_id != payload.branch_id):
            raise ValueError("La reserva ya no está disponible para este checkout")
        # Keep reservation line creation/hold invariants in the existing writer.
        from app.services.reservation_service import transfer_reservation_to_cart
        return transfer_reservation_to_cart(db, user_id, reservation.id)
    existing = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.variant_id == payload.variant_id).first()
    if existing and existing.reservation_id:
        raise ValueError("El carrito ya contiene una línea de una variante reservada")
    available = _available_quantity(db, variant.id, variant.tenant_id, payload.branch_id)
    next_quantity = payload.quantity + (existing.quantity if existing else 0)
    from app.services.offline_sync_service import trusted_time

    # An offline add may still win the unit by time at checkout (CU30), so it is not rejected here.
    if next_quantity > available and not trusted_time(payload.offline_requested_at):
        raise ValueError("No hay stock disponible suficiente para la variante")
    if cart.promotion_code_id and variant.product and variant.product.discount_type and variant.product.discount_value:
        raise ValueError("Retira el cupón antes de agregar un producto con descuento")

    cart.tenant_id = variant.tenant_id
    if payload.branch_id and not cart.branch_id:
        cart.branch_id = payload.branch_id
    if existing:
        existing.quantity = next_quantity
        existing.unit_price = variant.price
    else:
        db.add(CartItem(cart_id=cart.id, variant_id=payload.variant_id, quantity=payload.quantity, unit_price=variant.price))

    record_interaction(db, user_id, variant.product_id, ADD_TO_CART, variant_id=variant.id, branch_id=payload.branch_id)
    refresh_cart_totals(db, cart)
    db.commit()
    db.refresh(cart)
    return _serialize_cart(db, cart)


def update_cart_item(db: Session, user_id: UUID, item_id: UUID, payload: CartItemUpdate) -> CartRead:
    cart = _get_mutable_cart(db, user_id)
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item:
        raise ValueError("Item de carrito no encontrado")

    if payload.quantity == 0:
        db.delete(item)
        refresh_cart_totals(db, cart)
        db.commit()
        db.refresh(cart)
        return _serialize_cart(db, cart)

    validate_cart_company(db, cart, cart.tenant_id)
    if item.reservation_id and payload.quantity != item.quantity:
        raise ValueError("No puedes cambiar la cantidad de una variante reservada")
    available = _available_quantity(db, item.variant_id, cart.tenant_id)
    if payload.quantity > available and not item.reservation_id:
        raise ValueError("No hay stock disponible suficiente para la variante")

    variant = db.query(ProductVariant).filter(ProductVariant.id == item.variant_id).first()
    if not variant:
        raise ValueError("Variante no encontrada")

    item.quantity = payload.quantity
    item.unit_price = variant.price
    refresh_cart_totals(db, cart)
    db.commit()
    db.refresh(cart)
    return _serialize_cart(db, cart)


def remove_cart_item(db: Session, user_id: UUID, item_id: UUID) -> CartRead:
    cart = _get_mutable_cart(db, user_id)
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item:
        raise ValueError("Item de carrito no encontrado")

    db.delete(item)
    refresh_cart_totals(db, cart)
    db.commit()
    db.refresh(cart)
    return _serialize_cart(db, cart)


# [CU16 - Secuencia: Paso 4.6] wishlist_routes invoca clear_cart(user_id) sobre la entidad DetalleCarrito
# [CU16 - Secuencia: Paso 4.7] DetalleCarrito retorna clear_cart(user_id): CartRead a wishlist_routes
def clear_cart(db: Session, user_id: UUID) -> CartRead:
    cart = _get_mutable_cart(db, user_id)
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(synchronize_session=False)
    cart.tenant_id = None
    cart.branch_id = None
    cart.promotion_code_id = None
    refresh_cart_totals(db, cart)
    db.commit()
    db.refresh(cart)
    return _serialize_cart(db, cart)


# [CU15 - Secuencia: Pasos 3.14, 4.4] cart_routes invoca refresh_cart_totals(cart) sobre la entidad Carrito
# [CU15 - Secuencia: Pasos 3.15, 4.5] Carrito retorna refresh_cart_totals(cart): None a cart_routes
# [CU25 - Secuencia: Paso 2.17] cart_routes invoca refresh_cart_totals(cart) sobre la entidad Carrito
# [CU25 - Secuencia: Paso 2.18] Carrito retorna refresh_cart_totals(cart): None a cart_routes
# [CU30 - Secuencia: Paso 3.14] cart_routes invoca refresh_cart_totals(cart) sobre la entidad Carrito
# [CU30 - Secuencia: Paso 3.15] Carrito retorna refresh_cart_totals(cart): None a cart_routes
def refresh_cart_totals(db: Session, cart: Cart) -> None:
    # SessionLocal has autoflush=False: without this, a just-added line is invisible
    # here and the cart would be emptied of its company (tenant_id = None).
    db.flush()
    items = _load_cart_items(db, cart.id)
    # cart_id is a transient association, not reservation history. Detach only
    # after the last line disappears; clearing never changes status or holds.
    linked = db.query(Reservation).filter(
        Reservation.cart_id == cart.id, Reservation.user_id == cart.user_id,
    ).with_for_update().all()
    for reservation in linked:
        remaining = db.query(CartItem.id).filter(
            CartItem.cart_id == cart.id, CartItem.reservation_id == reservation.id,
        ).first()
        if not remaining:
            reservation.cart_id = None
    if not items:
        if not cart.branch_id:
            cart.tenant_id = None
        cart.promotion_code_id = None
    subtotal = sum(Decimal(str(item["original_unit_price"])) * int(item["quantity"]) for item in items)
    item_discount = sum(Decimal(str(item["discount_amount"])) * int(item["quantity"]) for item in items)
    coupon_discount = Decimal("0.00")
    if cart.promotion_code_id and item_discount:
        cart.promotion_code_id = None
    elif cart.promotion_code_id:
        coupon = db.query(PromotionCode).filter(PromotionCode.id == cart.promotion_code_id).first()
        if coupon:
            try:
                coupon_discount = calculate_discount(coupon, subtotal)
            except ValueError:
                cart.promotion_code_id = None
    cart.subtotal = subtotal
    cart.discount_amount = item_discount + coupon_discount
    cart.total_amount = max(subtotal - cart.discount_amount, Decimal("0.00"))


def apply_coupon(db: Session, user_id: UUID, payload: PromotionCodeApply) -> CartRead:
    cart = _get_mutable_cart(db, user_id)
    if not cart.items:
        raise ValueError("El carrito está vacío")
    if cart_has_product_discount(db, cart.id):
        raise ValueError("No puedes aplicar un cupón a un carrito con productos rebajados")
    validate_cart_company(db, cart, cart.tenant_id)
    code_obj = get_code(db, payload.code)
    if not code_obj or code_obj.tenant_id != cart.tenant_id:
        raise ValueError("El código promocional no existe, está inactivo o fuera de vigencia")
    if code_obj.branch_id is not None:
        if cart.branch_id is None:
            raise ValueError("Este código promocional es exclusivo de una sucursal. Selecciona la sucursal antes de aplicarlo")
        if code_obj.branch_id != cart.branch_id:
            raise ValueError("El código promocional no aplica a esta sucursal")
    code = validate_for_user(db, payload.code, user_id, branch_id=cart.branch_id, tenant_id=cart.tenant_id)
    items = _load_cart_items(db, cart.id)
    subtotal = sum(Decimal(str(item["original_unit_price"])) * int(item["quantity"]) for item in items)
    calculate_discount(code, subtotal)
    cart.promotion_code_id = code.id
    refresh_cart_totals(db, cart)
    db.commit()
    db.refresh(cart)
    return _serialize_cart(db, cart)


# [CU16 - Secuencia: Paso 4.8] wishlist_routes invoca set_cart_branch(user_id, branch_id) sobre la entidad Sucursal
# [CU16 - Secuencia: Paso 4.9] Sucursal retorna set_cart_branch(user_id, branch_id): tuple[CartRead, str | None] a wishlist_routes
def set_cart_branch(db: Session, user_id: UUID, branch_id: UUID | None) -> tuple[CartRead, str | None]:
    cart = _get_mutable_cart(db, user_id)
    warning_message = None
    if branch_id is not None:
        branch = db.query(Branch).filter(Branch.id == branch_id).first()
        if not branch:
            raise ValueError("Sucursal no encontrada")
        if cart.tenant_id and branch.tenant_id != cart.tenant_id:
            raise ValueError("La sucursal no pertenece a la empresa de los productos en tu carrito")
        if cart.branch_id and cart.branch_id != branch_id and cart.items:
            db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(synchronize_session=False)
            cart.promotion_code_id = None
            warning_message = "Al cambiar de sucursal, el carrito se reinició porque el inventario pertenece a cada tienda física"
        cart.branch_id = branch_id
        cart.tenant_id = branch.tenant_id
    else:
        if cart.items:
            db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(synchronize_session=False)
            cart.promotion_code_id = None
            warning_message = "Al desvincular la sucursal, el carrito se vació"
        cart.branch_id = None
        cart.tenant_id = None

    refresh_cart_totals(db, cart)
    db.commit()
    db.refresh(cart)
    return _serialize_cart(db, cart), warning_message


def remove_coupon(db: Session, user_id: UUID) -> CartRead:
    cart = _get_mutable_cart(db, user_id)
    cart.promotion_code_id = None
    refresh_cart_totals(db, cart)
    db.commit()
    db.refresh(cart)
    return _serialize_cart(db, cart)
