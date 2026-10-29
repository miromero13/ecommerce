from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_tenant_id, require_roles
from app.core.database import get_db
from app.models.tenant import Tenant
from app.schemas.enums import RolEnum
from app.schemas.payout_schema import BankAccountUpdate, PayoutSummaryRead, SettlementRead, TransferConfirm
from app.services.payout_service import (
    get_summary, list_settlements, mark_settlement_paid, run_daily_settlements, update_bank_account,
)
from app.utils.response import response


router = APIRouter(prefix="/payouts", tags=["Payouts"])
ADMIN = require_roles(RolEnum.administrador)
SUPERADMIN = require_roles(RolEnum.superadministrador)


def _settlements(db: Session, rows):
    names = dict(db.query(Tenant.id, Tenant.name).filter(Tenant.id.in_({row.tenant_id for row in rows})).all())
    return [{**SettlementRead.model_validate(row).model_dump(), "tenant_name": names.get(row.tenant_id)} for row in rows]


@router.get("/summary")
def summary_route(db: Session = Depends(get_db), _: dict = Depends(ADMIN),
                  tenant_id: UUID = Depends(get_current_tenant_id)):
    data = PayoutSummaryRead.model_validate(get_summary(db, tenant_id)).model_dump()
    return response(status_code=200, message="Resumen de cobros en línea obtenido", data=data)


@router.put("/bank-account")
def bank_account_route(payload: BankAccountUpdate, db: Session = Depends(get_db), _: dict = Depends(ADMIN),
                       tenant_id: UUID = Depends(get_current_tenant_id)):
    update_bank_account(db, tenant_id, payload.model_dump())
    return response(status_code=200, message="Cuenta bancaria registrada exitosamente", data=payload.model_dump())


@router.get("/settlements")
def settlements_route(
    db: Session = Depends(get_db),
    payload: dict = Depends(require_roles(RolEnum.administrador, RolEnum.superadministrador)),
    tenant_id: UUID | None = Depends(get_current_tenant_id),
    filter_tenant_id: UUID | None = Query(default=None, alias="tenant_id"),
):
    # A company admin always sees only its own settlements; the superadmin may filter.
    scope = tenant_id if payload["rol"] == RolEnum.administrador.value else filter_tenant_id
    return response(status_code=200, message="Liquidaciones obtenidas", data=_settlements(db, list_settlements(db, scope)))


@router.post("/settlements/run")
def run_settlements_route(db: Session = Depends(get_db), _: dict = Depends(SUPERADMIN)):
    created = run_daily_settlements(db)
    return response(status_code=200, message=f"Se generaron {len(created)} liquidaciones", data=_settlements(db, created))


@router.patch("/settlements/{settlement_id}/paid")
def mark_paid_route(settlement_id: UUID, body: TransferConfirm, db: Session = Depends(get_db),
                    payload: dict = Depends(SUPERADMIN)):
    try:
        settlement = mark_settlement_paid(db, settlement_id, body.transfer_reference, UUID(payload["sub"]))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return response(status_code=200, message="Liquidación marcada como transferida",
                    data=SettlementRead.model_validate(settlement).model_dump())
