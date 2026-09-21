from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

from app.schemas.notification_schema import DeviceTokenUpsert
from app.services import notification_service
from app.services import notification_delivery


def _query_db(result=None, *, all_result=None, update_result=0):
    db = MagicMock()
    query = MagicMock()
    query.filter.return_value = query
    query.order_by.return_value = query
    query.limit.return_value = query
    query.first.return_value = result
    query.all.return_value = all_result or []
    query.count.return_value = 0
    query.update.return_value = update_result
    db.query.return_value = query
    return db


def _notification(user_id):
    return SimpleNamespace(
        id=uuid4(),
        user_id=user_id,
        title="Title",
        body="Body",
        data={},
        read_at=None,
        created_at=datetime.now(timezone.utc),
    )


def test_mark_read_only_finds_notifications_owned_by_the_user():
    user_id = uuid4()
    notification = _notification(user_id)
    db = _query_db(notification)

    result = notification_service.mark_notification_read(db, user_id, notification.id)

    assert result["id"] == notification.id
    assert notification.read_at is not None
    db.commit.assert_called_once()

    db.query.return_value.first.side_effect = [None]
    missing = notification_service.mark_notification_read(db, uuid4(), notification.id)
    assert missing is None


def test_mark_all_read_returns_updated_count():
    db = _query_db(update_result=3)

    assert notification_service.mark_all_notifications_read(db, uuid4()) == 3
    db.commit.assert_called_once()


def test_web_device_token_upsert_reactivates_existing_token_without_duplicate_insert():
    user_id = uuid4()
    device = SimpleNamespace(id=uuid4(), user_id=uuid4(), token="token", platform="android", is_active=False)
    db = _query_db(device)

    result = notification_service.register_device_token(db, user_id, DeviceTokenUpsert(token=" token ", platform="web"))

    assert result["token"] == "token"
    assert result["platform"] == "web"
    assert device.user_id == user_id
    assert device.is_active is True
    db.add.assert_not_called()


def test_push_delivery_failure_does_not_escape_business_flow(monkeypatch):
    db = _query_db(all_result=[SimpleNamespace(token="token")])
    notification = _notification(uuid4())
    monkeypatch.setattr(notification_delivery, "_send_push", MagicMock(side_effect=RuntimeError("FCM down")))

    notification_service.deliver_notification(db, notification)
