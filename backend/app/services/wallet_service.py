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


# [CU19 - Secuencia: Pasos 1.2, 1.8, 2.8, 2.14, 3.10, 3.16, 4.22] wallet_routes invoca get_or_create_wallet(user_id) sobre la entidad BilleteraUsuario
# [CU19 - Secuencia: Pasos 1.3, 1.9, 2.9, 2.15, 3.11, 3.17, 4.23] BilleteraUsuario retorna get_or_create_wallet(user_id): UserWallet a wallet_routes
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


# [CU19 - Secuencia: Paso 2.2] wallet_routes invoca redeem_gift_card(user_id, card_code) sobre la entidad BilleteraUsuario
# [CU19 - Secuencia: Paso 2.3] BilleteraUsuario retorna redeem_gift_card(user_id, card_code): dict a wallet_routes
# [CU19 - Secuencia: Paso 2.4] wallet_routes invoca redeem_gift_card(user_id, card_code) sobre la entidad MovimientoBilletera
# [CU19 - Secuencia: Paso 2.5] MovimientoBilletera retorna redeem_gift_card(user_id, card_code): dict a wallet_routes
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


# [CU19 - Secuencia: Paso 3.2] wallet_routes invoca convert_loyalty_points(user_id, tenant_id, points) sobre la entidad BilleteraUsuario
# [CU19 - Secuencia: Paso 3.3] BilleteraUsuario retorna convert_loyalty_points(user_id, tenant_id, points): dict a wallet_routes
# [CU19 - Secuencia: Paso 3.4] wallet_routes invoca convert_loyalty_points(user_id, tenant_id, points) sobre la entidad MovimientoBilletera
# [CU19 - Secuencia: Paso 3.5] MovimientoBilletera retorna convert_loyalty_points(user_id, tenant_id, points): dict a wallet_routes
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


# [CU19 - Secuencia: Paso 4.2] wallet_routes invoca checkout_with_wallet(user_id, pickup_branch_id, delivery, points_to_redeem) sobre la entidad BilleteraUsuario
# [CU19 - Secuencia: Paso 4.3] BilleteraUsuario retorna checkout_with_wallet(user_id, pickup_branch_id, delivery, points_to_redeem): dict a wallet_routes
# [CU19 - Secuencia: Paso 4.4] wallet_routes invoca checkout_with_wallet(user_id, pickup_branch_id, delivery, points_to_redeem) sobre la entidad MovimientoBilletera
# [CU19 - Secuencia: Paso 4.5] MovimientoBilletera retorna checkout_with_wallet(user_id, pickup_branch_id, delivery, points_to_redeem): dict a wallet_routes
def checkout_with_wallet(
    db: Session,
    user_id: UUID,
    pickup_branch_id: UUID,
    delivery: dict | None = None,
    points_to_redeem: int = 0,
) -> dict:
    from app.models.cart import Cart
    from app.schemas.cart_schema import CartStatusEnum
    from app.services.cart_service import CART_LOCKED_MESSAGE, pending_order
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
        if pending_order(db, user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=CART_LOCKED_MESSAGE,
            )
        cart.status = CartStatusEnum.active  # stale lock without a pending order


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
    from app.services.notification_service import notify_order_event

    notify_order_event(db, order.id, order.user_id, "paid")  # same notice a card payment gets
    return _serialize_order(db, order).model_dump()


# [CU30 - Secuencia: Paso 5.13] offline_routes invoca credit_wallet(user_id, amount, concept, source_type, source_id, description, commit) sobre la entidad BilleteraUsuario
# [CU30 - Secuencia: Paso 5.14] BilleteraUsuario retorna credit_wallet(user_id, amount, concept, source_type, source_id, description, commit): UserWallet a offline_routes
# [CU30 - Secuencia: Paso 5.15] offline_routes invoca credit_wallet(user_id, amount, concept, source_type, source_id, description, commit) sobre la entidad MovimientoBilletera
# [CU30 - Secuencia: Paso 5.16] MovimientoBilletera retorna credit_wallet(user_id, amount, concept, source_type, source_id, description, commit): UserWallet a offline_routes
def credit_wallet(
    db: Session,
    user_id: UUID,
    amount: Decimal,
    concept: str,
    source_type: str | None = None,
    source_id: UUID | None = None,
    description: str | None = None,
    commit: bool = True,
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
    if not commit:  # caller owns the transaction (e.g. CU30 conflict resolution)
        db.flush()
        return wallet
    db.commit()
    db.refresh(wallet)
    return wallet


# [CU19 - Secuencia: Pasos 1.6, 2.12, 3.14] wallet_routes invoca list_transactions(user_id) sobre la entidad MovimientoBilletera
# [CU19 - Secuencia: Pasos 1.7, 2.13, 3.15] MovimientoBilletera retorna list_transactions(user_id): list[dict] a wallet_routes
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
