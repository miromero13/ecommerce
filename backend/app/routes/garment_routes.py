from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.models.product_variant import ProductVariant
from app.schemas.enums import RolEnum
from app.schemas.garment_schema import CatalogGarmentRequest
from app.services.catalog_garment_service import CatalogGarmentError, generate_catalog_garment
from app.services.subscription_service import TRY_ON_FEATURE, tenant_has_feature
from app.utils.response import response


router = APIRouter(prefix="/catalog", tags=["Catalog garment"])


@router.post("/garment")
async def catalog_garment_route(
    request: CatalogGarmentRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(RolEnum.cliente)),
):
    # The try-on belongs to the plan of the company that sells the garment.
    variant = db.query(ProductVariant).filter(ProductVariant.image_url == request.source_url).first()
    if not variant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La imagen no pertenece a una prenda del catálogo")
    if not tenant_has_feature(db, variant.tenant_id, TRY_ON_FEATURE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta tienda no tiene el vestidor virtual incluido en su plan",
        )
    try:
        data = await generate_catalog_garment(request.source_url)
    except CatalogGarmentError as error:
        return response(status_code=error.status_code, message=error.detail, error=error.detail)
    return response(status_code=status.HTTP_200_OK, message="Prenda preparada exitosamente", data=data)
