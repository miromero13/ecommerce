from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.promotion_code import PromotionCode
from app.models.size import Size
from app.models.color import Color
from app.schemas.cart_schema import CartItemCreate, CartItemUpdate, CartRead, CartItemRead, CartStatusEnum
from app.schemas.promotion_schema import PromotionCodeApply
from app.services.pricing_service import discounted_price, discount_amount
from app.services.promotion_service import calculate_discount, cart_has_product_discount, get_code, validate_for_user
from app.services.recommendation_service import ADD_TO_CART, record_interaction


def _available_quantity(db: Session, variant_id: UUID) -> int:
    quantity = (
        db.query(Inventory.quantity, Inventory.reserved_quantity)
        .filter(Inventory.variant_id == variant_id)
        .all()
    )
    return sum(max((row.quantity or 0) - (row.reserved_quantity or 0), 0) for row in quantity)


def _get_active_cart(db: Session, user_id: UUID) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
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
    db.commit()
    db.refresh(cart)
    return cart


def _get_mutable_cart(db: Session, user_id: UUID) -> Cart:
    cart = _get_active_cart(db, user_id)
    if cart.status == CartStatusEnum.checkout_pending:
        raise ValueError("El carrito tiene un checkout pendiente")
    return cart


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
    return CartRead.model_validate(
        {
            "id": cart.id,
            "user_id": cart.user_id,
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
        }
    )


def get_current_cart(db: Session, user_id: UUID) -> CartRead:
    cart = _get_active_cart(db, user_id)
    return _serialize_cart(db, cart)


def add_cart_item(db: Session, user_id: UUID, payload: CartItemCreate) -> CartRead:
    cart = _get_mutable_cart(db, user_id)
    available = _available_quantity(db, payload.variant_id)
    existing = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.variant_id == payload.variant_id).first()
    next_quantity = payload.quantity + (existing.quantity if existing else 0)
    if next_quantity > available:
        raise ValueError("No hay stock disponible suficiente para la variante")

    variant = db.query(ProductVariant).join(Product).filter(ProductVariant.id == payload.variant_id).first()
    if not variant:
        raise ValueError("Variante no encontrada")
    if cart.promotion_code_id and variant.product and variant.product.discount_type and variant.product.discount_value:
        raise ValueError("Retira el cupón antes de agregar un producto con descuento")

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
        db.commit()
        db.refresh(cart)
        return _serialize_cart(db, cart)

    available = _available_quantity(db, item.variant_id)
    if payload.quantity > available:
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


def clear_cart(db: Session, user_id: UUID) -> CartRead:
    cart = _get_mutable_cart(db, user_id)
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(synchronize_session=False)
    refresh_cart_totals(db, cart)
    db.commit()
    db.refresh(cart)
    return _serialize_cart(db, cart)


def refresh_cart_totals(db: Session, cart: Cart) -> None:
    items = _load_cart_items(db, cart.id)
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
    code = validate_for_user(db, payload.code, user_id)
    items = _load_cart_items(db, cart.id)
    subtotal = sum(Decimal(str(item["original_unit_price"])) * int(item["quantity"]) for item in items)
    calculate_discount(code, subtotal)
    cart.promotion_code_id = code.id
    refresh_cart_totals(db, cart)
    db.commit()
    db.refresh(cart)
    return _serialize_cart(db, cart)


def remove_coupon(db: Session, user_id: UUID) -> CartRead:
    cart = _get_mutable_cart(db, user_id)
    cart.promotion_code_id = None
    refresh_cart_totals(db, cart)
    db.commit()
    db.refresh(cart)
    return _serialize_cart(db, cart)
