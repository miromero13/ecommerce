from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_roles
from app.core.database import get_db
from app.schemas.delivery_schema import ConfirmDeliveryRequest, DeliveryQuoteRequest, DriverCreate
from app.schemas.enums import RolEnum
from app.schemas.user_schema import UserRead
from app.services.delivery_service import (
    OutOfCoverage, claim_order, confirm_delivery, create_driver, customer_deliveries, driver_route,
    list_available, list_drivers, shipping_quote,
)
from app.utils.response import response


router = APIRouter(prefix="/delivery", tags=["Delivery"])
CLIENT = require_roles(RolEnum.cliente)
DRIVER = require_roles(RolEnum.delivery)
SUPERADMIN = require_roles(RolEnum.superadministrador)


def _run(action):
    try:
        return action()
    except OutOfCoverage as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/quotes")
def quote_route(payload: DeliveryQuoteRequest, db: Session = Depends(get_db), _: dict = Depends(CLIENT)):
    data = _run(lambda: shipping_quote(db, payload.branch_id, payload.latitude, payload.longitude))
    return response(status_code=200, message="Cotización de envío calculada", data=data)


@router.get("/my-orders")
def my_orders_route(db: Session = Depends(get_db), user: dict = Depends(CLIENT)):
    return response(status_code=200, message="Envíos obtenidos", data=customer_deliveries(db, UUID(user["sub"])))


@router.get("/available")
def available_route(db: Session = Depends(get_db), _: dict = Depends(DRIVER)):
    return response(status_code=200, message="Pedidos disponibles para despacho", data=list_available(db))


@router.post("/orders/{order_id}/claim")
def claim_route(order_id: UUID, db: Session = Depends(get_db), driver: dict = Depends(DRIVER)):
    data = _run(lambda: claim_order(db, order_id, UUID(driver["sub"])))
    return response(status_code=200, message="Pedido asignado a tu hoja de ruta", data=data)


@router.get("/routes")
def routes_route(db: Session = Depends(get_db), driver: dict = Depends(DRIVER)):
    return response(status_code=200, message="Hoja de ruta del día obtenida", data=driver_route(db, UUID(driver["sub"])))


@router.post("/confirm-delivery")
def confirm_route(payload: ConfirmDeliveryRequest, db: Session = Depends(get_db), driver: dict = Depends(DRIVER)):
    data = _run(lambda: confirm_delivery(db, payload.order_id, payload.security_pin, UUID(driver["sub"])))
    return response(status_code=200, message="Entrega confirmada y registrada exitosamente", data=data)


@router.get("/drivers")
def drivers_route(db: Session = Depends(get_db), _: dict = Depends(SUPERADMIN)):
    return response(status_code=200, message="Repartidores obtenidos",
                    data=[UserRead.model_validate(d).model_dump() for d in list_drivers(db)])


@router.post("/drivers", status_code=status.HTTP_201_CREATED)
def create_driver_route(payload: DriverCreate, db: Session = Depends(get_db), _: dict = Depends(SUPERADMIN)):
    driver = _run(lambda: create_driver(db, payload))
    return response(status_code=201, message="Repartidor registrado exitosamente",
                    data=UserRead.model_validate(driver).model_dump())
