from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.provider import Provider
from app.models.user import User
from app.schemas.enums import RolEnum, ProviderStatusEnum
from app.schemas.provider_schema import ProviderCreate, ProviderStatusUpdate
from app.services.user_service import pwd_context


def create_provider(db: Session, provider: ProviderCreate) -> Provider:
    hashed_password = pwd_context.hash(provider.password)

    db_user = User(
        name=provider.contact_name,
        email=provider.email,
        hashed_password=hashed_password,
        gender=provider.gender,
        rol=RolEnum.proveedor,
        branch_id=provider.branch_id,
    )

    db_provider = Provider(
        user_id=None,
        business_name=provider.business_name,
        contact_name=provider.contact_name,
        phone=provider.phone,
        branch_id=provider.branch_id,
        status=ProviderStatusEnum.active,
        is_active=True,
    )

    db.add(db_user)
    db.flush()
    db_provider.user_id = db_user.id
    db.add(db_provider)

    try:
        db.commit()
        db.refresh(db_provider)
        return db_provider
    except IntegrityError:
        db.rollback()
        raise ValueError("No se pudo crear el proveedor")


def get_providers(db: Session, branch_id=None):
    query = select(Provider, User).join(User, User.id == Provider.user_id)
    if branch_id is not None:
        query = query.where(Provider.branch_id == branch_id)
    result = db.execute(query.order_by(Provider.business_name.asc()))
    return result.all()


def update_provider_status(db: Session, provider_id, update_data: ProviderStatusUpdate) -> Provider | None:
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        return None

    provider.status = update_data.status
    db.commit()
    db.refresh(provider)
    return provider


def set_provider_active(db: Session, provider_id, is_active: bool) -> Provider | None:
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        return None

    provider.is_active = is_active
    db.commit()
    db.refresh(provider)
    return provider
