import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from app.routes import user_routes, auth, branch_routes, provider_routes, catalog_routes, garment_routes, inventory_routes, cart_routes, reservation_routes, order_routes, payment_routes, sales_routes, report_routes, dashboard_routes, promotion_routes, replenishment_routes, recommendation_routes, chatbot_routes, notification_routes, tenant_routes, subscription_routes, payout_routes, delivery_routes, rbac_routes, expert_replenishment_routes, rpa_ingest_routes, wishlist_routes, loyalty_routes, cash_session_routes
from app.core.error_handlers import register_error_handlers
from app.core.tenant_middleware import register_tenant_middleware
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


async def _expert_replenishment_loop() -> None:
    while True:
        await asyncio.sleep(21600)  # Every 6 hours
        db = SessionLocal()
        try:
            from app.services.expert_replenishment_service import run_auto_evaluation_all_tenants
            run_auto_evaluation_all_tenants(db)
        except Exception:
            db.rollback()
        finally:
            db.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(_expire_orders_loop())
    daily_task = asyncio.create_task(_daily_expiration_loop())
    replenishment_task = asyncio.create_task(_expert_replenishment_loop())
    try:
        yield
    finally:
        task.cancel()
        daily_task.cancel()
        replenishment_task.cancel()
        await asyncio.gather(task, daily_task, replenishment_task, return_exceptions=True)

app = FastAPI(title="ACI", lifespan=lifespan)

# Registered before CORS so CORS stays the outermost layer.
register_tenant_middleware(app)

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
api_router.include_router(garment_routes.router)
api_router.include_router(inventory_routes.router)
api_router.include_router(cart_routes.router)
api_router.include_router(reservation_routes.router)
api_router.include_router(order_routes.router)
api_router.include_router(payment_routes.router)
api_router.include_router(sales_routes.router)
api_router.include_router(report_routes.router)
api_router.include_router(dashboard_routes.router)
api_router.include_router(promotion_routes.router)
api_router.include_router(replenishment_routes.router)
api_router.include_router(recommendation_routes.router)
api_router.include_router(chatbot_routes.router)
api_router.include_router(notification_routes.router)
api_router.include_router(tenant_routes.router)
api_router.include_router(subscription_routes.router)
api_router.include_router(payout_routes.router)
api_router.include_router(delivery_routes.router)
api_router.include_router(rbac_routes.router)
api_router.include_router(expert_replenishment_routes.router)
api_router.include_router(rpa_ingest_routes.router)
api_router.include_router(wishlist_routes.router)
api_router.include_router(loyalty_routes.router)
api_router.include_router(cash_session_routes.router)

app.include_router(api_router)

register_error_handlers(app)
