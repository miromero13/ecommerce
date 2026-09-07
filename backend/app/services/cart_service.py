from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.size import Size
from app.models.color import Color
from app.schemas.cart_schema import CartItemCreate, CartItemUpdate, CartRead, CartItemRead, CartStatusEnum


def _available_quantity(db: Session, variant_id: UUID) -> int:
    quantity = (
        db.query(Inventory.quantity, Inventory.reserved_quantity)
        .filter(Inventory.variant_id == variant_id)
        .all()
    )
    return sum(max((row.quantity or 0) - (row.reserved_quantity or 0), 0) for row in quantity)


def _get_active_cart(db: Session, user_id: UUID) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id, Cart.status == CartStatusEnum.active).first()
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


def _load_cart_items(db: Session, cart_id: UUID):
    rows = (
        db.query(
            CartItem.id.label("id"),
            CartItem.cart_id.label("cart_id"),
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
        .order_by(CartItem.id.asc())
        .all()
    )

    return [
        CartItemRead.model_validate(
            {
                **row._mapping,
                "line_total": (row._mapping["unit_price"] or 0) * (row._mapping["quantity"] or 0),
            }
        ).model_dump()
        for row in rows
    ]


def _serialize_cart(db: Session, cart: Cart) -> CartRead:
    cart_items = _load_cart_items(db, cart.id)
    subtotal = sum(Decimal(str(item["line_total"])) for item in cart_items)
    discount_amount = Decimal(str(cart.discount_amount or 0))
    return CartRead.model_validate(
        {
            "id": cart.id,
            "user_id": cart.user_id,
            "status": cart.status,
            "subtotal": subtotal,
            "discount_amount": discount_amount,
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
    cart = _get_active_cart(db, user_id)
    available = _available_quantity(db, payload.variant_id)
    existing = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.variant_id == payload.variant_id).first()
    next_quantity = payload.quantity + (existing.quantity if existing else 0)
    if next_quantity > available:
        raise ValueError("No hay stock disponible suficiente para la variante")

    variant = db.query(ProductVariant).filter(ProductVariant.id == payload.variant_id).first()
    if not variant:
        raise ValueError("Variante no encontrada")

    if existing:
        existing.quantity = next_quantity
        existing.unit_price = variant.price
    else:
        db.add(CartItem(cart_id=cart.id, variant_id=payload.variant_id, quantity=payload.quantity, unit_price=variant.price))

    db.commit()
    db.refresh(cart)
    return _serialize_cart(db, cart)


def update_cart_item(db: Session, user_id: UUID, item_id: UUID, payload: CartItemUpdate) -> CartRead:
    cart = _get_active_cart(db, user_id)
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
    db.commit()
    db.refresh(cart)
    return _serialize_cart(db, cart)


def remove_cart_item(db: Session, user_id: UUID, item_id: UUID) -> CartRead:
    cart = _get_active_cart(db, user_id)
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
    if not item:
        raise ValueError("Item de carrito no encontrado")

    db.delete(item)
    db.commit()
    db.refresh(cart)
    return _serialize_cart(db, cart)


def clear_cart(db: Session, user_id: UUID) -> CartRead:
    cart = _get_active_cart(db, user_id)
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete(synchronize_session=False)
    db.commit()
    db.refresh(cart)
    return _serialize_cart(db, cart)
