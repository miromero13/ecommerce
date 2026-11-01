"""CU16 wishlist: favorites per customer, with move-to-cart through the regular cart rules."""
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.branch import Branch
from app.models.color import Color
from app.models.inventory import Inventory
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


# [CU16 - Secuencia: Pasos 2.8, 5.8] wishlist_routes invoca _active_variants(product_id) sobre la entidad VarianteProducto
# [CU16 - Secuencia: Pasos 2.9, 5.9] VarianteProducto retorna _active_variants(product_id): db.query(ProductVariant, Size.name, Color.name).outerjoin... a wishlist_routes
def _active_variants(db: Session, product_id: UUID):
    """Active variants of a product with their size and color names."""
    return (db.query(ProductVariant, Size.name, Color.name)
            .outerjoin(Size, Size.id == ProductVariant.size_id)
            .outerjoin(Color, Color.id == ProductVariant.color_id)
            .filter(ProductVariant.product_id == product_id, ProductVariant.status == ProductStatusEnum.active)
            .order_by(ProductVariant.sku.asc()).all())


# [CU16 - Secuencia: Pasos 1.4, 2.16, 3.12, 4.16, 5.16] wishlist_routes invoca _serialize(item) sobre la entidad ProductoFavorito
# [CU16 - Secuencia: Pasos 1.5, 2.17, 3.13, 4.17, 5.17] ProductoFavorito retorna _serialize(item): dict a wishlist_routes
def _serialize(db: Session, item: WishlistItem) -> dict:
    product = db.query(Product).filter(Product.id == item.product_id).one()
    rows = _active_variants(db, product.id)
    variant_ids = [variant.id for variant, _, _ in rows]

    branch_stocks_raw = (
        db.query(Inventory, Branch)
        .join(Branch, Inventory.branch_id == Branch.id)
        .filter(
            Inventory.variant_id.in_(variant_ids),
            Branch.is_active == True,
            (Inventory.quantity - Inventory.reserved_quantity) > 0,
        )
        .all()
    ) if variant_ids else []

    variant_branch_stocks = {}
    item_branches = {}
    for inv, br in branch_stocks_raw:
        avail = max((inv.quantity or 0) - (inv.reserved_quantity or 0), 0)
        if avail > 0:
            variant_branch_stocks.setdefault(inv.variant_id, []).append({
                "branch_id": br.id,
                "branch_name": br.name,
                "city": br.city,
                "quantity": avail,
            })
            if br.id not in item_branches:
                item_branches[br.id] = {
                    "branch_id": br.id,
                    "branch_name": br.name,
                    "city": br.city,
                }

    variants = [{
        "id": variant.id, "sku": variant.sku, "size": size, "color": color,
        "price": discounted_price(variant.price, product.discount_type, product.discount_value),
        "available": _available_quantity(db, variant.id, product.tenant_id),
        "branch_stocks": variant_branch_stocks.get(variant.id, []),
    } for variant, size, color in rows]
    return {
        "id": item.id, "product_id": product.id, "product_name": product.name,
        "tenant_id": product.tenant_id,
        "tenant_name": db.query(Tenant.name).filter(Tenant.id == product.tenant_id).scalar(),
        "price": min((v["price"] for v in variants), default=None),
        "image_url": next((variant.image_url for variant, _, _ in rows if variant.image_url), None),
        "in_stock": any(v["available"] > 0 for v in variants),
        "available_branches": list(item_branches.values()),
        "variants": variants, "created_at": item.created_at,
    }


# [CU16 - Secuencia: Pasos 1.2, 2.14, 3.10, 4.14, 5.14] wishlist_routes invoca list_items(user_id) sobre la entidad ProductoFavorito
# [CU16 - Secuencia: Pasos 1.3, 2.15, 3.11, 4.15, 5.15] ProductoFavorito retorna list_items(user_id): list[dict] a wishlist_routes
def list_items(db: Session, user_id: UUID) -> list[dict]:
    items = db.query(WishlistItem).filter(WishlistItem.user_id == user_id).order_by(WishlistItem.created_at.desc()).all()
    return [_serialize(db, item) for item in items]


# [CU16 - Secuencia: Pasos 2.6, 5.6] wishlist_routes invoca add_item(user_id, product_id) sobre la entidad ProductoFavorito
# [CU16 - Secuencia: Pasos 2.7, 5.7] ProductoFavorito retorna add_item(user_id, product_id): WishlistItem a wishlist_routes
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


# [CU16 - Secuencia: Pasos 2.2, 3.4, 5.2] wishlist_routes invoca _owned(user_id, product_id) sobre la entidad ProductoFavorito
# [CU16 - Secuencia: Pasos 2.3, 3.5, 5.3] ProductoFavorito retorna _owned(user_id, product_id): WishlistItem a wishlist_routes
def _owned(db: Session, user_id: UUID, product_id: UUID) -> WishlistItem:
    item = db.query(WishlistItem).filter(WishlistItem.user_id == user_id, WishlistItem.product_id == product_id).first()
    if not item:
        raise LookupError("La prenda no está en tu lista de deseos")
    return item


def remove_item(db: Session, user_id: UUID, product_id: UUID) -> None:
    db.delete(_owned(db, user_id, product_id))
    db.commit()


# [CU16 - Secuencia: Paso 3.2] wishlist_routes invoca move_to_cart(user_id, product_id, variant_id, branch_id, quantity) sobre la entidad VarianteProducto
# [CU16 - Secuencia: Paso 3.3] VarianteProducto retorna move_to_cart(user_id, product_id, variant_id, branch_id, quantity): cart a wishlist_routes
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


# [CU16 - Secuencia: Paso 4.2] wishlist_routes invoca move_all_to_cart(user_id, tenant_id, branch_id, clear_conflict) sobre la entidad Sucursal
# [CU16 - Secuencia: Paso 4.3] Sucursal retorna move_all_to_cart(user_id, tenant_id, branch_id, clear_conflict): (get_current_cart(db, user_id), moved_count) a wishlist_routes
def move_all_to_cart(db: Session, user_id: UUID, tenant_id: UUID, branch_id: UUID, clear_conflict: bool = True):
    branch = db.query(Branch).filter(Branch.id == branch_id, Branch.tenant_id == tenant_id).first()
    if not branch:
        raise ValueError("Sucursal no encontrada para esta empresa")

    from app.services.cart_service import _get_mutable_cart, clear_cart, set_cart_branch, get_current_cart
    cart = _get_mutable_cart(db, user_id)
    if cart.tenant_id and cart.tenant_id != tenant_id:
        if clear_conflict:
            clear_cart(db, user_id)
        else:
            company = db.query(Tenant.name).filter(Tenant.id == cart.tenant_id).scalar() or "otra empresa"
            raise ValueError(f"Ya tienes un carrito pendiente en {company}. Págalo o vacíalo antes de comprar en otra empresa.")
    elif cart.branch_id and cart.branch_id != branch_id:
        set_cart_branch(db, user_id, branch_id)

    wishlist_items = (
        db.query(WishlistItem)
        .filter(WishlistItem.user_id == user_id, WishlistItem.tenant_id == tenant_id)
        .all()
    )
    if not wishlist_items:
        raise ValueError("No tienes prendas en tu lista de deseos para esta empresa")

    moved_count = 0
    for w_item in wishlist_items:
        active_variants = (
            db.query(ProductVariant)
            .filter(ProductVariant.product_id == w_item.product_id, ProductVariant.status == ProductStatusEnum.active)
            .order_by(ProductVariant.sku.asc())
            .all()
        )
        selected_variant = None
        for variant in active_variants:
            inv = (
                db.query(Inventory)
                .filter(
                    Inventory.variant_id == variant.id,
                    Inventory.branch_id == branch_id,
                )
                .first()
            )
            if inv and max((inv.quantity or 0) - (inv.reserved_quantity or 0), 0) > 0:
                selected_variant = variant
                break

        if selected_variant:
            try:
                add_cart_item(db, user_id, CartItemCreate(variant_id=selected_variant.id, branch_id=branch_id, quantity=1))
                db.delete(w_item)
                moved_count += 1
            except Exception:
                continue

    db.commit()
    if moved_count == 0:
        raise ValueError("Ninguna de las prendas seleccionadas tiene stock disponible en esta sucursal")

    return get_current_cart(db, user_id), moved_count
