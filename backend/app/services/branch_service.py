from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.branch import Branch
from app.schemas.branch_schema import BranchCreate


def create_branch(db: Session, branch: BranchCreate) -> Branch:
    db_branch = Branch(name=branch.name, city=branch.city, is_default=branch.is_default)
    db.add(db_branch)
    db.commit()
    db.refresh(db_branch)
    return db_branch


def get_branches(db: Session, branch_id=None):
    query = select(Branch)
    if branch_id is not None:
        query = query.where(Branch.id == branch_id)
    result = db.execute(query.order_by(Branch.name.asc()))
    return result.scalars().all()
