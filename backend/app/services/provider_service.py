from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.models.product import Product
from app.models.provider import Provider
from app.models.user import User
from app.models.provider_variant_availability import ProviderVariantAvailability
from app.models.product_variant import ProductVariant
from app.schemas.enums import RolEnum, ProviderStatusEnum
from app.schemas.provider_schema import ProviderCreate, ProviderStatusUpdate
from app.services.user_service import pwd_context, normalize_email, ensure_email_available


def _providers(db: Session, tenant_id):
    return db.query(Provider).join(User, User.id == Provider.user_id).filter(
        Provider.tenant_id == tenant_id,
        User.tenant_id == tenant_id,
        User.rol == RolEnum.proveedor,
    )


def get_provider(db: Session, provider_id, tenant_id):
    return _providers(db, tenant_id).filter(Provider.id == provider_id).first()


def get_provider_for_user(db: Session, user_id, tenant_id):
    return _providers(db, tenant_id).filter(Provider.user_id == user_id).first()


def create_provider(db: Session, provider: ProviderCreate, tenant_id) -> Provider:
    hashed_password = pwd_context.hash(provider.password)
    ensure_email_available(db, provider.email)

    db_user = User(
        name=provider.contact_name,
        email=normalize_email(provider.email),
        hashed_password=hashed_password,
        gender=provider.gender,
        rol=RolEnum.proveedor,
        tenant_id=tenant_id,
        branch_id=None,
    )

    db_provider = Provider(
        tenant_id=tenant_id,
        user_id=None,
        business_name=provider.business_name,
        contact_name=provider.contact_name,
        phone=provider.phone,
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


def get_providers(db: Session, tenant_id):
    return _providers(db, tenant_id).with_entities(Provider, User).order_by(Provider.business_name.asc()).all()


def update_provider_status(db: Session, provider_id, update_data: ProviderStatusUpdate, tenant_id) -> Provider | None:
    provider = get_provider(db, provider_id, tenant_id)
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


def update_provider_full(db: Session, provider_id, update_data, tenant_id) -> Provider | None:
    provider = get_provider(db, provider_id, tenant_id)
    if not provider:
        return None

    user = db.query(User).filter(User.id == provider.user_id).first()
    if not user:
        return None

    ensure_email_available(db, update_data.email, exclude_user_id=user.id)
    provider.business_name = update_data.business_name
    provider.contact_name = update_data.contact_name
    provider.phone = update_data.phone
    provider.status = update_data.status

    user.name = update_data.contact_name
    user.email = normalize_email(update_data.email)
    user.gender = update_data.gender
    user.branch_id = None
    user.is_active = update_data.status == ProviderStatusEnum.active

    try:
        db.commit()
        db.refresh(provider)
        return provider
    except IntegrityError:
        db.rollback()
        raise ValueError("No se pudo actualizar el proveedor")


def delete_provider(db: Session, provider_id, tenant_id) -> bool:
    provider = get_provider(db, provider_id, tenant_id)
    if not provider:
        return False

    user = db.query(User).filter(User.id == provider.user_id).first()

    try:
        db.query(Product).filter(Product.provider_id == provider.id, Product.tenant_id == tenant_id).update({Product.provider_id: None}, synchronize_session=False)
        db.delete(provider)
        if user:
            db.delete(user)
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        raise ValueError("No se pudo eliminar el proveedor")


def list_provider_products(db: Session, provider_id, tenant_id):
    return (
        db.query(Product)
        .options(selectinload(Product.variants.and_(ProductVariant.tenant_id == tenant_id)))
        .filter(Product.provider_id == provider_id, Product.tenant_id == tenant_id)
        .order_by(Product.name.asc())
        .all()
    )


def provider_availability_map(db: Session, provider_id, variant_ids, tenant_id):
    if not variant_ids:
        return {}
    return {
        row.variant_id: row.quantity
        for row in db.query(ProviderVariantAvailability).join(
            ProductVariant, ProductVariant.id == ProviderVariantAvailability.variant_id,
        ).join(Product, Product.id == ProductVariant.product_id).filter(
            ProviderVariantAvailability.provider_id == provider_id,
            ProviderVariantAvailability.variant_id.in_(variant_ids),
            Product.provider_id == provider_id,
            Product.tenant_id == tenant_id,
            ProductVariant.tenant_id == tenant_id,
        )
    }


def update_provider_availability(db: Session, provider_id, updates, tenant_id):
    variant_ids = [item.variant_id for item in updates]
    variants = db.query(ProductVariant).join(Product).filter(
        Product.provider_id == provider_id,
        Product.tenant_id == tenant_id,
        ProductVariant.tenant_id == tenant_id,
        ProductVariant.id.in_(variant_ids),
    ).all()
    variants_by_id = {variant.id: variant for variant in variants}
    if len(variants_by_id) != len(set(variant_ids)):
        raise ValueError("La variante no pertenece a un producto asignado a este proveedor")

    for item in updates:
        row = db.query(ProviderVariantAvailability).filter_by(provider_id=provider_id, variant_id=item.variant_id).first()
        if row:
            row.quantity = item.quantity
        else:
            db.add(ProviderVariantAvailability(provider_id=provider_id, variant_id=item.variant_id, quantity=item.quantity))
    db.commit()
    return provider_availability_map(db, provider_id, variant_ids, tenant_id)
