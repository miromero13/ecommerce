from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.schemas.dashboard_schema import DashboardPeriod, DashboardQuery
from app.schemas.enums import RolEnum
from app.services.dashboard_service import get_dashboard
from app.utils.response import response


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _filters(
    branch_id: UUID | None = Query(default=None),
    from_date: date | None = Query(default=None),
    to_date: date | None = Query(default=None),
    period: DashboardPeriod = Query(default='day'),
) -> DashboardQuery:
    return DashboardQuery(branch_id=branch_id, from_date=from_date, to_date=to_date, period=period)


@router.get("")
def dashboard_route(
    db: Session = Depends(get_db),
    filters: DashboardQuery = Depends(_filters),
    current_user: dict = Depends(require_roles(RolEnum.administrador)),
):
    dashboard = get_dashboard(db, filters)
    return response(status_code=200, message="Dashboard obtenido exitosamente", data=dashboard.model_dump())
