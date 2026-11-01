from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_tenant_id, get_current_user, require_roles
from app.core.database import get_db
from app.models.user import User
from app.schemas.enums import RolEnum
from app.schemas.subscription_schema import (
    SubscriptionChangePlan,
    SubscriptionPlanCreate,
    SubscriptionPlanRead,
    SubscriptionPlanUpdate,
    SubscriptionPurchaseSimulated,
    TenantWithSubscriptionCreate,
)
from app.services.email_service import email_service
from app.services.subscription_service import (
    change_tenant_plan,
    create_plan,
    get_tenant_subscription_summary,
    list_plans,
    list_subscription_history,
    provision_tenant_by_superadmin,
    provision_tenant_onboarding,
    update_plan,
)
from app.utils.response import response

router = APIRouter(prefix="/saas", tags=["SaaS Subscriptions"])


# [CU01 - Secuencia: Paso 2.1] TenantManagementPageComponent llama a get_plans_route() de subscription_routes (GET /api/saas/public/plans)
# [CU01 - Secuencia: Paso 2.4] subscription_routes retorna get_plans_route(): 200 Planes de suscripción recuperados exitosamente a TenantManagementPageComponent
# [CU04 - Secuencia: Paso 1.1] PricingTableComponent llama a get_plans_route() de subscription_routes (GET /api/saas/public/plans)
# [CU04 - Secuencia: Paso 1.4] subscription_routes retorna get_plans_route(): 200 Planes de suscripción recuperados exitosamente a PricingTableComponent
# [CU27 - Secuencia: Paso 1.1] OnboardingPageComponent llama a get_plans_route() de subscription_routes (GET /api/saas/public/plans)
# [CU27 - Secuencia: Paso 1.4] subscription_routes retorna get_plans_route(): 200 Planes de suscripción recuperados exitosamente a OnboardingPageComponent
@router.get("/plans")
@router.get("/public/plans")
async def get_plans_route(db: Session = Depends(get_db)):
    plans = list_plans(db, only_active=True)
    serialized = [
        SubscriptionPlanRead.model_validate(p).model_dump() for p in plans
    ]
    return response(
        status_code=status.HTTP_200_OK,
        message="Planes de suscripción recuperados exitosamente",
        data=serialized,
        count_data=len(serialized),
    )


def _plan_data(plan) -> dict:
    return SubscriptionPlanRead.model_validate(plan).model_dump()


# [CU02 - Secuencia: Pasos 1.1, 2.11, 3.7] PlanManagementPageComponent llama a list_all_plans_route() de subscription_routes (GET /api/saas/plans/admin)
# [CU02 - Secuencia: Pasos 1.4, 2.14, 3.10] subscription_routes retorna list_all_plans_route(): 200 Planes de suscripción recuperados exitosamente a PlanManagementPageComponent
@router.get("/plans/admin")
async def list_all_plans_route(
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(RolEnum.superadministrador)),
):
    plans = [_plan_data(plan) for plan in list_plans(db, only_active=False)]
    return response(
        status_code=status.HTTP_200_OK,
        message="Planes de suscripción recuperados exitosamente",
        data=plans,
        count_data=len(plans),
    )


# [CU02 - Secuencia: Paso 2.7] PlanManagementPageComponent llama a create_plan_route(payload) de subscription_routes (POST /api/saas/plans)
# [CU02 - Secuencia: Paso 2.10] subscription_routes retorna create_plan_route(payload): 201 Plan creado exitosamente a PlanManagementPageComponent
@router.post("/plans", status_code=status.HTTP_201_CREATED)
async def create_plan_route(
    payload: SubscriptionPlanCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(RolEnum.superadministrador)),
):
    plan = create_plan(db, payload)
    return response(status_code=status.HTTP_201_CREATED, message="Plan creado exitosamente", data=_plan_data(plan))


# [CU02 - Secuencia: Pasos 2.1, 3.1] PlanManagementPageComponent llama a update_plan_route(plan_id, payload) de subscription_routes (PATCH /api/saas/plans/{plan_id})
# [CU02 - Secuencia: Pasos 2.6, 3.6] subscription_routes retorna update_plan_route(plan_id, payload): 200 Plan actualizado exitosamente a PlanManagementPageComponent
@router.patch("/plans/{plan_id}")
async def update_plan_route(
    plan_id: str,
    payload: SubscriptionPlanUpdate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(RolEnum.superadministrador)),
):
    plan = update_plan(db, plan_id, payload)
    return response(status_code=status.HTTP_200_OK, message="Plan actualizado exitosamente", data=_plan_data(plan))


# [CU27 - Secuencia: Paso 2.1] OnboardingPageComponent llama a purchase_simulated_subscription_route(payload) de subscription_routes (POST /api/saas/subscriptions/purchase-simulated)
# [CU27 - Secuencia: Paso 2.14] subscription_routes retorna purchase_simulated_subscription_route(payload): 201 Suscripción activada con éxito. Te enviamos un correo con los datos de acceso. a OnboardingPageComponent
@router.post("/subscriptions/purchase-simulated", status_code=status.HTTP_201_CREATED)
async def purchase_simulated_subscription_route(
    payload: SubscriptionPurchaseSimulated,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    result = provision_tenant_onboarding(db, payload)
    tenant = result["tenant"]
    admin_user = result["admin_user"]
    plan = result["plan"]
    subscription = result["subscription"]
    raw_password = result["raw_password"]

    # Queue or trigger email delivery
    background_tasks.add_task(
        email_service.send_welcome_credentials_email,
        to_email=admin_user.email,
        admin_name=admin_user.name,
        tenant_name=tenant.name,
        plan_name=plan.name,
        password=raw_password,
    )

    sub_status = subscription.status.value if hasattr(subscription.status, "value") else str(subscription.status)
    return response(
        status_code=status.HTTP_201_CREATED,
        message="Suscripción activada con éxito. Te enviamos un correo con los datos de acceso.",
        data={
            "tenant_id": str(tenant.id),
            "tenant_name": tenant.name,
            "tenant_slug": tenant.slug,
            "admin_email": admin_user.email,
            "plan_name": plan.name,
            "subscription_status": sub_status,
            "is_trial": sub_status == "trialing",
        },
    )


def _target_tenant(current_user: User, tenant_id: Optional[UUID]) -> UUID:
    """The superadmin names the company; everyone else always sees their own."""
    if current_user.rol == RolEnum.superadministrador:
        target = tenant_id or current_user.tenant_id
        if not target:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="El superadministrador debe especificar un tenant_id.")
        return target
    if not current_user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El usuario no pertenece a ninguna empresa.")
    return UUID(str(current_user.tenant_id))


# [CU28 - Secuencia: Pasos 1.7, 2.11] SubscriptionPageComponent llama a get_subscription_history_route(tenant_id) de subscription_routes (GET /api/saas/subscriptions/history)
# [CU28 - Secuencia: Pasos 1.10, 2.14] subscription_routes retorna get_subscription_history_route(tenant_id): 200 Historial de pagos obtenido exitosamente a SubscriptionPageComponent
@router.get("/subscriptions/history")
async def get_subscription_history_route(
    tenant_id: Optional[UUID] = Query(None, description="Solo superadmin"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: dict = Depends(require_roles(RolEnum.administrador, RolEnum.superadministrador)),
):
    return response(
        status_code=status.HTTP_200_OK,
        message="Historial de pagos obtenido exitosamente",
        data=list_subscription_history(db, _target_tenant(current_user, tenant_id)),
    )


# [CU28 - Secuencia: Paso 1.1] SubscriptionPageComponent llama a get_current_subscription_route(tenant_id) de subscription_routes (GET /api/saas/subscriptions/current)
# [CU28 - Secuencia: Paso 1.6] subscription_routes retorna get_current_subscription_route(tenant_id): 200 Suscripción obtenida exitosamente a SubscriptionPageComponent
@router.get("/subscriptions/current")
async def get_current_subscription_route(
    tenant_id: Optional[UUID] = Query(None, description="Solo superadmin"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_tenant_id = _target_tenant(current_user, tenant_id)
    summary = get_tenant_subscription_summary(db, target_tenant_id)
    return response(
        status_code=status.HTTP_200_OK,
        message="Suscripción obtenida exitosamente",
        data=summary,
    )


# [CU28 - Secuencia: Paso 2.1] SubscriptionPageComponent llama a change_plan_route(payload) de subscription_routes (POST /api/saas/subscriptions/change-plan)
# [CU28 - Secuencia: Paso 2.10] subscription_routes retorna change_plan_route(payload): 200 Plan actualizado con éxito. Tu empresa ahora tiene el plan .... a SubscriptionPageComponent
@router.post("/subscriptions/change-plan")
async def change_plan_route(
    payload: SubscriptionChangePlan,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(RolEnum.administrador)),
    current_tenant_id: UUID = Depends(get_current_tenant_id),
):
    summary = change_tenant_plan(db, current_tenant_id, payload)
    return response(
        status_code=status.HTTP_200_OK,
        message=f"Plan actualizado con éxito. Tu empresa ahora tiene el plan {summary['plan']['name']}.",
        data=summary,
    )


# [CU01 - Secuencia: Paso 3.1] TenantManagementPageComponent llama a create_tenant_with_subscription_route(payload) de subscription_routes (POST /api/saas/tenants/with-subscription)
# [CU01 - Secuencia: Paso 3.14] subscription_routes retorna create_tenant_with_subscription_route(payload): 201 Empresa y suscripción creadas exitosamente. Credenciales despachadas por correo. a TenantManagementPageComponent
@router.post("/tenants/with-subscription", status_code=status.HTTP_201_CREATED)
async def create_tenant_with_subscription_route(
    payload: TenantWithSubscriptionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: dict = Depends(require_roles(RolEnum.superadministrador)),
):
    result = provision_tenant_by_superadmin(db, payload)
    tenant = result["tenant"]
    admin_user = result["admin_user"]
    plan = result["plan"]
    subscription = result["subscription"]
    raw_password = result["raw_password"]

    background_tasks.add_task(
        email_service.send_welcome_credentials_email,
        to_email=admin_user.email,
        admin_name=admin_user.name,
        tenant_name=tenant.name,
        plan_name=plan.name,
        password=raw_password,
    )

    sub_status = subscription.status.value if hasattr(subscription.status, "value") else str(subscription.status)
    return response(
        status_code=status.HTTP_201_CREATED,
        message="Empresa y suscripción creadas exitosamente. Credenciales despachadas por correo.",
        data={
            "tenant_id": str(tenant.id),
            "tenant_name": tenant.name,
            "tenant_slug": tenant.slug,
            "admin_email": admin_user.email,
            "plan_name": plan.name,
            "subscription_status": sub_status,
            "is_trial": sub_status == "trialing",
        },
    )
