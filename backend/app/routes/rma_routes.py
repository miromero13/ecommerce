"""CU21 & CU24: Endpoints for RMA customer requests, manager reviews, and PDF slip downloads."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_payload, get_current_tenant_id, get_current_user, require_roles
from app.core.database import get_db
from app.models.rma import RmaRequest
from app.models.user import User
from app.schemas.enums import RolEnum
from app.schemas.rma_schema import RmaItemReview, RmaRequestCreate
from app.services.rma_pdf_service import generate_rma_pdf
from app.services.rma_service import (
    create_rma_request,
    get_rma_request,
    list_eligible_orders,
    list_rma_requests,
    review_rma_item,
    settle_monthly_wallets,
)
from app.utils.response import response

router = APIRouter(prefix="/rma", tags=["RMA - Cambios y Devoluciones"])


# [CU21 - Secuencia: Paso 1.1] RmaHistoryPageComponent llama a get_eligible_orders_endpoint() de rma_routes (GET /api/rma/eligible-orders)
# [CU21 - Secuencia: Paso 1.4] rma_routes retorna get_eligible_orders_endpoint(): 200 Órdenes elegibles para cambio o devolución obtenidas a RmaHistoryPageComponent
@router.get("/eligible-orders")
async def get_eligible_orders_endpoint(
    db: Session = Depends(get_db),
    tenant_id: UUID | None = Depends(get_current_tenant_id),
    current_user: User = Depends(get_current_user),
):
    """List orders of the current customer delivered within the last 30 days, eligible for RMA."""
    orders = list_eligible_orders(db, current_user, tenant_id=tenant_id)
    return response(
        status_code=200,
        message="Órdenes elegibles para cambio o devolución obtenidas",
        data=[o.model_dump() for o in orders],
    )


# [CU21 - Secuencia: Paso 2.1] RmaHistoryPageComponent llama a create_rma_request_endpoint(payload) de rma_routes (POST /api/rma/requests)
# [CU21 - Secuencia: Paso 2.8] rma_routes retorna create_rma_request_endpoint(payload): 201 Solicitud de cambio/devolución registrada exitosamente a RmaHistoryPageComponent
@router.post("/requests", status_code=status.HTTP_201_CREATED)
async def create_rma_request_endpoint(
    payload: RmaRequestCreate,
    db: Session = Depends(get_db),
    tenant_id: UUID | None = Depends(get_current_tenant_id),
    current_user: User = Depends(get_current_user),
):
    """Register a new multiline RMA request from a customer."""
    rma = create_rma_request(db, current_user, payload, tenant_id=tenant_id)
    return response(
        status_code=201,
        message="Solicitud de cambio/devolución registrada exitosamente",
        data=rma.model_dump(),
    )


# [CU21 - Secuencia: Paso 2.9] RmaHistoryPageComponent llama a list_rma_requests_endpoint(status_filter) de rma_routes (GET /api/rma/requests)
# [CU21 - Secuencia: Paso 2.14] rma_routes retorna list_rma_requests_endpoint(status_filter): 200 Solicitudes de devolución obtenidas a RmaHistoryPageComponent
# [CU21 - Secuencia: Pasos 3.1, 4.15, 5.9] RmaReviewPageComponent llama a list_rma_requests_endpoint(status_filter) de rma_routes (GET /api/rma/requests)
# [CU21 - Secuencia: Pasos 3.6, 4.20, 5.14] rma_routes retorna list_rma_requests_endpoint(status_filter): 200 Solicitudes de devolución obtenidas a RmaReviewPageComponent
@router.get("/requests")
async def list_rma_requests_endpoint(
    status_filter: str | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    tenant_id: UUID | None = Depends(get_current_tenant_id),
    current_user: User = Depends(get_current_user),
):
    """List RMA requests (filtered by user role: client sees own, staff sees tenant's)."""
    rmas = list_rma_requests(db, current_user, tenant_id=tenant_id, status_filter=status_filter)
    return response(
        status_code=200,
        message="Solicitudes de devolución obtenidas",
        data=[r.model_dump() for rmas_list in [rmas] for r in rmas_list],
    )


@router.get("/requests/{rma_id}")
async def get_rma_request_endpoint(
    rma_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID | None = Depends(get_current_tenant_id),
    current_user: User = Depends(get_current_user),
):
    """Get complete detail of an RMA request and its items."""
    rma = get_rma_request(db, rma_id, current_user, tenant_id=tenant_id)
    return response(
        status_code=200,
        message="Detalle de solicitud de devolución obtenido",
        data=rma.model_dump(),
    )


# [CU21 - Secuencia: Paso 2.15] RmaHistoryPageComponent llama a download_rma_pdf_endpoint(rma_id) de rma_routes (GET /api/rma/requests/{rma_id}/pdf)
# [CU21 - Secuencia: Paso 2.20] rma_routes retorna download_rma_pdf_endpoint(rma_id): Response a RmaHistoryPageComponent
@router.get("/requests/{rma_id}/pdf")
async def download_rma_pdf_endpoint(
    rma_id: UUID,
    db: Session = Depends(get_db),
    tenant_id: UUID | None = Depends(get_current_tenant_id),
    current_user: User = Depends(get_current_user),
):
    """Download the official RMA slip in PDF format."""
    query = db.query(RmaRequest).filter(RmaRequest.id == rma_id)
    if tenant_id is not None:
        query = query.filter(RmaRequest.tenant_id == tenant_id)
    if current_user.rol == RolEnum.cliente:
        query = query.filter(RmaRequest.user_id == current_user.id)

    rma = query.first()
    if not rma:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Solicitud de devolución no encontrada")

    pdf_bytes = generate_rma_pdf(db, rma)
    filename = f"Ficha_{rma.rma_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


# [CU21 - Secuencia: Paso 4.1] RmaReviewPageComponent llama a review_rma_item_endpoint(rma_id, rma_item_id, payload) de rma_routes (PATCH /api/rma/requests/{rma_id}/items/{rma_item_id}/review)
# [CU21 - Secuencia: Paso 4.14] rma_routes retorna review_rma_item_endpoint(rma_id, rma_item_id, payload): 200 Ítem de RMA dictaminado exitosamente a RmaReviewPageComponent
# [CU24 - Secuencia: Paso 1.1] RmaReviewPageComponent llama a review_rma_item_endpoint(rma_id, rma_item_id, payload) de rma_routes (PATCH /api/rma/requests/{rma_id}/items/{rma_item_id}/review)
# [CU24 - Secuencia: Paso 1.14] rma_routes retorna review_rma_item_endpoint(rma_id, rma_item_id, payload): 200 Ítem de RMA dictaminado exitosamente a RmaReviewPageComponent
@router.patch("/requests/{rma_id}/items/{rma_item_id}/review")
async def review_rma_item_endpoint(
    rma_id: UUID,
    rma_item_id: UUID,
    payload: RmaItemReview,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    current_user: User = Depends(get_current_user),
    _role_check: dict = Depends(require_roles(RolEnum.administrador, RolEnum.encargado)),
):
    """Physical inspection and granular review of one RMA item by store manager/admin."""
    updated_rma = review_rma_item(
        db=db,
        rma_id=rma_id,
        item_id=rma_item_id,
        payload=payload,
        reviewer=current_user,
        tenant_id=tenant_id,
    )
    return response(
        status_code=200,
        message="Ítem de RMA dictaminado exitosamente",
        data=updated_rma.model_dump(),
    )


# [CU21 - Secuencia: Paso 5.1] RmaReviewPageComponent llama a settle_monthly_wallets_endpoint() de rma_routes (POST /api/rma/settle-monthly-wallets)
# [CU21 - Secuencia: Paso 5.8] rma_routes retorna settle_monthly_wallets_endpoint(): 200 Liquidación mensual de billeteras procesada exitosamente a RmaReviewPageComponent
@router.post("/settle-monthly-wallets")
async def settle_monthly_wallets_endpoint(
    db: Session = Depends(get_db),
    _role_check: dict = Depends(require_roles(RolEnum.administrador, RolEnum.superadministrador)),
):
    """Trigger month-end wallet crediting for pending approved refunds."""
    result = settle_monthly_wallets(db)
    return response(
        status_code=200,
        message="Liquidación mensual de billeteras procesada exitosamente",
        data=result,
    )
