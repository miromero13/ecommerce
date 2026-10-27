"""CU20 delivery. Drivers belong to the platform (no company, no branch) and take
ready delivery orders from every company; the customer proves receipt with a PIN."""
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from math import asin, cos, radians, sin, sqrt
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.branch import Branch
from app.models.order import Order
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.enums import RolEnum
from app.schemas.order_schema import FulfillmentStatusEnum, PaymentMethodEnum, PaymentStatusEnum

CENT = Decimal("0.01")
EARTH_RADIUS_KM = 6371.0
MINUTES_PER_KM = 4  # urban motorcycle average, plus preparation
PREPARATION_MINUTES = 15


class OutOfCoverage(ValueError):
    pass


def distance_km(lat1, lon1, lat2, lon2) -> float:
    """Haversine great-circle distance."""
    lat1, lon1, lat2, lon2 = map(lambda value: radians(float(value)), (lat1, lon1, lat2, lon2))
    a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * EARTH_RADIUS_KM * asin(sqrt(a))


def shipping_quote(db: Session, branch_id: UUID, latitude, longitude) -> dict:
    branch = db.query(Branch).filter(Branch.id == branch_id, Branch.is_active.is_(True)).first()
    if not branch:
        raise LookupError("Sucursal no encontrada")
    if branch.latitude is None or branch.longitude is None:
        raise ValueError("La sucursal no tiene ubicación registrada para envíos")
    km = Decimal(str(distance_km(branch.latitude, branch.longitude, latitude, longitude))).quantize(CENT)
    if km > Decimal(str(settings.delivery_max_km)):
        raise OutOfCoverage("La dirección de entrega se encuentra fuera del radio de cobertura")
    cost = (Decimal(str(settings.delivery_base_fee)) + Decimal(str(settings.delivery_fee_per_km)) * km)
    return {"distance_km": km, "shipping_cost": cost.quantize(CENT, rounding=ROUND_HALF_UP),
            "estimated_minutes": PREPARATION_MINUTES + int(km * MINUTES_PER_KM)}


def _summary(db: Session, order: Order, include_pin: bool = False) -> dict:
    branch = db.query(Branch).filter(Branch.id == order.pickup_branch_id).first()
    data = {
        "order_id": order.id,
        "tenant_name": db.query(Tenant.name).filter(Tenant.id == order.tenant_id).scalar(),
        "branch_name": branch.name if branch else None,
        "branch_city": branch.city if branch else None,
        "client_name": db.query(User.name).filter(User.id == order.user_id).scalar(),
        "address": order.delivery_address,
        "reference": order.delivery_reference,
        "latitude": order.delivery_latitude,
        "longitude": order.delivery_longitude,
        "distance_km": order.delivery_distance_km,
        "shipping_cost": order.shipping_cost,
        "total_amount": order.total_amount,
        "currency": order.currency,
        # Cash on delivery: the driver must collect this amount for the platform.
        "collect_on_delivery": order.payment_method == PaymentMethodEnum.cash,
        "status": order.fulfillment_status,
        "driver_name": db.query(User.name).filter(User.id == order.delivery_driver_id).scalar()
        if order.delivery_driver_id else None,
        "delivered_at": order.delivered_at,
        "created_at": order.created_at,
    }
    if include_pin:
        data["delivery_pin"] = order.delivery_pin
    return data


def _delivery_orders(db: Session):
    return db.query(Order).filter(Order.fulfillment_type == "delivery")


def list_available(db: Session) -> list[dict]:
    """Ready delivery orders of every company that no driver has taken yet."""
    orders = (_delivery_orders(db).filter(Order.fulfillment_status == FulfillmentStatusEnum.ready_for_pickup,
                                          Order.delivery_driver_id.is_(None))
              .order_by(Order.created_at.asc()).all())
    return [_summary(db, order) for order in orders]


def claim_order(db: Session, order_id: UUID, driver_id: UUID) -> dict:
    order = _delivery_orders(db).filter(Order.id == order_id).with_for_update().first()
    if not order:
        raise LookupError("Pedido no encontrado")
    if order.delivery_driver_id and order.delivery_driver_id != driver_id:
        raise RuntimeError("Otro repartidor ya tomó este pedido")
    if order.fulfillment_status != FulfillmentStatusEnum.ready_for_pickup:
        raise ValueError("El pedido aún no está listo para despacho")
    order.delivery_driver_id = driver_id
    order.fulfillment_status = FulfillmentStatusEnum.in_transit
    db.commit()
    return _summary(db, order)


def driver_route(db: Session, driver_id: UUID) -> list[dict]:
    orders = (_delivery_orders(db).filter(Order.delivery_driver_id == driver_id)
              .order_by(Order.delivered_at.is_not(None), Order.created_at.desc()).limit(50).all())
    return [_summary(db, order) for order in orders]


def confirm_delivery(db: Session, order_id: UUID, security_pin: str, driver_id: UUID) -> dict:
    from app.services.order_service import _consume_order
    from app.services.payout_service import record_payment

    order = _delivery_orders(db).filter(Order.id == order_id, Order.delivery_driver_id == driver_id).with_for_update().first()
    if not order:
        raise LookupError("Pedido no encontrado en tu hoja de ruta")
    if order.fulfillment_status != FulfillmentStatusEnum.in_transit:
        raise ValueError("La orden no se encuentra en estado en tránsito para ser entregada")
    if order.delivery_pin != security_pin:
        raise ValueError("El código PIN de seguridad es incorrecto")
    if order.payment_method == PaymentMethodEnum.cash and order.payment_status == PaymentStatusEnum.pending:
        # The driver collects the cash for the platform; it reaches the company in the daily settlement.
        _consume_order(db, order, driver_id)
        record_payment(db, order.tenant_id, "order", order.id, "cash",
                       order.total_amount - order.shipping_cost, order.currency)
    order.fulfillment_status = FulfillmentStatusEnum.delivered
    order.delivered_at = datetime.now(timezone.utc)
    db.commit()
    return {"order_id": order.id, "delivered_at": order.delivered_at}


def customer_deliveries(db: Session, user_id: UUID) -> list[dict]:
    orders = _delivery_orders(db).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()
    return [_summary(db, order, include_pin=True) for order in orders]


def list_drivers(db: Session) -> list[User]:
    return db.query(User).filter(User.rol == RolEnum.delivery).order_by(User.name.asc()).all()


def create_driver(db: Session, payload) -> User:
    from app.services.user_service import ensure_email_available, normalize_email, pwd_context

    ensure_email_available(db, payload.email)
    driver = User(name=payload.name, email=normalize_email(payload.email), gender=payload.gender,
                  rol=RolEnum.delivery, hashed_password=pwd_context.hash(payload.password),
                  tenant_id=None, branch_id=None, is_active=True)
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return driver
