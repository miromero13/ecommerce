from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from sqlalchemy import update as sa_update
from app.models.user import User
from app.models.provider import Provider
from app.models.product import Product
from app.schemas.user_schema import UserCreate, UserUpdateRol, UserUpdateBranch
from app.schemas.enums import RolEnum
from uuid import UUID  
from passlib.context import CryptContext

# Configura el hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user(db: Session, user: UserCreate) -> User:
    # 🔐 Hashea la contraseña antes de guardarla
    hashed_password = pwd_context.hash(user.password)

    db_user = User(
        name=user.name,
        email=user.email,
        gender=user.gender,
        rol=RolEnum.cliente,
        hashed_password=hashed_password,
        branch_id=None,
        is_active=True,
    )
    
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise ValueError("El correo ya está registrado")

def get_user(db: Session, user_id: UUID) -> User | None:  # 👈 Cambia int → UUID
    result = db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()

def get_users(db: Session, skip: int = 0, limit: int = 10, branch_id: UUID | None = None):
    query = select(User)
    if branch_id is not None:
        query = query.where(or_(User.branch_id == branch_id, User.rol == RolEnum.cliente))
    result = db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

def get_users_count(db: Session, branch_id: UUID | None = None):
    query = select(func.count(User.id))
    if branch_id is not None:
        query = query.where(or_(User.branch_id == branch_id, User.rol == RolEnum.cliente))
    result = db.execute(query)
    return result.scalar_one()
def update_user_rol(db: Session, user_id: UUID, update_data: UserUpdateRol) -> User | None:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    user.rol = update_data.rol
    db.commit()
    db.refresh(user)
    return user


def update_user_branch(db: Session, user_id: UUID, update_data: UserUpdateBranch) -> User | None:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    if user.rol not in {RolEnum.administrador, RolEnum.encargado, RolEnum.cajero}:
        raise ValueError("Solo los usuarios internos pueden tener sucursal asignada")

    user.branch_id = update_data.branch_id
    db.commit()
    db.refresh(user)
    return user


def update_user_full(db: Session, user_id: UUID, update_data) -> User | None:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    user.name = update_data.name
    user.email = update_data.email
    user.gender = update_data.gender
    user.branch_id = update_data.branch_id
    user.is_active = update_data.is_active
    if update_data.password:
        user.hashed_password = pwd_context.hash(update_data.password)

    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise ValueError("No se pudo actualizar el usuario")


def delete_user(db: Session, user_id: UUID) -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False

    try:
        if user.rol == RolEnum.proveedor:
            provider = db.query(Provider).filter(Provider.user_id == user.id).first()
            if provider:
                db.query(Product).filter(Product.provider_id == provider.id).update({Product.provider_id: None}, synchronize_session=False)
                db.delete(provider)

        db.delete(user)
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        raise ValueError("No se pudo eliminar el usuario")


def set_user_active(db: Session, user_id: UUID, is_active: bool) -> User | None:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user
