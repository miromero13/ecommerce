from fastapi import APIRouter, Depends, status

from app.auth.dependencies import require_roles
from app.schemas.enums import RolEnum
from app.schemas.garment_schema import CatalogGarmentRequest
from app.services.catalog_garment_service import CatalogGarmentError, generate_catalog_garment
from app.utils.response import response


router = APIRouter(prefix="/catalog", tags=["Catalog garment"])


@router.post("/garment")
async def catalog_garment_route(
    request: CatalogGarmentRequest,
    _: dict = Depends(require_roles(RolEnum.cliente)),
):
    try:
        data = await generate_catalog_garment(request.source_url)
    except CatalogGarmentError as error:
        return response(status_code=error.status_code, message=error.detail, error=error.detail)
    return response(status_code=status.HTTP_200_OK, message="Prenda preparada exitosamente", data=data)
