from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.branch import Branch
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.enums import TenantStatusEnum
from app.schemas.tenant_schema import TenantCreate, TenantUpdate


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
        "created_at": tenant.created_at,
        "updated_at": tenant.updated_at,
        "branches_count": branches_count,
        "users_count": users_count,
    }


def list_tenants(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    status: Optional[TenantStatusEnum] = None,
) -> tuple[list[dict], int]:
    query = db.query(Tenant)

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
