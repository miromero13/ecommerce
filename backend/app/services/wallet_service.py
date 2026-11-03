"""CU19: Store wallet service: balance query, gift card redemptions, order debiting and ledger."""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.gift_card import GiftCard
from app.models.order import Order
from app.models.wallet import UserWallet, WalletTransaction
from app.schemas.order_schema import PaymentMethodEnum, PaymentStatusEnum


def get_or_create_wallet(db: Session, user_id: UUID) -> UserWallet:
    wallet = db.query(UserWallet).filter(UserWallet.user_id == user_id).first()
    if not wallet:
        wallet = UserWallet(user_id=user_id, balance=Decimal("0.00"), currency="BOB")
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    return wallet


def get_wallet_balance(db: Session, user_id: UUID) -> dict:
    wallet = get_or_create_wallet(db, user_id)
    return {
        "balance": float(wallet.balance),
        "currency": wallet.currency,
    }


def redeem_gift_card(db: Session, user_id: UUID, card_code: str) -> dict:
    code = card_code.strip().upper()
    now = datetime.now(timezone.utc)

    card = db.query(GiftCard).filter(GiftCard.code == code).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La tarjeta de regalo no existe o ha expirado",
        )

    if card.expires_at and card.expires_at < now:
        if card.status == "active":
            card.status = "expired"
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La tarjeta de regalo no existe o ha expirado",
        )

    if card.status != "active" or card.balance <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código de la tarjeta de regalo no es válido o ya fue canjeado",
        )

    # Concurrency safe lock on wallet
    wallet = (
        db.query(UserWallet)
        .filter(UserWallet.user_id == user_id)
        .with_for_update()
        .first()
    )
    if not wallet:
        wallet = UserWallet(user_id=user_id, balance=Decimal("0.00"), currency="BOB")
        db.add(wallet)
        db.flush()

    credited = card.balance
    wallet.balance += credited
    card.status = "redeemed"
    card.balance = Decimal("0.00")
    card.redeemed_at = now
    card.redeemed_by_id = user_id

    tx = WalletTransaction(
        wallet_id=wallet.id,
        type="credit",
        amount=credited,
        balance_after=wallet.balance,
        concept="gift_card_redeem",
        source_type="gift_card",
        source_id=card.id,
        description=f"Canje de Gift Card {card.code}",
        created_at=now,
    )
    db.add(tx)
    db.commit()
    db.refresh(wallet)

    return {
        "credited_amount": float(credited),
        "new_balance": float(wallet.balance),
    }


def convert_loyalty_points(db: Session, user_id: UUID, tenant_id: UUID, points: int) -> dict:
    from app.models.tenant import Tenant
    from app.services import loyalty_service

    if points <= 0 or points % 100 != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Los puntos se canjean en múltiplos de 100",
        )

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada",
        )

    wallet = (
        db.query(UserWallet)
        .filter(UserWallet.user_id == user_id)
        .with_for_update()
        .first()
    )
    if not wallet:
        wallet = UserWallet(user_id=user_id, balance=Decimal("0.00"), currency="BOB")
        db.add(wallet)
        db.flush()

    try:
        credited = loyalty_service.redeem(
            db,
            tenant_id=tenant_id,
            user_id=user_id,
            points=points,
            max_amount=Decimal("999999.00"),
            source_type="wallet",
            source_id=wallet.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    wallet.balance += credited
    now = datetime.now(timezone.utc)

    tx = WalletTransaction(
        wallet_id=wallet.id,
        type="credit",
        amount=credited,
        balance_after=wallet.balance,
        concept="points_conversion",
        source_type="loyalty",
        source_id=tenant_id,
        description=f"Conversión de {points} puntos de {tenant.name} a saldo",
        created_at=now,
    )
    db.add(tx)
    db.commit()
    db.refresh(wallet)

    return {
        "converted_points": points,
        "credited_amount": float(credited),
        "new_balance": float(wallet.balance),
        "tenant_name": tenant.name,
    }


def pay_order_with_wallet(db: Session, user_id: UUID, order_id: UUID, amount_to_debit: Decimal) -> None:
    from app.services.order_service import _consume_order

    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == user_id)
        .with_for_update()
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado",
        )
    if order.payment_status == PaymentStatusEnum.paid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El pedido ya se encuentra pagado",
        )

    wallet = (
        db.query(UserWallet)
        .filter(UserWallet.user_id == user_id)
        .with_for_update()
        .first()
    )
    debit_amount = Decimal(str(amount_to_debit)).quantize(Decimal("0.01"))
    if not wallet or wallet.balance < debit_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Saldo insuficiente en la billetera virtual para completar la operación",
        )

    now = datetime.now(timezone.utc)
    wallet.balance -= debit_amount
    order.payment_method = PaymentMethodEnum.wallet

    tx = WalletTransaction(
        wallet_id=wallet.id,
        type="debit",
        amount=debit_amount,
        balance_after=wallet.balance,
        concept="order_payment",
        source_type="order",
        source_id=order.id,
        description=f"Pago de pedido #{order.id}",
        created_at=now,
    )
    db.add(tx)
    _consume_order(db, order)
    db.commit()


def checkout_with_wallet(
    db: Session,
    user_id: UUID,
    pickup_branch_id: UUID,
    delivery: dict | None = None,
    points_to_redeem: int = 0,
) -> dict:
    from app.models.cart import Cart
    from app.schemas.enums import CartStatusEnum
    from app.services.order_service import (
        _consume_order,
        _locked_cart,
        _new_order,
        _serialize_order,
        expire_due_orders,
    )

    expire_due_orders(db)
    cart = _locked_cart(db, user_id)
    if cart.status == CartStatusEnum.checkout_pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El carrito tiene un checkout pendiente",
        )

    wallet = (
        db.query(UserWallet)
        .filter(UserWallet.user_id == user_id)
        .with_for_update()
        .first()
    )
    if not wallet:
        wallet = UserWallet(user_id=user_id, balance=Decimal("0.00"), currency="BOB")
        db.add(wallet)
        db.flush()

    order = _new_order(
        db,
        cart,
        user_id,
        pickup_branch_id,
        PaymentMethodEnum.wallet,
        delivery,
        points_to_redeem,
    )

    if wallet.balance < order.total_amount:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Saldo insuficiente en la billetera virtual para completar la operación",
        )

    now = datetime.now(timezone.utc)
    wallet.balance -= order.total_amount

    tx = WalletTransaction(
        wallet_id=wallet.id,
        type="debit",
        amount=order.total_amount,
        balance_after=wallet.balance,
        concept="order_payment",
        source_type="order",
        source_id=order.id,
        description=f"Pago con Billetera Digital - Pedido #{order.id}",
        created_at=now,
    )
    db.add(tx)
    _consume_order(db, order)
    db.commit()
    return _serialize_order(db, order).model_dump()


def credit_wallet(
    db: Session,
    user_id: UUID,
    amount: Decimal,
    concept: str,
    source_type: str | None = None,
    source_id: UUID | None = None,
    description: str | None = None,
) -> UserWallet:
    wallet = (
        db.query(UserWallet)
        .filter(UserWallet.user_id == user_id)
        .with_for_update()
        .first()
    )
    if not wallet:
        wallet = UserWallet(user_id=user_id, balance=Decimal("0.00"), currency="BOB")
        db.add(wallet)
        db.flush()

    credit_amount = Decimal(str(amount)).quantize(Decimal("0.01"))
    wallet.balance += credit_amount
    now = datetime.now(timezone.utc)

    tx = WalletTransaction(
        wallet_id=wallet.id,
        type="credit",
        amount=credit_amount,
        balance_after=wallet.balance,
        concept=concept,
        source_type=source_type,
        source_id=source_id,
        description=description or f"Crédito por {concept}",
        created_at=now,
    )
    db.add(tx)
    db.commit()
    db.refresh(wallet)
    return wallet


def list_transactions(db: Session, user_id: UUID) -> list[dict]:
    wallet = get_or_create_wallet(db, user_id)
    txs = (
        db.query(WalletTransaction)
        .filter(WalletTransaction.wallet_id == wallet.id)
        .order_by(WalletTransaction.created_at.desc())
        .all()
    )
    return [
        {
            "id": tx.id,
            "type": tx.type,
            "amount": float(tx.amount),
            "balance_after": float(tx.balance_after),
            "concept": tx.concept,
            "source_type": tx.source_type,
            "source_id": tx.source_id,
            "description": tx.description,
            "created_at": tx.created_at,
        }
        for tx in txs
    ]
