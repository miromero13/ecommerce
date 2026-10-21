from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.core.database import get_db
from app.models.user import User
from app.schemas.enums import RolEnum
from app.schemas.subscription_schema import (
    SubscriptionPlanRead,
    SubscriptionPurchaseSimulated,
    TenantWithSubscriptionCreate,
)
from app.services.email_service import email_service
from app.services.subscription_service import (
    get_tenant_subscription_summary,
    list_plans,
    provision_tenant_by_superadmin,
    provision_tenant_onboarding,
)
from app.utils.response import response

router = APIRouter(prefix="/saas", tags=["SaaS Subscriptions"])


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

    return response(
        status_code=status.HTTP_201_CREATED,
        message="Suscripción activada con éxito. Te enviamos un correo con los datos de acceso.",
        data={
            "tenant_id": str(tenant.id),
            "tenant_name": tenant.name,
            "tenant_slug": tenant.slug,
            "admin_email": admin_user.email,
            "plan_name": plan.name,
            "subscription_status": "active",
        },
    )


@router.get("/subscriptions/current")
async def get_current_subscription_route(
    tenant_id: Optional[UUID] = Query(None, description="Solo superadmin"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_rol = current_user.rol
    user_tenant_id = current_user.tenant_id

    if user_rol == RolEnum.superadministrador:
        target_tenant_id = tenant_id or user_tenant_id
        if not target_tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El superadministrador debe especificar un tenant_id.",
            )
    else:
        if not user_tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El usuario no pertenece a ninguna empresa.",
            )
        target_tenant_id = UUID(str(user_tenant_id))

    summary = get_tenant_subscription_summary(db, target_tenant_id)
    return response(
        status_code=status.HTTP_200_OK,
        message="Suscripción obtenida exitosamente",
        data=summary,
    )


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
    raw_password = result["raw_password"]

    background_tasks.add_task(
        email_service.send_welcome_credentials_email,
        to_email=admin_user.email,
        admin_name=admin_user.name,
        tenant_name=tenant.name,
        plan_name=plan.name,
        password=raw_password,
    )

    return response(
        status_code=status.HTTP_201_CREATED,
        message="Empresa y suscripción creadas exitosamente. Credenciales despachadas por correo.",
        data={
            "tenant_id": str(tenant.id),
            "tenant_name": tenant.name,
            "tenant_slug": tenant.slug,
            "admin_email": admin_user.email,
            "plan_name": plan.name,
            "subscription_status": "active",
        },
    )
