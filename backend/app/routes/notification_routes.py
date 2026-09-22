from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.notification_schema import DeviceTokenUpsert
from app.services.notification_service import (
    list_notifications,
    mark_all_notifications_read,
    mark_notification_read,
    register_device_token,
    unregister_device_token,
    unread_count,
)
from app.utils.response import response


router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
async def list_notifications_route(
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return response(200, "Notificaciones obtenidas exitosamente", list_notifications(db, current_user.id, limit))


@router.get("/unread-count")
async def unread_count_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return response(200, "Conteo de notificaciones obtenido exitosamente", {"count": unread_count(db, current_user.id)})


@router.patch("/read-all")
async def mark_all_read_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return response(200, "Notificaciones marcadas como leídas", {"updated": mark_all_notifications_read(db, current_user.id)})


@router.patch("/{notification_id}/read")
async def mark_read_route(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = mark_notification_read(db, current_user.id, notification_id)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificación no encontrada")
    return response(200, "Notificación marcada como leída", notification)


@router.post("/tokens", status_code=status.HTTP_201_CREATED)
async def register_token_route(
    payload: DeviceTokenUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return response(201, "Token registrado exitosamente", register_device_token(db, current_user.id, payload))


@router.delete("/tokens")
async def unregister_token_route(
    payload: DeviceTokenUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    removed = unregister_device_token(db, current_user.id, payload.token)
    return response(200, "Token eliminado exitosamente", {"removed": removed})
