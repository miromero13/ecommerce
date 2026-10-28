"""1P-CU18 cash drawer. Rules:
- each cashier opens their own session, always in their own branch and company; drawers of different branches never mix;
- selling (cash or QR) and charging a web order in cash require the cashier's open session;
- a cash payment records what the customer handed over and the change returned;
- deposits and withdrawals need a reason; a withdrawal cannot take more cash than the drawer holds;
- expected cash = opening + cash sales + cash order collections + deposits - withdrawals (QR never enters the drawer);
- closing stores the counted cash and the difference (counted - expected).
Helpers that take part in a sale or an order flush but never commit: the caller owns the transaction."""
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.cash_session import CashMovement, CashSession
from app.models.user import User

CENT = Decimal("0.01")
NO_OPEN_SESSION = "Abre tu caja para registrar ventas y cobros"
LOCAL_TZ = timezone(timedelta(hours=-4))  # America/La_Paz


class CashSessionConflict(Exception):
    pass


def _money(value) -> Decimal:
    return Decimal(str(value)).quantize(CENT)


def get_open_session(db: Session, cashier_id: UUID, lock: bool = False) -> CashSession | None:
    query = db.query(CashSession).filter(CashSession.cashier_id == cashier_id, CashSession.status == "open")
    return (query.with_for_update() if lock else query).first()


def require_open_session(db: Session, cashier_id: UUID, branch_id: UUID | None, tenant_id: UUID | None) -> CashSession:
    session = get_open_session(db, cashier_id, lock=True)
    if session is None:
        raise ValueError(NO_OPEN_SESSION)
    if session.branch_id != branch_id or session.tenant_id != tenant_id:
        # The cashier was moved to another branch with a drawer still open: never mix both branches' cash.
        raise ValueError("Tu caja abierta pertenece a otra sucursal: ciérrala antes de operar en esta")
    return session


def expected_cash(session: CashSession) -> Decimal:
    total = _money(session.opening_amount)
    for movement in session.movements:
        if movement.type == "withdrawal":
            total -= movement.amount
        elif movement.method == "cash":
            total += movement.amount
    return _money(total)


def _record_payment(db: Session, session: CashSession, type_: str, method: str, total: Decimal,
                    cash_received, source_id: UUID) -> CashMovement:
    total = _money(total)
    received = change = None
    if method == "cash":
        received = total if cash_received is None else _money(cash_received)  # None: exact amount, no change
        if received < total:
            raise ValueError(f"El monto recibido ({received} Bs.) es menor al total a cobrar ({total} Bs.)")
        change = received - total
    movement = CashMovement(session_id=session.id, type=type_, method=method, amount=total,
                            cash_received=received, change_given=change, source_id=source_id)
    db.add(movement)
    db.flush()
    db.refresh(session)  # keep session.movements in sync for expected_cash
    return movement


def record_sale(db: Session, session: CashSession, sale, cash_received=None) -> CashMovement:
    method = "qr" if getattr(sale.payment_method, "value", sale.payment_method) == "qr" else "cash"
    return _record_payment(db, session, "sale", method, sale.total_amount, cash_received if method == "cash" else None, sale.id)


def record_order_collection(db: Session, session: CashSession, order, cash_received=None) -> CashMovement:
    return _record_payment(db, session, "order", "cash", order.total_amount, cash_received, order.id)


def open_session(db: Session, cashier: User, opening_amount) -> dict:
    if cashier.branch_id is None or cashier.tenant_id is None:
        raise ValueError("Necesitas una sucursal asignada para abrir caja")
    if get_open_session(db, cashier.id):
        raise CashSessionConflict("Ya tienes una caja abierta: ciérrala antes de abrir otra")
    session = CashSession(tenant_id=cashier.tenant_id, branch_id=cashier.branch_id, cashier_id=cashier.id,
                          status="open", opening_amount=_money(opening_amount))
    db.add(session)
    try:
        db.commit()
    except IntegrityError as exc:  # two simultaneous openings by the same cashier
        db.rollback()
        raise CashSessionConflict("Ya tienes una caja abierta: ciérrala antes de abrir otra") from exc
    db.refresh(session)
    return serialize(db, session)


def add_manual_movement(db: Session, cashier: User, type_: str, amount, reason: str) -> dict:
    session = require_open_session(db, cashier.id, cashier.branch_id, cashier.tenant_id)
    amount = _money(amount)
    if type_ == "withdrawal" and amount > expected_cash(session):
        raise ValueError(f"No puedes retirar {amount} Bs.: la caja tiene {expected_cash(session)} Bs.")
    db.add(CashMovement(session_id=session.id, type=type_, method="cash", amount=amount, reason=reason.strip()))
    db.commit()
    db.refresh(session)
    return serialize(db, session)


def close_session(db: Session, cashier: User, counted_amount, note: str | None) -> dict:
    session = require_open_session(db, cashier.id, cashier.branch_id, cashier.tenant_id)
    session.expected_amount = expected_cash(session)
    session.counted_amount = _money(counted_amount)
    session.difference = session.counted_amount - session.expected_amount
    session.closing_note = (note or "").strip() or None
    session.status = "closed"
    session.closed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    return serialize(db, session)


def _totals(session: CashSession) -> dict:
    def total(**match) -> Decimal:
        return _money(sum((m.amount for m in session.movements
                           if all(getattr(m, k) == v for k, v in match.items())), Decimal("0")))
    return {
        "cash_sales": total(type="sale", method="cash"),
        "qr_sales": total(type="sale", method="qr"),
        "order_collections": total(type="order"),
        "deposits": total(type="deposit"),
        "withdrawals": total(type="withdrawal"),
        "change_given": _money(sum((m.change_given or 0 for m in session.movements), Decimal("0"))),
        "sales_count": sum(1 for m in session.movements if m.type == "sale"),
    }


def serialize(db: Session, session: CashSession, with_movements: bool = True) -> dict:
    from app.models.branch import Branch

    cashier_name = db.query(User.name).filter(User.id == session.cashier_id).scalar()
    branch_name = db.query(Branch.name).filter(Branch.id == session.branch_id).scalar()
    data = {
        "id": session.id, "status": session.status, "tenant_id": session.tenant_id,
        "branch_id": session.branch_id, "branch_name": branch_name,
        "cashier_id": session.cashier_id, "cashier_name": cashier_name,
        "opening_amount": _money(session.opening_amount), "opened_at": session.opened_at,
        # While open, the expected cash is live; once closed, the stored figure is the official one.
        "expected_amount": session.expected_amount if session.status == "closed" else expected_cash(session),
        "counted_amount": session.counted_amount, "difference": session.difference,
        "closing_note": session.closing_note, "closed_at": session.closed_at,
        **_totals(session),
    }
    if with_movements:
        data["movements"] = [{
            "id": m.id, "type": m.type, "method": m.method, "amount": m.amount,
            "cash_received": m.cash_received, "change_given": m.change_given,
            "source_id": m.source_id, "reason": m.reason, "created_at": m.created_at,
        } for m in session.movements]
    return data


def list_sessions(db: Session, tenant_id: UUID, branch_id: UUID | None = None, cashier_id: UUID | None = None,
                  day: date | None = None) -> list[dict]:
    query = db.query(CashSession).filter(CashSession.tenant_id == tenant_id)
    if branch_id is not None:
        query = query.filter(CashSession.branch_id == branch_id)
    if cashier_id is not None:
        query = query.filter(CashSession.cashier_id == cashier_id)
    if day is not None:
        # ponytail: Bolivia's fixed UTC-4 (no daylight saving); use the company's own zone if it operates elsewhere.
        start = datetime.combine(day, time.min, tzinfo=LOCAL_TZ)
        query = query.filter(CashSession.opened_at >= start, CashSession.opened_at < start + timedelta(days=1))
    sessions = query.order_by(CashSession.opened_at.desc()).limit(200).all()
    return [serialize(db, session, with_movements=False) for session in sessions]


def get_session(db: Session, session_id: UUID, tenant_id: UUID, branch_id: UUID | None = None,
                cashier_id: UUID | None = None) -> dict | None:
    query = db.query(CashSession).filter(CashSession.id == session_id, CashSession.tenant_id == tenant_id)
    if branch_id is not None:
        query = query.filter(CashSession.branch_id == branch_id)
    if cashier_id is not None:
        query = query.filter(CashSession.cashier_id == cashier_id)
    session = query.first()
    return serialize(db, session) if session else None
