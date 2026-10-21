from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.hash import hash_password
from app.models.branch import Branch
from app.models.product import Product
from app.models.subscription_plan import SubscriptionPlan
from app.models.tenant import Tenant
from app.models.tenant_subscription import TenantSubscription
from app.models.user import User
from app.schemas.enums import (
    BillingCycleEnum,
    GenderEnum,
    RolEnum,
    SubscriptionPaymentMethodEnum,
    SubscriptionStatusEnum,
    TenantStatusEnum,
)
from app.schemas.subscription_schema import (
    SubscriptionPurchaseSimulated,
    TenantWithSubscriptionCreate,
)
from app.utils.password_generator import generate_random_password


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")



def list_plans(db: Session, only_active: bool = True) -> list[SubscriptionPlan]:
    query = select(SubscriptionPlan)
    if only_active:
        query = query.where(SubscriptionPlan.is_active.is_(True))
    query = query.order_by(SubscriptionPlan.price_monthly.asc())
    return list(db.execute(query).scalars().all())


def get_plan_by_id(db: Session, plan_id: str) -> SubscriptionPlan | None:
    return db.execute(
        select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
    ).scalars().first()


def get_active_subscription(db: Session, tenant_id: UUID) -> TenantSubscription | None:
    return db.execute(
        select(TenantSubscription)
        .where(
            TenantSubscription.tenant_id == tenant_id,
            TenantSubscription.status == SubscriptionStatusEnum.active,
        )
        .order_by(TenantSubscription.created_at.desc())
    ).scalars().first()


def check_tenant_branch_quota(db: Session, tenant_id: UUID) -> None:
    """
    Validates if creating another branch exceeds the plan quota.
    Raises HTTPException 403 if quota is reached.
    """
    subscription = get_active_subscription(db, tenant_id)
    if not subscription or not subscription.plan:
        return

    current_branches_count = db.execute(
        select(func.count(Branch.id)).where(Branch.tenant_id == tenant_id)
    ).scalar_one()

    if current_branches_count >= subscription.plan.max_branches:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Límite de sucursales alcanzado para el plan actual. Actualizá tu suscripción.",
        )


def check_tenant_garment_quota(db: Session, tenant_id: UUID) -> None:
    """
    Validates if creating another product exceeds the plan quota.
    Raises HTTPException 403 if quota is reached.
    """
    subscription = get_active_subscription(db, tenant_id)
    if not subscription or not subscription.plan:
        return

    current_products_count = db.execute(
        select(func.count(Product.id)).where(Product.tenant_id == tenant_id)
    ).scalar_one()

    if current_products_count >= subscription.plan.max_garments:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Límite de prendas alcanzado para el plan actual. Actualizá tu suscripción.",
        )


def tenant_has_feature(db: Session, tenant_id: UUID, feature_key: str) -> bool:
    """
    Returns True if the tenant's active subscription includes the given feature.
    """
    subscription = get_active_subscription(db, tenant_id)
    if not subscription or not subscription.plan:
        return False
    features = subscription.plan.features or []
    return feature_key in features


def create_or_update_tenant_subscription(
    db: Session,
    tenant_id: UUID,
    plan_id: str,
    billing_cycle: BillingCycleEnum = BillingCycleEnum.monthly,
    payment_method: SubscriptionPaymentMethodEnum = SubscriptionPaymentMethodEnum.simulated_card,
    duration_days: int | None = None,
) -> TenantSubscription:
    plan = get_plan_by_id(db, plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El plan de suscripción seleccionado no existe.",
        )

    now = datetime.now(timezone.utc)
    if duration_days is None:
        duration_days = 365 if billing_cycle == BillingCycleEnum.yearly else 30
    end_date = now + timedelta(days=duration_days)

    # Cancel previous active subscriptions for this tenant
    existing_subs = db.execute(
        select(TenantSubscription).where(
            TenantSubscription.tenant_id == tenant_id,
            TenantSubscription.status == SubscriptionStatusEnum.active,
        )
    ).scalars().all()
    for sub in existing_subs:
        sub.status = SubscriptionStatusEnum.canceled

    new_sub = TenantSubscription(
        tenant_id=tenant_id,
        plan_id=plan.id,
        billing_cycle=billing_cycle,
        status=SubscriptionStatusEnum.active,
        payment_method=payment_method,
        start_date=now,
        end_date=end_date,
    )
    db.add(new_sub)
    db.flush()
    return new_sub


def get_tenant_subscription_summary(db: Session, tenant_id: UUID) -> dict:
    tenant = db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organización no encontrada.",
        )

    subscription = get_active_subscription(db, tenant_id)
    branches_count = db.execute(
        select(func.count(Branch.id)).where(Branch.tenant_id == tenant_id)
    ).scalar_one()
    garments_count = db.execute(
        select(func.count(Product.id)).where(Product.tenant_id == tenant_id)
    ).scalar_one()

    if not subscription or not subscription.plan:
        return {
            "tenant_id": str(tenant.id),
            "tenant_name": tenant.name,
            "has_active_subscription": False,
            "plan": None,
            "subscription": None,
            "usage": {
                "branches_count": branches_count,
                "branches_max": None,
                "garments_count": garments_count,
                "garments_max": None,
            },
            "features": [],
        }

    plan = subscription.plan
    return {
        "tenant_id": str(tenant.id),
        "tenant_name": tenant.name,
        "has_active_subscription": True,
        "plan": {
            "id": plan.id,
            "name": plan.name,
            "slug": plan.slug,
            "description": plan.description,
            "price_monthly": float(plan.price_monthly),
            "price_yearly": float(plan.price_yearly),
            "max_branches": plan.max_branches,
            "max_garments": plan.max_garments,
            "features": plan.features or [],
        },
        "subscription": {
            "id": str(subscription.id),
            "status": subscription.status.value if hasattr(subscription.status, "value") else subscription.status,
            "billing_cycle": subscription.billing_cycle.value if hasattr(subscription.billing_cycle, "value") else subscription.billing_cycle,
            "payment_method": subscription.payment_method.value if hasattr(subscription.payment_method, "value") else subscription.payment_method,
            "start_date": subscription.start_date.isoformat() if subscription.start_date else None,
            "end_date": subscription.end_date.isoformat() if subscription.end_date else None,
        },
        "usage": {
            "branches_count": branches_count,
            "branches_max": plan.max_branches,
            "garments_count": garments_count,
            "garments_max": plan.max_garments,
        },
        "features": plan.features or [],
    }


def provision_tenant_onboarding(
    db: Session,
    payload: SubscriptionPurchaseSimulated,
) -> dict:
    company_name = payload.company_name.strip()
    slug_candidate = (payload.slug or slugify(company_name)).strip().lower()
    admin_email = payload.admin_email.strip().lower()

    # 1. Validation checks
    existing_tenant_name = db.execute(
        select(Tenant).where(func.lower(Tenant.name) == company_name.lower())
    ).scalars().first()
    if existing_tenant_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una empresa registrada con el nombre '{company_name}'.",
        )

    existing_tenant_slug = db.execute(
        select(Tenant).where(func.lower(Tenant.slug) == slug_candidate.lower())
    ).scalars().first()
    if existing_tenant_slug:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El subdominio o identificador '{slug_candidate}' ya está en uso. Elegí otro.",
        )

    existing_user = db.execute(
        select(User).where(func.lower(User.email) == admin_email)
    ).scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El correo electrónico '{admin_email}' ya se encuentra registrado para otro usuario.",
        )

    plan = get_plan_by_id(db, payload.plan_id)
    if not plan or not plan.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El plan de suscripción seleccionado no se encuentra disponible.",
        )

    # 2. Atomic Provisioning
    tenant = Tenant(
        name=company_name,
        slug=slug_candidate,
        contact_email=admin_email,
        currency=(payload.currency or "BOB").strip().upper(),
        country=(payload.country or "Bolivia").strip(),
        status=TenantStatusEnum.active,
    )
    db.add(tenant)
    db.flush()

    raw_password = generate_random_password(12)
    admin_user = User(
        name=payload.admin_name.strip(),
        email=admin_email,
        hashed_password=hash_password(raw_password),
        gender=GenderEnum.femenino,  # Default fallback
        rol=RolEnum.administrador,
        tenant_id=tenant.id,
        branch_id=None,
        is_active=True,
    )
    db.add(admin_user)
    db.flush()

    duration_days = 365 if payload.billing_cycle == BillingCycleEnum.yearly else 30
    now = datetime.now(timezone.utc)
    subscription = TenantSubscription(
        tenant_id=tenant.id,
        plan_id=plan.id,
        billing_cycle=payload.billing_cycle,
        status=SubscriptionStatusEnum.active,
        payment_method=SubscriptionPaymentMethodEnum.simulated_card,
        start_date=now,
        end_date=now + timedelta(days=duration_days),
    )
    db.add(subscription)
    db.commit()
    db.refresh(tenant)
    db.refresh(admin_user)
    db.refresh(subscription)

    return {
        "tenant": tenant,
        "admin_user": admin_user,
        "subscription": subscription,
        "plan": plan,
        "raw_password": raw_password,
    }


def provision_tenant_by_superadmin(
    db: Session,
    payload: TenantWithSubscriptionCreate,
) -> dict:
    company_name = payload.name.strip()
    slug_candidate = (payload.slug or slugify(company_name)).strip().lower()
    admin_email = payload.contact_email.strip().lower()

    # 1. Validation checks
    existing_tenant_name = db.execute(
        select(Tenant).where(func.lower(Tenant.name) == company_name.lower())
    ).scalars().first()
    if existing_tenant_name:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe una empresa registrada con el nombre '{company_name}'.",
        )

    existing_tenant_slug = db.execute(
        select(Tenant).where(func.lower(Tenant.slug) == slug_candidate.lower())
    ).scalars().first()
    if existing_tenant_slug:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El identificador '{slug_candidate}' ya está en uso. Elegí otro.",
        )

    existing_user = db.execute(
        select(User).where(func.lower(User.email) == admin_email)
    ).scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"El correo '{admin_email}' ya está registrado para otro usuario.",
        )

    plan = get_plan_by_id(db, payload.plan_id)
    if not plan or not plan.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El plan de suscripción seleccionado no existe o no está activo.",
        )

    # 2. Atomic Provisioning
    tenant = Tenant(
        name=company_name,
        slug=slug_candidate,
        contact_email=admin_email,
        currency=(payload.currency or "BOB").strip().upper(),
        country=(payload.country or "Bolivia").strip(),
        status=TenantStatusEnum.active,
    )
    db.add(tenant)
    db.flush()

    raw_password = generate_random_password(12)
    admin_user = User(
        name=payload.admin_name.strip(),
        email=admin_email,
        hashed_password=hash_password(raw_password),
        gender=GenderEnum.masculino,
        rol=RolEnum.administrador,
        tenant_id=tenant.id,
        branch_id=None,
        is_active=True,
    )
    db.add(admin_user)
    db.flush()

    duration_days = 365 if payload.billing_cycle == BillingCycleEnum.yearly else 30
    now = datetime.now(timezone.utc)
    subscription = TenantSubscription(
        tenant_id=tenant.id,
        plan_id=plan.id,
        billing_cycle=payload.billing_cycle,
        status=SubscriptionStatusEnum.active,
        payment_method=payload.payment_method,
        start_date=now,
        end_date=now + timedelta(days=duration_days),
    )
    db.add(subscription)
    db.commit()
    db.refresh(tenant)
    db.refresh(admin_user)
    db.refresh(subscription)

    return {
        "tenant": tenant,
        "admin_user": admin_user,
        "subscription": subscription,
        "plan": plan,
        "raw_password": raw_password,
    }

