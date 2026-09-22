from datetime import datetime, timezone
import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.notification import DeviceToken, Notification
from app.schemas.notification_schema import DeviceTokenUpsert, NotificationRead
from app.services.notification_delivery import deliver_notification


logger = logging.getLogger(__name__)


def _serialize(notification: Notification) -> dict:
    return NotificationRead.model_validate(notification).model_dump()


def list_notifications(db: Session, user_id: UUID, limit: int = 100) -> list[dict]:
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )
    return [_serialize(notification) for notification in notifications]


def unread_count(db: Session, user_id: UUID) -> int:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.read_at.is_(None))
        .count()
    )


def mark_notification_read(db: Session, user_id: UUID, notification_id: UUID) -> dict | None:
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )
    if notification is None:
        return None
    if notification.read_at is None:
        notification.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notification)
    return _serialize(notification)


def mark_all_notifications_read(db: Session, user_id: UUID) -> int:
    updated = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.read_at.is_(None))
        .update({Notification.read_at: datetime.now(timezone.utc)}, synchronize_session=False)
    )
    db.commit()
    return updated


def register_device_token(db: Session, user_id: UUID, payload: DeviceTokenUpsert) -> dict:
    token = payload.token.strip()
    device = db.query(DeviceToken).filter(DeviceToken.token == token).first()
    if device is None:
        device = DeviceToken(user_id=user_id, token=token, platform=payload.platform, is_active=True)
        db.add(device)
    else:
        device.user_id = user_id
        device.platform = payload.platform
        device.is_active = True
    db.commit()
    db.refresh(device)
    return {"id": device.id, "token": device.token, "platform": device.platform}


def unregister_device_token(db: Session, user_id: UUID, token: str) -> bool:
    device = (
        db.query(DeviceToken)
        .filter(DeviceToken.user_id == user_id, DeviceToken.token == token.strip())
        .first()
    )
    if device is None:
        return False
    db.delete(device)
    db.commit()
    return True


def create_notification(
    db: Session,
    user_id: UUID,
    title: str,
    body: str,
    data: dict | None = None,
    dedupe_key: str | None = None,
) -> Notification | None:
    try:
        if dedupe_key:
            existing = db.query(Notification).filter(Notification.dedupe_key == dedupe_key).first()
            if existing:
                return existing
        notification = Notification(
            user_id=user_id,
            title=title,
            body=body,
            data=data or {},
            dedupe_key=dedupe_key,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
    except Exception:
        db.rollback()
        logger.exception("Could not persist notification for user %s", user_id)
        return None

    try:
        deliver_notification(db, notification)
    except Exception:
        logger.exception("Could not inspect device tokens for notification %s", notification.id)
    return notification


from app.services.notification_delivery import notify_low_stock, notify_order_event, notify_reservation_event
