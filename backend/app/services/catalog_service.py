from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_

from app.models.category import Category
from app.models.color import Color
from app.models.collection import Collection
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.season import Season
from app.models.size import Size
from app.schemas.catalog_schema import NameCreate, ColorCreate, CollectionCreate, ProductCreate, ProductStatusUpdate
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


def create_product(db: Session, payload: ProductCreate, provider_id=None, status: ProductStatusEnum = ProductStatusEnum.active):
    product = Product(
        sku=payload.sku,
        name=payload.name,
        description=payload.description,
        price=payload.price,
        provider_id=provider_id,
        category_id=payload.category_id,
        size_id=payload.size_id,
        color_id=payload.color_id,
        season_id=payload.season_id,
        collection_id=payload.collection_id,
        status=status,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product_status(db: Session, product_id, update_data: ProductStatusUpdate):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
      return None
    product.status = update_data.status
    db.commit()
    db.refresh(product)
    return product


def list_public_products(db: Session, branch_id=None, category_id=None, size_id=None, color_id=None, season_id=None, collection_id=None, q=None):
    query = db.query(Product).filter(Product.status == ProductStatusEnum.active)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if size_id:
        query = query.filter(Product.size_id == size_id)
    if color_id:
        query = query.filter(Product.color_id == color_id)
    if season_id:
        query = query.filter(Product.season_id == season_id)
    if collection_id:
        query = query.filter(Product.collection_id == collection_id)
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))

    products = query.order_by(Product.name.asc()).all()
    result = []
    for product in products:
        branch_quantity = None
        if branch_id:
            inv = db.query(Inventory).filter(Inventory.product_id == product.id, Inventory.branch_id == branch_id).first()
            branch_quantity = inv.quantity if inv else 0
        result.append((product, branch_quantity))
    return result


def get_branch_quantity(db: Session, product_id, branch_id):
    inv = db.query(Inventory).filter(Inventory.product_id == product_id, Inventory.branch_id == branch_id).first()
    return inv.quantity if inv else 0


def create_or_update_inventory(db: Session, product_id, branch_id, quantity: int):
    inv = db.query(Inventory).filter(Inventory.product_id == product_id, Inventory.branch_id == branch_id).first()
    if inv:
        inv.quantity = quantity
    else:
        inv = Inventory(product_id=product_id, branch_id=branch_id, quantity=quantity)
        db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv
