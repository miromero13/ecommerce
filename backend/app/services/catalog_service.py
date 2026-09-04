from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.models.color import Color
from app.models.collection import Collection
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.season import Season
from app.models.size import Size
from app.schemas.catalog_schema import (
    NameCreate,
    ColorCreate,
    CollectionCreate,
    ProductCreate,
    ProductVariantStatusUpdate,
    ProductRead,
    ProductVariantRead,
)
from app.schemas.catalog_enums import ProductStatusEnum


def create_name_item(db: Session, model, payload: NameCreate):
    item = model(name=payload.name)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def create_color(db: Session, payload: ColorCreate):
    item = Color(name=payload.name, hex_code=payload.hex_code)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def create_collection(db: Session, payload: CollectionCreate):
    item = Collection(name=payload.name, season_id=payload.season_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _normalized_variants(payload: ProductCreate, default_status: ProductStatusEnum) -> list[dict]:
    variants = payload.variants or []
    if not variants:
        if not payload.sku:
            raise ValueError("El producto debe incluir al menos una variante con SKU")
        variants = [
            {
                "sku": payload.sku,
                "price": payload.price,
                "size_id": payload.size_id,
                "color_id": payload.color_id,
                "status": payload.status or default_status,
            }
        ]

    normalized = []
    for variant in variants:
        normalized.append(
            {
                "sku": variant.sku,
                "price": variant.price if variant.price is not None else payload.price,
                "size_id": variant.size_id,
                "color_id": variant.color_id,
                "status": variant.status or default_status,
            }
        )
    return normalized


def _validate_variant_payload(variants: list[dict]) -> None:
    sku_set: set[str] = set()
    combo_set: set[tuple] = set()

    for variant in variants:
        sku = variant["sku"]
        combo = (variant["size_id"], variant["color_id"])

        if sku in sku_set:
            raise ValueError("No se pueden repetir SKUs dentro del mismo producto")
        if combo in combo_set:
            raise ValueError("No se puede repetir la combinacion talla y color dentro del mismo producto")

        sku_set.add(sku)
        combo_set.add(combo)


def create_product(
    db: Session,
    payload: ProductCreate,
    provider_id=None,
    status: ProductStatusEnum = ProductStatusEnum.active,
):
    try:
        normalized_variants = _normalized_variants(payload, status)
        _validate_variant_payload(normalized_variants)

        product = Product(
            name=payload.name,
            description=payload.description,
            price=payload.price,
            provider_id=provider_id,
            category_id=payload.category_id,
            season_id=payload.season_id,
            collection_id=payload.collection_id,
        )
        db.add(product)
        db.flush()

        variants = []
        for variant_data in normalized_variants:
            variant = ProductVariant(
                product_id=product.id,
                sku=variant_data["sku"],
                price=variant_data["price"],
                size_id=variant_data["size_id"],
                color_id=variant_data["color_id"],
                status=variant_data["status"],
            )
            db.add(variant)
            variants.append(variant)

        if variants:
            product.price = variants[0].price

        db.commit()

        db.refresh(product)
        for variant in variants:
            db.refresh(variant)
        return product
    except IntegrityError:
        db.rollback()
        raise ValueError("No se pudo crear el producto")


def update_product_status(db: Session, variant_id, update_data: ProductVariantStatusUpdate):
    variant = db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
    if not variant:
        return None
    variant.status = update_data.status
    db.commit()
    db.refresh(variant)
    return variant


def update_name_item(db: Session, model, item_id, payload):
    item = db.query(model).filter(model.id == item_id).first()
    if not item:
        return None

    for field, value in payload.model_dump().items():
        setattr(item, field, value)

    try:
        db.commit()
        db.refresh(item)
        return item
    except IntegrityError:
        db.rollback()
        raise ValueError("No se pudo actualizar el registro")


def delete_category(db: Session, category_id) -> bool:
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        return False

    if db.query(Product).filter(Product.category_id == category_id).first():
        raise ValueError("No se puede eliminar una categoria con productos asociados")

    db.delete(category)
    db.commit()
    return True


def delete_size(db: Session, size_id) -> bool:
    size = db.query(Size).filter(Size.id == size_id).first()
    if not size:
        return False

    if db.query(ProductVariant).filter(ProductVariant.size_id == size_id).first():
        raise ValueError("No se puede eliminar una talla con variantes asociadas")

    db.delete(size)
    db.commit()
    return True


def delete_color(db: Session, color_id) -> bool:
    color = db.query(Color).filter(Color.id == color_id).first()
    if not color:
        return False

    if db.query(ProductVariant).filter(ProductVariant.color_id == color_id).first():
        raise ValueError("No se puede eliminar un color con variantes asociadas")

    db.delete(color)
    db.commit()
    return True


def delete_season(db: Session, season_id) -> bool:
    season = db.query(Season).filter(Season.id == season_id).first()
    if not season:
        return False

    if db.query(Product).filter(Product.season_id == season_id).first():
        raise ValueError("No se puede eliminar una temporada con productos asociados")
    if db.query(Collection).filter(Collection.season_id == season_id).first():
        raise ValueError("No se puede eliminar una temporada con colecciones asociadas")

    db.delete(season)
    db.commit()
    return True


def delete_collection(db: Session, collection_id) -> bool:
    collection = db.query(Collection).filter(Collection.id == collection_id).first()
    if not collection:
        return False

    if db.query(Product).filter(Product.collection_id == collection_id).first():
        raise ValueError("No se puede eliminar una coleccion con productos asociados")

    db.delete(collection)
    db.commit()
    return True


def update_product(db: Session, product_id, payload: ProductCreate) -> Product | None:
    product = db.query(Product).options(selectinload(Product.variants)).filter(Product.id == product_id).first()
    if not product:
        return None

    try:
        variant_ids = [variant.id for variant in product.variants]
        if variant_ids:
            db.query(Inventory).filter(Inventory.variant_id.in_(variant_ids)).delete(synchronize_session=False)
            db.query(ProductVariant).filter(ProductVariant.id.in_(variant_ids)).delete(synchronize_session=False)

        product.name = payload.name
        product.description = payload.description
        product.price = payload.price
        product.provider_id = payload.provider_id
        product.category_id = payload.category_id
        product.season_id = payload.season_id
        product.collection_id = payload.collection_id

        variants = []
        normalized_variants = _normalized_variants(payload, payload.status or ProductStatusEnum.active)
        _validate_variant_payload(normalized_variants)

        for variant_data in normalized_variants:
            variant = ProductVariant(
                product_id=product.id,
                sku=variant_data["sku"],
                price=variant_data["price"],
                size_id=variant_data["size_id"],
                color_id=variant_data["color_id"],
                status=variant_data["status"],
            )
            db.add(variant)
            variants.append(variant)

        if variants:
            product.price = variants[0].price

        db.commit()

        return db.query(Product).options(selectinload(Product.variants)).filter(Product.id == product_id).first()
    except IntegrityError:
        db.rollback()
        raise ValueError("No se pudo actualizar el producto")


def delete_product(db: Session, product_id) -> bool:
    product = db.query(Product).options(selectinload(Product.variants)).filter(Product.id == product_id).first()
    if not product:
        return False

    try:
        variant_ids = [variant.id for variant in product.variants]
        if variant_ids:
            db.query(Inventory).filter(Inventory.variant_id.in_(variant_ids)).delete(synchronize_session=False)
            db.query(ProductVariant).filter(ProductVariant.id.in_(variant_ids)).delete(synchronize_session=False)
        db.delete(product)
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        raise ValueError("No se pudo eliminar el producto")


def _product_to_read(product: Product, variants: list[ProductVariant], branch_quantity_map: dict | None = None):
    variant_reads = []
    total_quantity = 0
    primary = None

    for variant in variants:
        branch_quantity = None
        if branch_quantity_map is not None:
            branch_quantity = branch_quantity_map.get(variant.id, 0)
            total_quantity += branch_quantity
        variant_data = ProductVariantRead.model_validate(
            {
                "id": variant.id,
                "product_id": product.id,
                "sku": variant.sku,
                "price": variant.price,
                "size_id": variant.size_id,
                "color_id": variant.color_id,
                "status": variant.status,
                "branch_quantity": branch_quantity,
            }
        ).model_dump()
        variant_reads.append(variant_data)
        if primary is None:
            primary = variant_data

    if primary is None:
        return None

    return ProductRead.model_validate(
        {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "provider_id": product.provider_id,
            "category_id": product.category_id,
            "season_id": product.season_id,
            "collection_id": product.collection_id,
            "sku": primary["sku"],
            "price": primary["price"],
            "status": primary["status"],
            "size_id": primary["size_id"],
            "color_id": primary["color_id"],
            "branch_quantity": total_quantity if branch_quantity_map is not None else None,
            "variants": variant_reads,
        }
    ).model_dump()


def list_public_products(
    db: Session,
    branch_id=None,
    category_id=None,
    size_id=None,
    color_id=None,
    season_id=None,
    collection_id=None,
    q=None,
):
    query = db.query(Product).options(selectinload(Product.variants))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if season_id:
        query = query.filter(Product.season_id == season_id)
    if collection_id:
        query = query.filter(Product.collection_id == collection_id)
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))

    products = query.order_by(Product.name.asc()).all()
    result = []
    for product in products:
        variants = [variant for variant in product.variants if variant.status == ProductStatusEnum.active]
        if size_id:
            variants = [variant for variant in variants if variant.size_id == size_id]
        if color_id:
            variants = [variant for variant in variants if variant.color_id == color_id]
        if not variants:
            continue

        branch_quantity_map = None
        if branch_id:
            inventories = db.query(Inventory).filter(
                Inventory.variant_id.in_([variant.id for variant in variants]),
                Inventory.branch_id == branch_id,
            ).all()
            branch_quantity_map = {inventory.variant_id: inventory.quantity for inventory in inventories}

        result.append(_product_to_read(product, variants, branch_quantity_map))
    return result


def list_product_variants_for_admin(db: Session, product_id):
    product = db.query(Product).options(selectinload(Product.variants)).filter(Product.id == product_id).first()
    if not product:
        return None
    return product


def list_pending_products(db: Session):
    products = (
        db.query(Product)
        .options(selectinload(Product.variants))
        .order_by(Product.name.asc())
        .all()
    )

    result = []
    for product in products:
        variants = [variant for variant in product.variants if variant.status == ProductStatusEnum.pending]
        if not variants:
            continue
        result.append(_product_to_read(product, variants))

    return result


def get_branch_quantity(db: Session, variant_id, branch_id):
    inv = db.query(Inventory).filter(Inventory.variant_id == variant_id, Inventory.branch_id == branch_id).first()
    return inv.quantity if inv else 0


def create_or_update_inventory(db: Session, variant_id, branch_id, quantity: int):
    inv = db.query(Inventory).filter(Inventory.variant_id == variant_id, Inventory.branch_id == branch_id).first()
    if inv:
        inv.quantity = quantity
    else:
        inv = Inventory(variant_id=variant_id, branch_id=branch_id, quantity=quantity)
        db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv
