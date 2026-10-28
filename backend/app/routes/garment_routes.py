from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.tenant import Tenant
from app.schemas.catalog_enums import ProductStatusEnum
from app.schemas.enums import RolEnum, TenantStatusEnum
from app.schemas.garment_schema import CatalogGarmentRequest
from app.services.catalog_garment_service import CatalogGarmentError, generate_catalog_garment
from app.services.subscription_service import TRY_ON_FEATURE, tenant_has_feature
from app.services.virtual_try_on_service import MAX_PHOTO_BYTES, generate_try_on
from app.utils.response import response


router = APIRouter(prefix="/catalog", tags=["Catalog garment"])

NOT_IN_PLAN = "Esta tienda no tiene el vestidor virtual incluido en su plan"


def _require_try_on(db: Session, tenant_id) -> None:
    # The try-on belongs to the plan of the company that sells the garment.
    if not tenant_has_feature(db, tenant_id, TRY_ON_FEATURE):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=NOT_IN_PLAN)


@router.post("/garment")
async def catalog_garment_route(
    request: CatalogGarmentRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(RolEnum.cliente)),
):
    variant = db.query(ProductVariant).filter(or_(ProductVariant.image_url == request.source_url,
                                                  ProductVariant.try_on_image_url == request.source_url)).first()
    if not variant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La imagen no pertenece a una prenda del catálogo")
    _require_try_on(db, variant.tenant_id)
    try:
        data = await generate_catalog_garment(request.source_url)
    except CatalogGarmentError as error:
        return response(status_code=error.status_code, message=error.detail, error=error.detail)
    return response(status_code=status.HTTP_200_OK, message="Prenda preparada exitosamente", data=data)


@router.post("/try-on")
async def virtual_try_on_route(
    variant_id: UUID = Form(...),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(RolEnum.cliente)),
):
    """Put a catalog garment on the customer's photo (CU5, Hugging Face IDM-VTON)."""
    row = (
        db.query(ProductVariant, Product, Tenant)
        .join(Product, Product.id == ProductVariant.product_id)
        .join(Tenant, Tenant.id == ProductVariant.tenant_id)
        .filter(ProductVariant.id == variant_id, ProductVariant.status == ProductStatusEnum.active,
                Product.tenant_id == ProductVariant.tenant_id)
        .first()
    )
    # Suspended companies are hidden from the public catalog, so their garments are "not found".
    if not row or row.Tenant.status == TenantStatusEnum.suspended:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prenda no encontrada")
    variant, product, _tenant = row
    _require_try_on(db, variant.tenant_id)
    # The transparent cut-out fits the AI best; the catalog photo is the fallback.
    garment_url = variant.try_on_image_url or variant.image_url
    if not garment_url:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="La prenda no tiene una imagen para el vestidor")

    image = await photo.read(MAX_PHOTO_BYTES + 1)
    try:
        data = await generate_try_on(image, garment_url, product.name)
    except CatalogGarmentError as error:
        return response(status_code=error.status_code, message=error.detail, error=error.detail)
    return response(status_code=status.HTTP_200_OK, message="Prueba virtual generada exitosamente", data=data)
