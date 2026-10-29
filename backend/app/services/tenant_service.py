from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.branch import Branch
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.enums import RolEnum, TenantStatusEnum
from app.core.config import settings
from app.schemas.tenant_schema import TenantAdminCreate, TenantBrandingRead, TenantCreate, TenantUpdate
from app.services.cloudinary_service import delete_image, upload_image

LOGO_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp"}
LOGO_MAX_BYTES = 2 * 1024 * 1024


def _serialize_tenant(db: Session, tenant: Tenant) -> dict:
    branches_count = (
        db.query(func.count(Branch.id))
        .filter(Branch.tenant_id == tenant.id)
        .scalar()
        or 0
    )
    users_count = (
        db.query(func.count(User.id))
        .filter(User.tenant_id == tenant.id)
        .scalar()
        or 0
    )
    return {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "contact_email": tenant.contact_email,
        "currency": tenant.currency,
        "country": tenant.country,
        "status": tenant.status,
        "platform_fee_percent": tenant.platform_fee_percent,
        "logo_url": tenant.logo_url,
        "primary_color": tenant.primary_color,
        "created_at": tenant.created_at,
        "updated_at": tenant.updated_at,
        "branches_count": branches_count,
        "users_count": users_count,
        "has_admin": _active_admin(db, tenant.id) is not None,
        **_plan_info(db, tenant.id),
    }


def _plan_info(db: Session, tenant_id: UUID) -> dict:
    from app.services.subscription_service import get_active_subscription

    sub = get_active_subscription(db, tenant_id)
    return {
        "plan_name": sub.plan.name if sub and sub.plan else None,
        "subscription_end_date": sub.end_date if sub else None,
    }


def _active_admin(db: Session, tenant_id: UUID) -> User | None:
    return (db.query(User)
            .filter(User.tenant_id == tenant_id, User.rol == RolEnum.administrador, User.is_active.is_(True))
            .order_by(User.email).first())


def _add_admin(db: Session, tenant_id: UUID, admin: TenantAdminCreate) -> User:
    from app.services.user_service import ensure_email_available, normalize_email, pwd_context

    ensure_email_available(db, admin.email)
    user = User(name=admin.name.strip(), email=normalize_email(admin.email), gender=admin.gender,
                rol=RolEnum.administrador, hashed_password=pwd_context.hash(admin.password),
                tenant_id=tenant_id, branch_id=None, is_active=True)
    db.add(user)
    return user


def list_tenants(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    status: Optional[TenantStatusEnum] = None,
) -> tuple[list[dict], int]:
    from app.models.tenant_subscription import TenantSubscription

    # CU2: only companies that subscribed to a plan (current or past) are platform tenants.
    query = db.query(Tenant).filter(select(TenantSubscription.id).where(TenantSubscription.tenant_id == Tenant.id).exists())

    if search:
        search_term = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                func.lower(Tenant.name).like(search_term),
                func.lower(Tenant.slug).like(search_term),
                func.lower(Tenant.contact_email).like(search_term),
            )
        )

    if status:
        query = query.filter(Tenant.status == status)

    total = query.count()
    tenants = query.order_by(Tenant.created_at.desc()).offset(skip).limit(limit).all()
    data = [_serialize_tenant(db, t) for t in tenants]
    return data, total


def get_tenant(db: Session, tenant_id: UUID) -> dict | None:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return None
    return _serialize_tenant(db, tenant)


def create_tenant(db: Session, payload: TenantCreate) -> dict:
    existing_name = db.query(Tenant).filter(func.lower(Tenant.name) == payload.name.strip().lower()).first()
    if existing_name:
        raise ValueError(f"Ya existe una empresa con el nombre '{payload.name}'")

    existing_slug = db.query(Tenant).filter(func.lower(Tenant.slug) == payload.slug.strip().lower()).first()
    if existing_slug:
        raise ValueError(f"Ya existe una empresa con el identificador '{payload.slug}'")

    tenant = Tenant(
        name=payload.name.strip(),
        slug=payload.slug.strip().lower(),
        contact_email=payload.contact_email.strip().lower(),
        currency=payload.currency.strip().upper(),
        country=payload.country.strip() if payload.country else "Bolivia",
        status=payload.status,
    )
    db.add(tenant)
    try:
        db.commit()
        db.refresh(tenant)
        return _serialize_tenant(db, tenant)
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Error de integridad al registrar la empresa") from exc


def register_tenant_admin(db: Session, tenant_id: UUID, admin: TenantAdminCreate) -> dict | None:
    """For companies created before the administrator was required."""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return None
    if _active_admin(db, tenant_id):
        raise ValueError("La empresa ya tiene un administrador activo")
    try:
        _add_admin(db, tenant_id, admin)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("El correo ya está registrado") from exc
    return _serialize_tenant(db, tenant)


class NoTenantAdmin(Exception):
    pass


def open_tenant_panel(db: Session, tenant_id: UUID, superadmin_id: UUID) -> dict | None:
    """Session of the company's administrator for the superadmin (full access, like the administrator).
    The token keeps `impersonated_by` so the action can be traced back to the superadmin."""
    from app.auth.jwt import create_access_token
    from app.schemas.user_schema import UserRead
    from app.services.rbac_service import effective_permissions

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return None
    if tenant.status == TenantStatusEnum.suspended:
        raise ValueError("La empresa está suspendida: actívala para entrar a su panel")
    admin = _active_admin(db, tenant_id)
    if not admin:
        raise NoTenantAdmin("La empresa no tiene un administrador activo. Regístralo desde el detalle de la empresa.")
    perms = effective_permissions(db, admin)
    token = create_access_token(data={
        "sub": str(admin.id), "rol": admin.rol.value, "tenant_id": str(tenant_id), "branch_id": None,
        "permissions": perms, "impersonated_by": str(superadmin_id),
    })
    user_out = UserRead.model_validate(admin).model_dump()
    user_out["permissions"] = perms
    return {"access_token": token, "token_type": "bearer", "user": user_out, "tenant_name": tenant.name}


def update_tenant(db: Session, tenant_id: UUID, payload: TenantUpdate) -> dict | None:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return None

    if payload.name is not None:
        name_check = db.query(Tenant).filter(
            func.lower(Tenant.name) == payload.name.strip().lower(),
            Tenant.id != tenant_id,
        ).first()
        if name_check:
            raise ValueError(f"Ya existe otra empresa con el nombre '{payload.name}'")
        tenant.name = payload.name.strip()

    if payload.slug is not None:
        slug_check = db.query(Tenant).filter(
            func.lower(Tenant.slug) == payload.slug.strip().lower(),
            Tenant.id != tenant_id,
        ).first()
        if slug_check:
            raise ValueError(f"Ya existe otra empresa con el identificador '{payload.slug}'")
        tenant.slug = payload.slug.strip().lower()

    if payload.contact_email is not None:
        tenant.contact_email = payload.contact_email.strip().lower()

    if payload.currency is not None:
        tenant.currency = payload.currency.strip().upper()

    if payload.country is not None:
        tenant.country = payload.country.strip()

    if payload.status is not None:
        tenant.status = payload.status

    if payload.platform_fee_percent is not None:
        tenant.platform_fee_percent = payload.platform_fee_percent

    if payload.primary_color is not None:
        tenant.primary_color = payload.primary_color.lower()

    try:
        db.commit()
        db.refresh(tenant)
        return _serialize_tenant(db, tenant)
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Error de integridad al actualizar la empresa") from exc


def update_tenant_status(db: Session, tenant_id: UUID, new_status: TenantStatusEnum) -> dict | None:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return None
    tenant.status = new_status
    db.commit()
    db.refresh(tenant)
    return _serialize_tenant(db, tenant)


def _branding(tenant: Tenant) -> dict:
    return TenantBrandingRead(tenant_id=tenant.id, name=tenant.name, logo_url=tenant.logo_url,
                              primary_color=tenant.primary_color, currency=tenant.currency).model_dump()


def get_branding(db: Session, tenant_id: UUID) -> dict | None:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    return _branding(tenant) if tenant else None


def update_branding_color(db: Session, tenant_id: UUID, primary_color: str | None) -> dict:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).one()
    tenant.primary_color = primary_color.lower() if primary_color else None
    db.commit()
    return _branding(tenant)


def update_tenant_logo(db: Session, tenant_id: UUID, content: bytes, content_type: str | None) -> dict | None:
    """Validate at the upload boundary, store in Cloudinary, then drop the replaced logo."""
    if content_type not in LOGO_CONTENT_TYPES:
        raise ValueError("El logo debe ser una imagen PNG, JPG o WEBP")
    if not content:
        raise ValueError("El archivo del logo no puede estar vacío")
    if len(content) > LOGO_MAX_BYTES:
        raise ValueError("El logo no puede superar los 2 MB")
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        return None
    uploaded = upload_image(content, folder=f"{settings.cloudinary_folder}/tenants/{tenant.id}")
    previous = tenant.logo_public_id
    tenant.logo_url, tenant.logo_public_id = uploaded["image_url"], uploaded["image_public_id"]
    db.commit()
    if previous and previous != tenant.logo_public_id:
        delete_image(previous)
    return _branding(tenant)
