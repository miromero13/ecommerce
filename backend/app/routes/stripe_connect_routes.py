from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_tenant_id, require_roles
from app.core.database import get_db
from app.schemas.enums import RolEnum
from app.schemas.stripe_connect_schema import OnboardingLinkRequest
from app.services.stripe_connect_service import create_onboarding_link, get_status
from app.utils.response import response


router = APIRouter(prefix="/saas/stripe-connect", tags=["Stripe Connect"])
ADMIN = require_roles(RolEnum.administrador)


@router.post("/onboarding-link")
def onboarding_link_route(payload: OnboardingLinkRequest, db: Session = Depends(get_db),
                          _: dict = Depends(ADMIN), tenant_id: UUID = Depends(get_current_tenant_id)):
    try:
        url = create_onboarding_link(db, tenant_id, str(payload.return_url))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=200, message="Enlace de conexión con Stripe generado", data={"url": url})


@router.get("/status")
def status_route(db: Session = Depends(get_db), _: dict = Depends(ADMIN),
                 tenant_id: UUID = Depends(get_current_tenant_id)):
    try:
        data = get_status(db, tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=200, message="Estado de pagos en línea obtenido", data=data)
