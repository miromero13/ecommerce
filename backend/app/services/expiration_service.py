from app.core.database import SessionLocal
from app.services.order_service import expire_due_orders
from app.services.payout_service import run_daily_settlements
from app.services.reservation_service import expire_due_reservations, expire_transferred_reservations


def run_daily_expiration() -> None:
    db = SessionLocal()
    try:
        expire_due_reservations(db)
        expire_due_orders(db)
        expire_transferred_reservations(db)
        # Runs right after midnight: yesterday's online payments become one settlement per company.
        run_daily_settlements(db)
    finally:
        db.close()
