from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.product import Product
from app.models.provider import Provider
from app.models.user import User
from app.schemas.enums import RolEnum, ProviderStatusEnum
from app.schemas.provider_schema import ProviderCreate, ProviderStatusUpdate
from app.services.user_service import pwd_context, normalize_email, ensure_email_available


def create_provider(db: Session, provider: ProviderCreate) -> Provider:
    hashed_password = pwd_context.hash(provider.password)
    ensure_email_available(db, provider.email)

    db_user = User(
        name=provider.contact_name,
        email=normalize_email(provider.email),
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
    if provider.user_id:
        db.query(User).filter(User.id == provider.user_id).update(
            {User.is_active: update_data.status == ProviderStatusEnum.active},
            synchronize_session=False,
        )
    db.commit()
    db.refresh(provider)
    return provider


def update_provider_full(db: Session, provider_id, update_data) -> Provider | None:
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        return None

    user = db.query(User).filter(User.id == provider.user_id).first()
    if not user:
        return None

    ensure_email_available(db, update_data.email, exclude_user_id=user.id)
    provider.business_name = update_data.business_name
    provider.contact_name = update_data.contact_name
    provider.phone = update_data.phone
    provider.branch_id = update_data.branch_id
    provider.status = update_data.status

    user.name = update_data.contact_name
    user.email = normalize_email(update_data.email)
    user.gender = update_data.gender
    user.branch_id = update_data.branch_id
    user.is_active = update_data.status == ProviderStatusEnum.active

    try:
        db.commit()
        db.refresh(provider)
        return provider
    except IntegrityError:
        db.rollback()
        raise ValueError("No se pudo actualizar el proveedor")


def delete_provider(db: Session, provider_id) -> bool:
    provider = db.query(Provider).filter(Provider.id == provider_id).first()
    if not provider:
        return False

    user = db.query(User).filter(User.id == provider.user_id).first()

    try:
        db.query(Product).filter(Product.provider_id == provider.id).update({Product.provider_id: None}, synchronize_session=False)
        db.delete(provider)
        if user:
            db.delete(user)
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        raise ValueError("No se pudo eliminar el proveedor")
