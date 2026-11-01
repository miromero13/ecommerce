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


# [CU12 - Secuencia: Paso 1.5] NotificationPageComponent llama a list_notifications_route(limit) de notification_routes (GET /api/notifications)
# [CU12 - Secuencia: Paso 1.10] notification_routes retorna list_notifications_route(limit): 200 Notificaciones obtenidas exitosamente a NotificationPageComponent
@router.get("")
async def list_notifications_route(
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return response(200, "Notificaciones obtenidas exitosamente", list_notifications(db, current_user.id, limit))


# [CU12 - Secuencia: Paso 1.11] NotificationPageComponent llama a unread_count_route() de notification_routes (GET /api/notifications/unread-count)
# [CU12 - Secuencia: Paso 1.14] notification_routes retorna unread_count_route(): 200 Conteo de notificaciones obtenido exitosamente a NotificationPageComponent
@router.get("/unread-count")
async def unread_count_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return response(200, "Conteo de notificaciones obtenido exitosamente", {"count": unread_count(db, current_user.id)})


# [CU12 - Secuencia: Paso 3.1] NotificationPageComponent llama a mark_all_read_route() de notification_routes (PATCH /api/notifications/read-all)
# [CU12 - Secuencia: Paso 3.4] notification_routes retorna mark_all_read_route(): 200 Notificaciones marcadas como leídas a NotificationPageComponent
@router.patch("/read-all")
async def mark_all_read_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return response(200, "Notificaciones marcadas como leídas", {"updated": mark_all_notifications_read(db, current_user.id)})


# [CU12 - Secuencia: Paso 2.1] NotificationPageComponent llama a mark_read_route(notification_id) de notification_routes (PATCH /api/notifications/{notification_id}/read)
# [CU12 - Secuencia: Paso 2.6] notification_routes retorna mark_read_route(notification_id): 200 Notificación marcada como leída a NotificationPageComponent
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


# [CU12 - Secuencia: Paso 1.1] NotificationPageComponent llama a register_token_route(payload) de notification_routes (POST /api/notifications/tokens)
# [CU12 - Secuencia: Paso 1.4] notification_routes retorna register_token_route(payload): 201 Token registrado exitosamente a NotificationPageComponent
@router.post("/tokens", status_code=status.HTTP_201_CREATED)
async def register_token_route(
    payload: DeviceTokenUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return response(201, "Token registrado exitosamente", register_device_token(db, current_user.id, payload))


# [CU12 - Secuencia: Paso 4.1] AppShellComponent llama a unregister_token_route(payload) de notification_routes (DELETE /api/notifications/tokens)
# [CU12 - Secuencia: Paso 4.4] notification_routes retorna unregister_token_route(payload): 200 Token eliminado exitosamente a AppShellComponent
@router.delete("/tokens")
async def unregister_token_route(
    payload: DeviceTokenUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    removed = unregister_device_token(db, current_user.id, payload.token)
    return response(200, "Token eliminado exitosamente", {"removed": removed})
