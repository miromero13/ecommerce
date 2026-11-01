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
    DiscardTransfersRequest,
    ExpertRuleRead,
    ExpertRuleUpdate,
)
from app.services.expert_replenishment_service import (
    apply_transfers,
    discard_transfers,
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


# [CU09 - Secuencia: Paso 3.1] AdminExpertReplenishmentPageComponent llama a evaluate_replenishment() de expert_replenishment_routes (POST /api/inventory/expert-replenishment/evaluate)
# [CU09 - Secuencia: Paso 3.14] expert_replenishment_routes retorna evaluate_replenishment(): 200 Evaluación del sistema experto finalizada a AdminExpertReplenishmentPageComponent
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


# [CU09 - Secuencia: Paso 4.1] AdminExpertReplenishmentPageComponent llama a apply_replenishment_transfers(payload) de expert_replenishment_routes (POST /api/inventory/expert-replenishment/apply-transfers)
# [CU09 - Secuencia: Paso 4.8] expert_replenishment_routes retorna apply_replenishment_transfers(payload): 200 Órdenes de traspaso automático aplicadas al inventario a AdminExpertReplenishmentPageComponent
# [CU09 - Secuencia: Paso 6.1] NotificationPageComponent llama a apply_replenishment_transfers(payload) de expert_replenishment_routes (POST /api/inventory/expert-replenishment/apply-transfers)
# [CU09 - Secuencia: Paso 6.8] expert_replenishment_routes retorna apply_replenishment_transfers(payload): 200 Órdenes de traspaso automático aplicadas al inventario a NotificationPageComponent
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


# [CU09 - Secuencia: Paso 7.1] NotificationPageComponent llama a discard_replenishment_transfers(payload) de expert_replenishment_routes (POST /api/inventory/expert-replenishment/discard-transfers)
# [CU09 - Secuencia: Paso 7.4] expert_replenishment_routes retorna discard_replenishment_transfers(payload): 200 Sugerencias de traspaso descartadas a NotificationPageComponent
@router.post(
    "/discard-transfers",
    dependencies=[Depends(require_roles(RolEnum.administrador)), Depends(require_permission("replenishment:manage"))],
)
def discard_replenishment_transfers(
    payload: DiscardTransfersRequest,
    db: Session = Depends(get_db),
    tenant_id: UUID = Depends(get_current_tenant_id),
):
    discarded_count = discard_transfers(
        db=db,
        tenant_id=tenant_id,
        transfer_ids=payload.transfer_ids,
    )
    return response(
        status.HTTP_200_OK,
        message="Sugerencias de traspaso descartadas",
        data={"discarded_count": discarded_count},
    )


# [CU09 - Secuencia: Paso 1.1] AdminExpertReplenishmentPageComponent llama a get_rules() de expert_replenishment_routes (GET /api/inventory/expert-replenishment/rules)
# [CU09 - Secuencia: Paso 1.4] expert_replenishment_routes retorna get_rules(): 200 Reglas de reabastecimiento obtenidas a AdminExpertReplenishmentPageComponent
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


# [CU09 - Secuencia: Paso 5.1] AdminExpertReplenishmentPageComponent llama a update_replenishment_rules(payload) de expert_replenishment_routes (PUT /api/inventory/expert-replenishment/rules)
# [CU09 - Secuencia: Paso 5.6] expert_replenishment_routes retorna update_replenishment_rules(payload): 200 Reglas de reabastecimiento actualizadas a AdminExpertReplenishmentPageComponent
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


# [CU09 - Secuencia: Pasos 2.1, 4.9] AdminExpertReplenishmentPageComponent llama a get_suggestions(status_filter) de expert_replenishment_routes (GET /api/inventory/expert-replenishment/suggestions)
# [CU09 - Secuencia: Pasos 2.4, 4.12] expert_replenishment_routes retorna get_suggestions(status_filter): 200 Sugerencias de reabastecimiento obtenidas a AdminExpertReplenishmentPageComponent
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
