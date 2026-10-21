from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.branch import Branch
from app.models.user import User
from app.schemas.branch_schema import BranchCreate


def create_branch(db: Session, branch: BranchCreate, tenant_id: UUID | None = None) -> Branch:
    db_branch = Branch(
        name=branch.name,
        city=branch.city,
        is_default=branch.is_default,
        is_active=True,
        tenant_id=tenant_id,
    )
    db.add(db_branch)
    db.commit()
    db.refresh(db_branch)
    return db_branch


def get_branches(db: Session, branch_id: UUID | None = None, tenant_id: UUID | None = None):
    query = select(Branch)
    if tenant_id is not None:
        query = query.where(Branch.tenant_id == tenant_id)
    if branch_id is not None:
        query = query.where(Branch.id == branch_id)
    result = db.execute(query.order_by(Branch.name.asc()))
    return result.scalars().all()


def update_branch(db: Session, branch_id: UUID, update_data, tenant_id: UUID | None = None) -> Branch | None:
    query = db.query(Branch).filter(Branch.id == branch_id)
    if tenant_id is not None:
        query = query.filter(Branch.tenant_id == tenant_id)
    branch = query.first()
    if not branch:
        return None

    branch.name = update_data.name
    branch.city = update_data.city
    branch.is_default = update_data.is_default
    branch.is_active = update_data.is_active
    db.commit()
    db.refresh(branch)
    return branch


def delete_branch(db: Session, branch_id: UUID, tenant_id: UUID | None = None) -> bool:
    query = db.query(Branch).filter(Branch.id == branch_id)
    if tenant_id is not None:
        query = query.filter(Branch.tenant_id == tenant_id)
    branch = query.first()
    if not branch:
        return False

    try:
        db.query(User).filter(User.branch_id == branch.id).update({User.branch_id: None}, synchronize_session=False)
        db.delete(branch)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise ValueError("No se pudo eliminar la sucursal")


def set_branch_active(db: Session, branch_id: UUID, is_active: bool, tenant_id: UUID | None = None) -> Branch | None:
    query = db.query(Branch).filter(Branch.id == branch_id)
    if tenant_id is not None:
        query = query.filter(Branch.tenant_id == tenant_id)
    branch = query.first()
    if not branch:
        return None

    branch.is_active = is_active
    db.commit()
    db.refresh(branch)
    return branch
