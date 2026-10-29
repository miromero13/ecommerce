"""CU17 loyalty program, kept per company (approved rules):
- earn 1 point per 10 Bs paid for products (shipping does not count);
- redeem 10 points = 1 Bs, never more than the amount to pay;
- tier by lifetime points: Bronce < 500, Plata 500-1499, Oro >= 1500.
Callers own the transaction: these helpers flush but never commit."""
from decimal import Decimal, ROUND_DOWN
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.loyalty import LoyaltyAccount, LoyaltyLedger
from app.models.tenant import Tenant

BS_PER_EARNED_POINT = Decimal("10")
POINTS_PER_BS = 10
TIERS = ((1500, "Oro"), (500, "Plata"), (0, "Bronce"))


def tier_for(lifetime_points: int) -> str:
    return next(name for threshold, name in TIERS if lifetime_points >= threshold)


def points_for(amount: Decimal) -> int:
    return int((Decimal(str(amount)) / BS_PER_EARNED_POINT).to_integral_value(rounding=ROUND_DOWN))


def points_value(points: int) -> Decimal:
    return (Decimal(points) / POINTS_PER_BS).quantize(Decimal("0.01"))


def _account(db: Session, tenant_id: UUID, user_id: UUID) -> LoyaltyAccount:
    account = (db.query(LoyaltyAccount)
               .filter(LoyaltyAccount.tenant_id == tenant_id, LoyaltyAccount.user_id == user_id)
               .with_for_update().first())
    if not account:
        account = LoyaltyAccount(tenant_id=tenant_id, user_id=user_id, points_balance=0, lifetime_points=0)
        db.add(account)
        db.flush()
    return account


def _already(db: Session, source_type: str, source_id: UUID, type_: str) -> LoyaltyLedger | None:
    return db.query(LoyaltyLedger).filter(LoyaltyLedger.source_type == source_type,
                                          LoyaltyLedger.source_id == source_id, LoyaltyLedger.type == type_).first()


def earn(db: Session, tenant_id: UUID, user_id: UUID, amount: Decimal, source_type: str, source_id: UUID) -> int:
    points = points_for(amount)
    if points <= 0 or _already(db, source_type, source_id, "earn"):
        return 0
    account = _account(db, tenant_id, user_id)
    account.points_balance += points
    account.lifetime_points += points
    db.add(LoyaltyLedger(account_id=account.id, type="earn", points=points, source_type=source_type, source_id=source_id))
    db.flush()
    return points


def redeem(db: Session, tenant_id: UUID, user_id: UUID, points: int, max_amount: Decimal,
           source_type: str, source_id: UUID) -> Decimal:
    """Spend points on a purchase; returns the discount in money."""
    if points <= 0:
        return Decimal("0.00")
    if points % POINTS_PER_BS:
        raise ValueError(f"Los puntos se canjean en múltiplos de {POINTS_PER_BS}")
    account = _account(db, tenant_id, user_id)
    if account.points_balance < points:
        raise ValueError(f"Puntos insuficientes: tienes {account.points_balance} puntos en esta empresa")
    discount = points_value(points)
    if discount > Decimal(str(max_amount)):
        raise ValueError("Los puntos canjeados superan el monto a pagar")
    account.points_balance -= points
    db.add(LoyaltyLedger(account_id=account.id, type="redeem", points=points, source_type=source_type, source_id=source_id))
    db.flush()
    return discount


def refund_redeem(db: Session, source_type: str, source_id: UUID) -> None:
    """Give back the points of a purchase that was cancelled or expired before paying."""
    spent = _already(db, source_type, source_id, "redeem")
    if not spent or _already(db, source_type, source_id, "refund"):
        return
    account = db.query(LoyaltyAccount).filter(LoyaltyAccount.id == spent.account_id).with_for_update().one()
    account.points_balance += spent.points
    db.add(LoyaltyLedger(account_id=account.id, type="refund", points=spent.points, source_type=source_type, source_id=source_id))
    db.flush()


def _serialize(account: LoyaltyAccount | None, tenant: Tenant) -> dict:
    balance = account.points_balance if account else 0
    lifetime = account.lifetime_points if account else 0
    return {"tenant_id": tenant.id, "tenant_name": tenant.name, "points_balance": balance,
            "lifetime_points": lifetime, "tier": tier_for(lifetime), "balance_value": points_value(balance)}


def list_balances(db: Session, user_id: UUID) -> list[dict]:
    rows = (db.query(LoyaltyAccount, Tenant).join(Tenant, Tenant.id == LoyaltyAccount.tenant_id)
            .filter(LoyaltyAccount.user_id == user_id).order_by(Tenant.name).all())
    return [_serialize(account, tenant) for account, tenant in rows]


def balance_for(db: Session, tenant_id: UUID, user_id: UUID) -> dict:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).one()
    account = db.query(LoyaltyAccount).filter(LoyaltyAccount.tenant_id == tenant_id, LoyaltyAccount.user_id == user_id).first()
    return _serialize(account, tenant)


def list_transactions(db: Session, user_id: UUID, limit: int = 100) -> list[dict]:
    rows = (db.query(LoyaltyLedger, Tenant.name)
            .join(LoyaltyAccount, LoyaltyAccount.id == LoyaltyLedger.account_id)
            .join(Tenant, Tenant.id == LoyaltyAccount.tenant_id)
            .filter(LoyaltyAccount.user_id == user_id)
            .order_by(LoyaltyLedger.created_at.desc()).limit(limit).all())
    return [{"id": row.id, "tenant_name": name, "type": row.type, "points": row.points,
             "source_type": row.source_type, "source_id": row.source_id, "created_at": row.created_at}
            for row, name in rows]
