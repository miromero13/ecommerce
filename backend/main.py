import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from app.routes import user_routes, auth, branch_routes, provider_routes, catalog_routes, inventory_routes, cart_routes, reservation_routes, order_routes, payment_routes, sales_routes, report_routes, dashboard_routes, promotion_routes
from app.core.error_handlers import register_error_handlers
from app.core.database import SessionLocal
from app.services.expiration_service import run_daily_expiration
from app.services.order_service import expire_due_orders


async def _expire_orders_loop() -> None:
    while True:
        await asyncio.sleep(60)
        db = SessionLocal()
        try:
            expire_due_orders(db)
        except Exception:
            db.rollback()
        finally:
            db.close()


async def _daily_expiration_loop() -> None:
    while True:
        now = datetime.now()
        next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        await asyncio.sleep(max((next_midnight - now).total_seconds(), 1))
        try:
            run_daily_expiration()
        except Exception:
            pass


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(_expire_orders_loop())
    daily_task = asyncio.create_task(_daily_expiration_loop())
    try:
        yield
    finally:
        task.cancel()
        daily_task.cancel()
        await asyncio.gather(task, daily_task, return_exceptions=True)

app = FastAPI(title="ACI", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
api_router = APIRouter(prefix="/api")
api_router.include_router(user_routes.router)
api_router.include_router(auth.router)  
api_router.include_router(branch_routes.router)
api_router.include_router(provider_routes.router)
api_router.include_router(catalog_routes.router)
api_router.include_router(inventory_routes.router)
api_router.include_router(cart_routes.router)
api_router.include_router(reservation_routes.router)
api_router.include_router(order_routes.router)
api_router.include_router(payment_routes.router)
api_router.include_router(sales_routes.router)
api_router.include_router(report_routes.router)
api_router.include_router(dashboard_routes.router)
api_router.include_router(promotion_routes.router)

app.include_router(api_router)

register_error_handlers(app)
