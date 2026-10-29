from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import (
    require_roles,
    get_current_tenant_id,
    get_current_user,
    require_permission,
)
from app.core.database import get_db
from app.schemas.enums import RolEnum
from app.models.user import User
from app.schemas.expert_replenishment_schema import (
    ApplyTransfersRequest,
    ExpertRuleRead,
    ExpertRuleUpdate,
)
from app.services.expert_replenishment_service import (
    apply_transfers,
    evaluate,
    get_or_create_rules,
    list_suggestions,
    update_rules,
)
from app.utils.response import response

router = APIRouter(
    prefix="/inventory/expert-replenishment",
    tags=["Expert Replenishment"],
)


@router.post(
    "/evaluate",
    # Compares and moves stock across ALL branches: only the company administrator (rule: a manager or a
    # supplier never sees other branches), on top of the permission.
    dependencies=[Depends(require_roles(RolEnum.administrador)), Depends(require_permission("replenishment:manage"))],
)
def evaluate_replenishment(
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    suggestions = evaluate(db, tenant_id)
    return response(
        status.HTTP_200_OK,
        message="Evaluación del sistema experto finalizada",
        data=[s.model_dump() for s in suggestions],
    )


@router.post(
    "/apply-transfers",
    # Compares and moves stock across ALL branches: only the company administrator (rule: a manager or a
    # supplier never sees other branches), on top of the permission.
    dependencies=[Depends(require_roles(RolEnum.administrador)), Depends(require_permission("replenishment:manage"))],
)
def apply_replenishment_transfers(
    payload: ApplyTransfersRequest,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
    current_user: User = Depends(get_current_user),
):
    applied_count = apply_transfers(
        db=db,
        tenant_id=tenant_id,
        transfer_ids=payload.transfer_ids,
        user_id=current_user.id,
    )
    return response(
        status.HTTP_200_OK,
        message="Órdenes de traspaso automático aplicadas al inventario",
        data={"applied_count": applied_count},
    )


@router.get(
    "/rules",
    # Compares and moves stock across ALL branches: only the company administrator (rule: a manager or a
    # supplier never sees other branches), on top of the permission.
    dependencies=[Depends(require_roles(RolEnum.administrador)), Depends(require_permission("replenishment:manage"))],
)
def get_rules(
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    rule = get_or_create_rules(db, tenant_id)
    return response(
        status.HTTP_200_OK,
        message="Reglas de reabastecimiento obtenidas",
        data=ExpertRuleRead.model_validate(rule).model_dump(),
    )


@router.put(
    "/rules",
    # Compares and moves stock across ALL branches: only the company administrator (rule: a manager or a
    # supplier never sees other branches), on top of the permission.
    dependencies=[Depends(require_roles(RolEnum.administrador)), Depends(require_permission("replenishment:manage"))],
)
def update_replenishment_rules(
    payload: ExpertRuleUpdate,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    rule = update_rules(db, tenant_id, payload)
    return response(
        status.HTTP_200_OK,
        message="Reglas de reabastecimiento actualizadas",
        data=ExpertRuleRead.model_validate(rule).model_dump(),
    )


@router.get(
    "/suggestions",
    # Compares and moves stock across ALL branches: only the company administrator (rule: a manager or a
    # supplier never sees other branches), on top of the permission.
    dependencies=[Depends(require_roles(RolEnum.administrador)), Depends(require_permission("replenishment:manage"))],
)
def get_suggestions(
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    suggestions = list_suggestions(db, tenant_id, status=status_filter)
    return response(
        status.HTTP_200_OK,
        message="Sugerencias de reabastecimiento obtenidas",
        data=[s.model_dump() for s in suggestions],
    )
