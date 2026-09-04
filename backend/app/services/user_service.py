from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.user import User
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

def get_users(db: Session, skip: int = 0, limit: int = 10):
    result = db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()

def get_users_count(db: Session):
    result = db.execute(select(func.count(User.id)))
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
