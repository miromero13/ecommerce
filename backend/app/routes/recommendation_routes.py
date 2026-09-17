from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.schemas.enums import RolEnum
from app.services.recommendation_service import get_recommendations, validate_recommendation_owner
from app.utils.response import response


router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/collaborative/user/{user_id}")
async def collaborative_recommendations_route(
    user_id: UUID,
    branch_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles(RolEnum.cliente)),
):
    try:
        validate_recommendation_owner(user_id, current_user)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return response(
        status_code=200,
        message="Recommendations retrieved",
        data=get_recommendations(
            db,
            user_id,
            branch_id=branch_id,
        ),
    )
