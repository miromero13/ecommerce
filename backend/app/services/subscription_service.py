from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
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
    SubscriptionChangePlan,
    SubscriptionPlanCreate,
    SubscriptionPlanUpdate,
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


# Modules the platform knows how to sell; the frontend describes each one.
PLAN_FEATURE_KEYS = (
    "catalog", "pos", "inventory", "reservations", "standard_reports", "chatbot",
    "virtual_try_on_2d", "ai_text_reports", "virtual_try_on_3d_ar", "ai_ml_smart_reports",
)


def _valid_features(features: list[str]) -> list[str]:
    unknown = [key for key in features if key not in PLAN_FEATURE_KEYS]
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Funciones de plan desconocidas: {', '.join(unknown)}",
        )
    return list(dict.fromkeys(features))


def create_plan(db: Session, payload: SubscriptionPlanCreate) -> SubscriptionPlan:
    plan_id = "plan_" + payload.slug.replace("-", "_")
    exists = db.execute(select(SubscriptionPlan.id).where(
        or_(SubscriptionPlan.id == plan_id, SubscriptionPlan.slug == payload.slug)
    )).first()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un plan con el identificador '{payload.slug}'.",
        )
    plan = SubscriptionPlan(id=plan_id, **{**payload.model_dump(), "features": _valid_features(payload.features)})
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def update_plan(db: Session, plan_id: str, payload: SubscriptionPlanUpdate) -> SubscriptionPlan:
    """Changes apply to current subscribers too; deactivating only hides the plan from new purchases."""
    plan = get_plan_by_id(db, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan no encontrado.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is None and field != "description":
            continue  # every other column is NOT NULL
        setattr(plan, field, _valid_features(value) if field == "features" else value)
    db.commit()
    db.refresh(plan)
    return plan


TRY_ON_FEATURE = "virtual_try_on_2d"
CHATBOT_FEATURE = "chatbot"
NO_ACTIVE_SUBSCRIPTION ="Tu empresa no tiene una suscripción activa. Renová o elegí un plan para continuar."


def _period_price(plan: SubscriptionPlan, billing_cycle: BillingCycleEnum):
    return plan.price_yearly if billing_cycle == BillingCycleEnum.yearly else plan.price_monthly


def _is_current() -> tuple:
    # A subscription past its end_date no longer counts, even if never marked canceled.
    return (
        TenantSubscription.status == SubscriptionStatusEnum.active,
        or_(TenantSubscription.end_date.is_(None), TenantSubscription.end_date > datetime.now(timezone.utc)),
    )


def get_active_subscription(db: Session, tenant_id: UUID) -> TenantSubscription | None:
    return db.execute(
        select(TenantSubscription)
        .where(TenantSubscription.tenant_id == tenant_id, *_is_current())
        .order_by(TenantSubscription.created_at.desc())
    ).scalars().first()


def _count_branches(db: Session, tenant_id: UUID) -> int:
    return db.execute(select(func.count(Branch.id)).where(Branch.tenant_id == tenant_id)).scalar_one()


def _count_garments(db: Session, tenant_id: UUID) -> int:
    return db.execute(select(func.count(Product.id)).where(Product.tenant_id == tenant_id)).scalar_one()


def _require_active_plan(db: Session, tenant_id: UUID) -> SubscriptionPlan:
    subscription = get_active_subscription(db, tenant_id)
    if not subscription or not subscription.plan:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=NO_ACTIVE_SUBSCRIPTION)
    return subscription.plan


def check_tenant_branch_quota(db: Session, tenant_id: UUID) -> None:
    """Raise 403 if the tenant has no current plan or reached its branch quota."""
    plan = _require_active_plan(db, tenant_id)
    if _count_branches(db, tenant_id) >= plan.max_branches:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Límite de sucursales alcanzado para el plan actual. Actualizá tu suscripción.",
        )


def check_tenant_garment_quota(db: Session, tenant_id: UUID) -> None:
    """Raise 403 if the tenant has no current plan or reached its garment quota."""
    plan = _require_active_plan(db, tenant_id)
    if _count_garments(db, tenant_id) >= plan.max_garments:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Límite de prendas alcanzado para el plan actual. Actualizá tu suscripción.",
        )


def tenant_features(db: Session, tenant_ids=None) -> dict[UUID, set[str]]:
    """Features of each tenant's current plan; tenants without one are absent."""
    query = select(TenantSubscription.tenant_id, SubscriptionPlan.features).join(
        SubscriptionPlan, SubscriptionPlan.id == TenantSubscription.plan_id
    ).where(*_is_current())
    if tenant_ids is not None:
        query = query.where(TenantSubscription.tenant_id.in_(list(tenant_ids)))
    return {tenant_id: set(features or []) for tenant_id, features in db.execute(query).all()}


def tenant_ids_with_feature(db: Session, feature_key: str) -> list[UUID]:
    return [tenant_id for tenant_id, features in tenant_features(db).items() if feature_key in features]


def tenant_has_feature(db: Session, tenant_id: UUID, feature_key: str) -> bool:
    return feature_key in tenant_features(db, [tenant_id]).get(tenant_id, set())


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

    # Serialize concurrent plan changes of the same tenant.
    db.query(Tenant).filter(Tenant.id == tenant_id).with_for_update().one()
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
        amount=_period_price(plan, billing_cycle),
        status=SubscriptionStatusEnum.active,
        payment_method=payment_method,
        start_date=now,
        end_date=end_date,
    )
    db.add(new_sub)
    db.flush()
    return new_sub


def change_tenant_plan(db: Session, tenant_id: UUID, payload: SubscriptionChangePlan) -> dict:
    """Simulated-card plan change for an existing company; starts a new period."""
    plan = get_plan_by_id(db, payload.plan_id)
    if not plan or not plan.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El plan seleccionado no se encuentra disponible.",
        )
    current = get_active_subscription(db, tenant_id)
    if current and current.plan_id == plan.id and current.billing_cycle == payload.billing_cycle:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tu empresa ya tiene activo el plan {plan.name} con esta facturación.",
        )
    # A downgrade must not leave the company above the new plan's limits.
    branches, garments = _count_branches(db, tenant_id), _count_garments(db, tenant_id)
    if branches > plan.max_branches:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No podés cambiar al plan {plan.name}: tenés {branches} sucursales y permite {plan.max_branches}.",
        )
    if garments > plan.max_garments:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No podés cambiar al plan {plan.name}: tenés {garments} prendas y permite {plan.max_garments}.",
        )
    try:
        create_or_update_tenant_subscription(
            db, tenant_id, plan.id, payload.billing_cycle, SubscriptionPaymentMethodEnum.simulated_card,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return get_tenant_subscription_summary(db, tenant_id)


_PAYMENT_METHOD_LABELS = {"simulated_card": "Tarjeta (simulada)", "cash": "Efectivo", "stripe": "Tarjeta (Stripe)"}


def list_subscription_history(db: Session, tenant_id: UUID) -> list[dict]:
    """CU2: every period the company paid, newest first (each plan purchase or change is one payment)."""
    if not db.get(Tenant, tenant_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organización no encontrada.")
    now = datetime.now(timezone.utc)
    rows = db.execute(
        select(TenantSubscription, SubscriptionPlan.name)
        .join(SubscriptionPlan, SubscriptionPlan.id == TenantSubscription.plan_id)
        .where(TenantSubscription.tenant_id == tenant_id)
        .order_by(TenantSubscription.created_at.desc())
    ).all()
    history = []
    for sub, plan_name in rows:
        if sub.status == SubscriptionStatusEnum.canceled:
            period_status = "Reemplazado"  # a later plan change started a new period
        elif sub.end_date and sub.end_date <= now:
            period_status = "Vencido"
        else:
            period_status = "Vigente"
        method = sub.payment_method.value if hasattr(sub.payment_method, "value") else sub.payment_method
        history.append({
            "id": str(sub.id),
            "paid_at": sub.created_at.isoformat() if sub.created_at else None,
            "plan_name": plan_name,
            "billing_cycle": sub.billing_cycle.value if hasattr(sub.billing_cycle, "value") else sub.billing_cycle,
            "amount": float(sub.amount) if sub.amount is not None else None,
            "currency": "BOB",  # plans are priced in bolivianos
            "payment_method": method,
            "payment_method_label": _PAYMENT_METHOD_LABELS.get(method, method),
            "start_date": sub.start_date.isoformat() if sub.start_date else None,
            "end_date": sub.end_date.isoformat() if sub.end_date else None,
            "status": period_status,
        })
    return history


def get_tenant_subscription_summary(db: Session, tenant_id: UUID) -> dict:
    tenant = db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organización no encontrada.",
        )

    subscription = get_active_subscription(db, tenant_id)
    branches_count = _count_branches(db, tenant_id)
    garments_count = _count_garments(db, tenant_id)

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
        amount=_period_price(plan, payload.billing_cycle),
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
        amount=_period_price(plan, payload.billing_cycle),
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

