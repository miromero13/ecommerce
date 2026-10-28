"""CU16 wishlist: favorites per customer, with move-to-cart through the regular cart rules."""
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.color import Color
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.size import Size
from app.models.tenant import Tenant
from app.models.wishlist_item import WishlistItem
from app.schemas.cart_schema import CartItemCreate
from app.schemas.catalog_enums import ProductStatusEnum
from app.services.cart_service import _available_quantity, add_cart_item
from app.services.pricing_service import discounted_price

NO_STOCK = "No hay stock disponible para mover la prenda al carrito"


class AlreadySaved(RuntimeError):
    pass


def _active_variants(db: Session, product_id: UUID):
    """Active variants of a product with their size and color names."""
    return (db.query(ProductVariant, Size.name, Color.name)
            .outerjoin(Size, Size.id == ProductVariant.size_id)
            .outerjoin(Color, Color.id == ProductVariant.color_id)
            .filter(ProductVariant.product_id == product_id, ProductVariant.status == ProductStatusEnum.active)
            .order_by(ProductVariant.sku.asc()).all())


def _serialize(db: Session, item: WishlistItem) -> dict:
    product = db.query(Product).filter(Product.id == item.product_id).one()
    rows = _active_variants(db, product.id)
    variants = [{
        "id": variant.id, "sku": variant.sku, "size": size, "color": color,
        "price": discounted_price(variant.price, product.discount_type, product.discount_value),
        "available": _available_quantity(db, variant.id, product.tenant_id),
    } for variant, size, color in rows]
    return {
        "id": item.id, "product_id": product.id, "product_name": product.name,
        "tenant_id": product.tenant_id,
        "tenant_name": db.query(Tenant.name).filter(Tenant.id == product.tenant_id).scalar(),
        "price": min((v["price"] for v in variants), default=None),
        "image_url": next((variant.image_url for variant, _, _ in rows if variant.image_url), None),
        "in_stock": any(v["available"] > 0 for v in variants),
        "variants": variants, "created_at": item.created_at,
    }


def list_items(db: Session, user_id: UUID) -> list[dict]:
    items = db.query(WishlistItem).filter(WishlistItem.user_id == user_id).order_by(WishlistItem.created_at.desc()).all()
    return [_serialize(db, item) for item in items]


def add_item(db: Session, user_id: UUID, product_id: UUID) -> WishlistItem:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product or not _active_variants(db, product.id):
        raise LookupError("La prenda seleccionada no existe en el catálogo")
    item = WishlistItem(tenant_id=product.tenant_id, user_id=user_id, product_id=product.id)
    db.add(item)
    try:
        db.flush()  # the unique constraint is the source of truth, also under concurrent clicks
        from app.services.recommendation_service import record_wishlist_interaction
        record_wishlist_interaction(db, user_id, product.id)  # CU6 signal
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AlreadySaved("La prenda ya se encuentra en tu lista de deseos") from exc
    db.refresh(item)
    return item


def _owned(db: Session, user_id: UUID, product_id: UUID) -> WishlistItem:
    item = db.query(WishlistItem).filter(WishlistItem.user_id == user_id, WishlistItem.product_id == product_id).first()
    if not item:
        raise LookupError("La prenda no está en tu lista de deseos")
    return item


def remove_item(db: Session, user_id: UUID, product_id: UUID) -> None:
    db.delete(_owned(db, user_id, product_id))
    db.commit()


def move_to_cart(db: Session, user_id: UUID, product_id: UUID, variant_id: UUID, branch_id: UUID | None, quantity: int):
    item_id = _owned(db, user_id, product_id).id
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id, ProductVariant.product_id == product_id).first()
    if not variant:
        raise ValueError("La talla o color elegido no pertenece a esta prenda")
    try:
        cart = add_cart_item(db, user_id, CartItemCreate(variant_id=variant_id, branch_id=branch_id, quantity=quantity))
    except ValueError as exc:
        # Same cart rules as the catalog (one company per cart, stock); clearer stock message.
        raise ValueError(NO_STOCK if "stock" in str(exc).lower() else str(exc)) from exc
    # The cart already committed; the favorite leaves the list only after the garment is in the cart.
    db.query(WishlistItem).filter(WishlistItem.id == item_id).delete(synchronize_session=False)
    db.commit()
    return cart
