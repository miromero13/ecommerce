from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_tenant_id, require_roles
from app.core.database import get_db
from app.schemas.enums import RolEnum
from app.services import loyalty_service as service
from app.services.sales_service import _registered_customer
from app.utils.response import response


router = APIRouter(prefix="/loyalty", tags=["Loyalty"])
CUSTOMER = require_roles(RolEnum.cliente)


@router.get("/balance")
def balance_route(db: Session = Depends(get_db), user: dict = Depends(CUSTOMER)):
    return response(status_code=200, message="Puntos obtenidos exitosamente",
                    data=service.list_balances(db, UUID(user["sub"])))


@router.get("/transactions")
def transactions_route(db: Session = Depends(get_db), user: dict = Depends(CUSTOMER)):
    return response(status_code=200, message="Movimientos de puntos obtenidos exitosamente",
                    data=service.list_transactions(db, UUID(user["sub"])))


@router.get("/customer")
def customer_balance_route(
    email: EmailStr = Query(...),
    db: Session = Depends(get_db),
    tenant_id: UUID | None = Depends(get_current_tenant_id),
    _: dict = Depends(require_roles(RolEnum.cajero)),
):
    """Till: balance of a registered customer in the cashier's company before redeeming."""
    try:
        customer = _registered_customer(db, email)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return response(status_code=200, message="Puntos del cliente obtenidos exitosamente",
                    data={**service.balance_for(db, tenant_id, customer.id), "customer_email": customer.email})
