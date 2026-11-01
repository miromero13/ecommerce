from pathlib import Path
import logging
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.inventory import Inventory
from app.models.notification import DeviceToken, Notification
from app.models.order import Order
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.reservation import Reservation
from app.models.rma import RmaRequest
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


# Same channel the mobile app creates; Android shows high-importance channels as heads-up banners.
ANDROID_CHANNEL_ID = "foreground_notifications"


def _send_push(token: str, title: str, body: str, data: dict[str, str]) -> bool:
    """Returns False when Firebase is not configured; raises when FCM rejects the message."""
    app = _firebase_app()
    if app is None:
        return False

    from firebase_admin import messaging

    messaging.send(
        messaging.Message(
            token=token,
            notification=messaging.Notification(title=title, body=body),
            data=data,
            android=messaging.AndroidConfig(
                priority="high",
                notification=messaging.AndroidNotification(channel_id=ANDROID_CHANNEL_ID),
            ),
        ),
        app=app,
    )
    return True


def deliver_notification(db: Session, notification: Notification) -> None:
    tokens = (
        db.query(DeviceToken)
        .filter(DeviceToken.user_id == notification.user_id, DeviceToken.is_active.is_(True))
        .all()
    )
    if not tokens:
        logger.warning(
            "Push skipped for notification %s: user %s has no registered device "
            "(open the mobile app or enable push on the web while logged in)",
            notification.id, notification.user_id,
        )
        return
    data = {key: str(value) for key, value in (notification.data or {}).items()}
    for device in tokens:
        try:
            _send_push(device.token, notification.title, notification.body, data)
        except Exception as error:
            # Uninstalled app / expired token: stop retrying it on every notification.
            if type(error).__name__ in ("UnregisteredError", "SenderIdMismatchError"):
                device.is_active = False
                db.commit()
                logger.warning("Deactivated invalid %s token for user %s: %s", device.platform, device.user_id, error)
            else:
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
    if status == "pending":
        branch_id = db.query(Reservation.branch_id).filter(Reservation.id == reservation_id).scalar()
        _notify_branch_managers(
            db,
            branch_id,
            "Nueva reserva",
            "Se creó una nueva reserva para tu sucursal.",
            {"destination": "reservations", "reservation_id": str(reservation_id), "status": status},
            f"reservation:{reservation_id}:{status}",
        )


def notify_order_event(db: Session, order_id: UUID, user_id: UUID, status: str) -> None:
    order = db.query(Order.total_amount, Order.currency).filter(Order.id == order_id).first()
    # Short, human reference so the customer knows which purchase the notice is about.
    ref = f"#{str(order_id)[:8].upper()}"
    amount = f"{order.total_amount} {(order.currency or '').upper()}" if order else ""
    total = f" por {amount}" if amount else ""
    labels = {
        "pending": (f"Pedido {ref} creado", f"Recibimos tu pedido{total}. Completa el pago para reservarlo."),
        "paid": (f"¡Compra confirmada! {ref}", f"Pagaste {amount or 'tu pedido'}. Te avisaremos cuando esté listo para retirar."),
        "ready_for_pickup": (f"Pedido {ref} listo", "Ya puedes recogerlo en la sucursal. Muestra tu código de retiro."),
        "collected": (f"Pedido {ref} entregado", "Gracias por tu compra."),
        "failed": (f"Pago rechazado {ref}", f"No se pudo cobrar{total}. No se te cobró nada; vuelve a intentar la compra."),
        "cancelled": (f"Pedido {ref} cancelado", "Tu pedido fue cancelado y las prendas se liberaron."),
        "expired": (f"Pedido {ref} vencido", "Se terminó el tiempo de pago o retiro y el pedido se cerró."),
    }
    title, body = labels.get(status, (f"Pedido {ref} actualizado", "Revisa el estado en Mis pedidos."))
    from app.services.notification_service import create_notification

    create_notification(
        db,
        user_id,
        title,
        body,
        {"destination": "orders", "order_id": str(order_id), "status": status},
        f"order:{order_id}:{status}",
    )
    if status == "pending":
        branch_id = db.query(Order.pickup_branch_id).filter(Order.id == order_id).scalar()
        _notify_branch_managers(
            db,
            branch_id,
            "Nuevo pedido",
            "Se creó un nuevo pedido para tu sucursal.",
            {"destination": "orders", "order_id": str(order_id), "status": status},
            f"order:{order_id}:{status}",
        )


def _notify_rma_event(db: Session, rma_id: UUID, status: str, item_id: UUID | None = None) -> None:
    """Return requests (CU21): tells the customer each step and the store staff about new requests."""
    rma = db.query(RmaRequest).filter(RmaRequest.id == rma_id).first()
    if rma is None:
        return
    from app.services.notification_service import create_notification

    data = {"destination": "rma", "rma_id": str(rma.id), "rma_number": rma.rma_number}
    if status == "requested":
        create_notification(
            db, rma.user_id, f"Solicitud de devolución {rma.rma_number} recibida",
            "La tienda revisará las prendas y te avisaremos el resultado.",
            data, f"rma:{rma.id}:requested",
        )
        staff = db.query(User.id).filter(
            User.rol.in_([RolEnum.administrador, RolEnum.encargado]), User.tenant_id == rma.tenant_id,
            User.is_active.is_(True),
        ).all()
        for (staff_id,) in staff:
            create_notification(
                db, staff_id, f"Nueva devolución {rma.rma_number}",
                "Un cliente solicitó una devolución. Revísala en Devoluciones.",
                data, f"rma:{rma.id}:requested:staff:{staff_id}",
            )
    elif status == "rejected":
        create_notification(
            db, rma.user_id, f"Devolución {rma.rma_number} rechazada",
            "Una prenda no cumplió las condiciones de devolución. Revisa el detalle en Mis devoluciones.",
            data, f"rma:{rma.id}:item:{item_id}:rejected",
        )


def _notify_branch_managers(
    db: Session,
    branch_id: UUID | None,
    title: str,
    body: str,
    data: dict[str, str],
    dedupe_prefix: str,
) -> None:
    if branch_id is None:
        return
    managers = (
        db.query(User)
        .filter(
            User.rol == RolEnum.encargado,
            User.branch_id == branch_id,
            User.is_active.is_(True),
        )
        .all()
    )
    from app.services.notification_service import create_notification

    for manager in managers:
        create_notification(
            db,
            manager.id,
            title,
            body,
            data,
            f"{dedupe_prefix}:manager:{manager.id}",
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
            User.tenant_id == inventory.tenant_id,
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

    # Reactively trigger Expert Replenishment evaluation so admins receive immediate transfer suggestions
    try:
        from app.services.expert_replenishment_service import evaluate_on_low_stock
        evaluate_on_low_stock(db, inventory)
    except Exception:
        logger.exception("Could not evaluate expert replenishment on low stock for inventory %s", inventory.id)

