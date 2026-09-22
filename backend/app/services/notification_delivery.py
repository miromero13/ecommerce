from pathlib import Path
import logging
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.inventory import Inventory
from app.models.notification import DeviceToken, Notification
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.user import User
from app.schemas.enums import RolEnum


logger = logging.getLogger(__name__)


def _firebase_app():
    path_value = settings.firebase_service_account_path
    if not path_value:
        logger.warning(
            "Firebase push delivery disabled: set FIREBASE_SERVICE_ACCOUNT_PATH "
            "or FIREBASE_SERVICE_ACCOUNT_FILE"
        )
        return None

    path = Path(path_value)
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.is_file():
        logger.warning("Firebase push delivery disabled: service-account path does not exist")
        return None

    try:
        import firebase_admin
        from firebase_admin import credentials

        try:
            return firebase_admin.get_app()
        except ValueError:
            return firebase_admin.initialize_app(credentials.Certificate(str(path)))
    except Exception:
        logger.exception("Could not initialize Firebase Admin SDK")
        return None


def _send_push(token: str, title: str, body: str, data: dict[str, str]) -> None:
    app = _firebase_app()
    if app is None:
        return

    from firebase_admin import messaging

    messaging.send(
        messaging.Message(
            token=token,
            notification=messaging.Notification(title=title, body=body),
            data=data,
        ),
        app=app,
    )


def deliver_notification(db: Session, notification: Notification) -> None:
    tokens = (
        db.query(DeviceToken)
        .filter(DeviceToken.user_id == notification.user_id, DeviceToken.is_active.is_(True))
        .all()
    )
    data = {key: str(value) for key, value in (notification.data or {}).items()}
    for device in tokens:
        try:
            _send_push(device.token, notification.title, notification.body, data)
        except Exception:
            logger.exception("FCM delivery failed for notification %s", notification.id)


def notify_reservation_event(db: Session, reservation_id: UUID, user_id: UUID, status: str) -> None:
    labels = {
        "pending": ("Reserva creada", "Tu reserva fue creada y está pendiente de confirmación."),
        "confirmed": ("Reserva confirmada", "La sucursal confirmó tu reserva."),
        "attended": ("Reserva atendida", "Tu visita fue registrada en la sucursal."),
        "purchase_pending": ("Compra pendiente", "Elige si deseas comprar las prendas de tu reserva."),
        "sold": ("Reserva vendida", "La compra de tu reserva fue confirmada."),
        "not_sold": ("Reserva cerrada", "La reserva fue cerrada sin compra."),
        "cancelled": ("Reserva cancelada", "Tu reserva fue cancelada."),
        "expired": ("Reserva expirada", "Tu reserva venció y liberó el stock."),
    }
    title, body = labels.get(status, ("Actualización de reserva", "Tu reserva fue actualizada."))
    from app.services.notification_service import create_notification

    create_notification(
        db,
        user_id,
        title,
        body,
        {"destination": "reservations", "reservation_id": str(reservation_id), "status": status},
        f"reservation:{reservation_id}:{status}",
    )


def notify_order_event(db: Session, order_id: UUID, user_id: UUID, status: str) -> None:
    labels = {
        "pending": ("Pedido creado", "Tu pedido fue creado y está pendiente de pago."),
        "paid": ("Pago confirmado", "El pago de tu pedido fue confirmado."),
        "ready_for_pickup": ("Pedido listo", "Tu pedido está listo para recoger en la sucursal."),
        "collected": ("Pedido entregado", "Tu pedido fue entregado."),
        "failed": ("Pago fallido", "No se pudo completar el pago de tu pedido."),
        "cancelled": ("Pedido cancelado", "Tu pedido fue cancelado."),
        "expired": ("Pedido expirado", "El tiempo de pago o retiro de tu pedido terminó."),
    }
    title, body = labels.get(status, ("Actualización de pedido", "Tu pedido fue actualizado."))
    from app.services.notification_service import create_notification

    create_notification(
        db,
        user_id,
        title,
        body,
        {"destination": "orders", "order_id": str(order_id), "status": status},
        f"order:{order_id}:{status}",
    )


def notify_low_stock(db: Session, inventory: Inventory) -> None:
    available = max((inventory.quantity or 0) - (inventory.reserved_quantity or 0), 0)
    if available > (inventory.minimum_stock or 0):
        return

    variant = db.query(ProductVariant).filter(ProductVariant.id == inventory.variant_id).first()
    product_name = "una variante"
    if variant:
        product_name = db.query(Product.name).filter(Product.id == variant.product_id).scalar() or product_name

    users = (
        db.query(User)
        .filter(
            or_(
                User.rol == RolEnum.administrador,
                (User.rol == RolEnum.encargado) & (User.branch_id == inventory.branch_id),
            ),
            User.is_active.is_(True),
        )
        .all()
    )
    from app.services.notification_service import create_notification

    for user in users:
        create_notification(
            db,
            user.id,
            "Stock bajo",
            f"{product_name} tiene {available} unidades disponibles.",
            {"destination": "inventory", "variant_id": str(inventory.variant_id), "branch_id": str(inventory.branch_id)},
            f"low-stock:{user.id}:{inventory.variant_id}:{inventory.branch_id}:{available}",
        )
