from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.auth.dependencies import get_current_user, require_roles
from app.core.database import get_db
from app.models.user import User
from app.schemas.catalog_enums import ProductStatusEnum
from app.schemas.catalog_schema import (
    NameCreate,
    ColorCreate,
    CollectionCreate,
    ProductCreate,
    ProductRead,
    ProductStatusUpdate,
)
from app.schemas.enums import RolEnum
from app.models.category import Category
from app.models.size import Size
from app.models.color import Color
from app.models.season import Season
from app.models.collection import Collection
from app.models.product import Product
from app.models.provider import Provider
from app.services.catalog_service import (
    create_name_item,
    create_color,
    create_collection,
    create_product,
    update_product_status,
    list_public_products,
    create_or_update_inventory,
    get_branch_quantity,
)
from app.utils.response import response


router = APIRouter(prefix="/catalog", tags=["Catalog"])


def _rows_to_data(rows):
    return [ProductRead.model_validate({
        "id": product.id,
        "sku": product.sku,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "status": product.status,
        "category_id": product.category_id,
        "size_id": product.size_id,
        "color_id": product.color_id,
        "season_id": product.season_id,
        "collection_id": product.collection_id,
        "branch_quantity": branch_quantity,
    }).model_dump() for product, branch_quantity in rows]


@router.get("/categories")
async def list_categories(db: Session = Depends(get_db)):
    items = db.query(Category).order_by(Category.name.asc()).all()
    return response(status_code=200, message="Categorias obtenidas exitosamente", data=[{"id": i.id, "name": i.name} for i in items])


@router.post("/categories", status_code=status.HTTP_201_CREATED)
async def create_category(payload: NameCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    item = create_name_item(db, Category, payload)
    return response(status_code=201, message="Categoria creada exitosamente", data={"id": item.id, "name": item.name})


@router.get("/sizes")
async def list_sizes(db: Session = Depends(get_db)):
    items = db.query(Size).order_by(Size.name.asc()).all()
    return response(status_code=200, message="Tallas obtenidas exitosamente", data=[{"id": i.id, "name": i.name} for i in items])


@router.post("/sizes", status_code=status.HTTP_201_CREATED)
async def create_size(payload: NameCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    item = create_name_item(db, Size, payload)
    return response(status_code=201, message="Talla creada exitosamente", data={"id": item.id, "name": item.name})


@router.get("/colors")
async def list_colors(db: Session = Depends(get_db)):
    items = db.query(Color).order_by(Color.name.asc()).all()
    return response(status_code=200, message="Colores obtenidos exitosamente", data=[{"id": i.id, "name": i.name, "hex_code": i.hex_code} for i in items])


@router.post("/colors", status_code=status.HTTP_201_CREATED)
async def create_color_route(payload: ColorCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    item = create_color(db, payload)
    return response(status_code=201, message="Color creado exitosamente", data={"id": item.id, "name": item.name, "hex_code": item.hex_code})


@router.get("/seasons")
async def list_seasons(db: Session = Depends(get_db)):
    items = db.query(Season).order_by(Season.name.asc()).all()
    return response(status_code=200, message="Temporadas obtenidas exitosamente", data=[{"id": i.id, "name": i.name} for i in items])


@router.post("/seasons", status_code=status.HTTP_201_CREATED)
async def create_season(payload: NameCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    item = create_name_item(db, Season, payload)
    return response(status_code=201, message="Temporada creada exitosamente", data={"id": item.id, "name": item.name})


@router.get("/collections")
async def list_collections(db: Session = Depends(get_db)):
    items = db.query(Collection).order_by(Collection.name.asc()).all()
    return response(status_code=200, message="Colecciones obtenidas exitosamente", data=[{"id": i.id, "name": i.name, "season_id": i.season_id} for i in items])


@router.post("/collections", status_code=status.HTTP_201_CREATED)
async def create_collection_route(payload: CollectionCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    item = create_collection(db, payload)
    return response(status_code=201, message="Coleccion creada exitosamente", data={"id": item.id, "name": item.name, "season_id": item.season_id})


@router.get("/products")
async def list_products(
    db: Session = Depends(get_db),
    q: str | None = None,
    branch_id: UUID | None = None,
    category_id: UUID | None = None,
    size_id: UUID | None = None,
    color_id: UUID | None = None,
    season_id: UUID | None = None,
    collection_id: UUID | None = None,
):
    rows = list_public_products(db, branch_id, category_id, size_id, color_id, season_id, collection_id, q)
    return response(status_code=200, message="Productos obtenidos exitosamente", data=_rows_to_data(rows))


@router.get("/products/pending")
async def list_pending_products(db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    products = db.query(Product).filter(Product.status == ProductStatusEnum.pending).order_by(Product.name.asc()).all()
    return response(status_code=200, message="Productos pendientes obtenidos exitosamente", data=[ProductRead.model_validate(product).model_dump() for product in products])


@router.post("/products", status_code=status.HTTP_201_CREATED)
async def create_product_route(payload: ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    product = create_product(db, payload, status=ProductStatusEnum.active)
    return response(status_code=201, message="Producto creado exitosamente", data=ProductRead.model_validate(product).model_dump())


@router.post("/products/provider-submission", status_code=status.HTTP_201_CREATED)
async def submit_product_route(payload: ProductCreate, db: Session = Depends(get_db), current_payload: dict = Depends(require_roles(RolEnum.proveedor, RolEnum.administrador))):
    provider = db.query(Provider).filter(Provider.user_id == UUID(current_payload["sub"])).first()
    provider_id = provider.id if provider else None
    product = create_product(db, payload, provider_id=provider_id, status=ProductStatusEnum.pending)
    return response(status_code=201, message="Producto enviado exitosamente", data=ProductRead.model_validate(product).model_dump())


@router.patch("/products/{product_id}/status")
async def update_product_status_route(product_id: UUID, payload: ProductStatusUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    product = update_product_status(db, product_id, payload)
    if not product:
        raise HTTPException(status_code=404, detail=f"Producto con id {product_id} no encontrado")
    return response(status_code=200, message="Producto actualizado exitosamente", data=ProductRead.model_validate(product).model_dump())


@router.get("/availability")
async def get_availability(product_id: UUID, branch_id: UUID, db: Session = Depends(get_db)):
    quantity = get_branch_quantity(db, product_id, branch_id)
    return response(status_code=200, message="Disponibilidad obtenida exitosamente", data={"product_id": product_id, "branch_id": branch_id, "quantity": quantity})


@router.put("/inventory")
async def set_inventory(product_id: UUID, branch_id: UUID, quantity: int, db: Session = Depends(get_db), current_user: User = Depends(require_roles(RolEnum.administrador))):
    inv = create_or_update_inventory(db, product_id, branch_id, quantity)
    return response(status_code=200, message="Inventario actualizado exitosamente", data={"product_id": inv.product_id, "branch_id": inv.branch_id, "quantity": inv.quantity})
