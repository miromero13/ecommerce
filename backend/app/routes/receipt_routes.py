from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services import receipt_service as service
from app.utils.response import response


router = APIRouter(prefix="/receipts", tags=["Receipts"])
Kind = Literal["order", "sale", "reservation_deposit", "subscription"]


def _find(db: Session, user: User, kind: str, source_id: UUID):
    receipt = service.find_receipt(db, user, kind, source_id)
    if receipt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comprobante no encontrado")
    return receipt


@router.get("")
def list_route(
    kind: Kind | None = Query(default=None),
    tenant_id: UUID | None = Query(default=None, description="Superadmin: comprobantes de plan de una empresa"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Customers see theirs; company staff see their company's (managers and cashiers, their branch)."""
    return response(status_code=200, message="Comprobantes obtenidos exitosamente",
                    data=service.list_receipts(db, user, kind, tenant_id))


@router.get("/{kind}/{source_id}/pdf")
def pdf_route(kind: Kind, source_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    receipt = _find(db, user, kind, source_id)
    number = service.display_number(receipt)
    return Response(content=service.render_pdf(db, receipt), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="comprobante-{number}.pdf"'})


@router.post("/{kind}/{source_id}/resend")
def resend_route(kind: Kind, source_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    receipt = _find(db, user, kind, source_id)
    try:
        service.request_resend(db, receipt)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=200, message=f"Enviaremos el comprobante a {receipt.customer_email}",
                    data=service.serialize(db, receipt))
