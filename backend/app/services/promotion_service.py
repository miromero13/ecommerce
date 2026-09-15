from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.models.promotion_code import PromotionCode
from app.models.promotion_code_usage import PromotionCodeUsage
from app.schemas.promotion_schema import PromotionCodeCreate, PromotionDiscountType


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _is_valid(code: PromotionCode, now: datetime | None = None) -> bool:
    now = now or _now()
    return code.is_active and (code.valid_from is None or code.valid_from <= now) and (code.valid_until is None or now < code.valid_until)


def get_code(db: Session, code: str) -> PromotionCode | None:
    return db.query(PromotionCode).filter(PromotionCode.code == code.strip().upper()).first()


def create_code(db: Session, payload: PromotionCodeCreate, creator_id: UUID) -> PromotionCode:
    code = PromotionCode(**payload.model_dump(exclude={"discount_type"}), created_by=creator_id, discount_type=payload.discount_type.value)
    db.add(code)
    try:
        db.commit()
        db.refresh(code)
        return code
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("El código promocional ya existe") from exc


def list_codes(db: Session, branch_id: UUID | None = None):
    query = db.query(PromotionCode).order_by(PromotionCode.created_at.desc())
    if branch_id is not None:
        query = query.filter(PromotionCode.branch_id == branch_id)
    return query.all()


def validate_for_user(db: Session, code_value: str, user_id: UUID, branch_id: UUID | None = None) -> PromotionCode:
    code = get_code(db, code_value)
    if not code or not _is_valid(code):
        raise ValueError("El código promocional no existe, está inactivo o fuera de vigencia")
    if code.branch_id is not None and branch_id is not None and code.branch_id != branch_id:
        raise ValueError("El código promocional no aplica a esta sucursal")
    if db.query(PromotionCodeUsage).filter(PromotionCodeUsage.promotion_code_id == code.id, PromotionCodeUsage.user_id == user_id).first():
        raise ValueError("Ya utilizaste este código promocional")
    return code


def cart_has_product_discount(db: Session, cart_id: UUID) -> bool:
    return db.query(CartItem.id).join(ProductVariant, ProductVariant.id == CartItem.variant_id).join(Product, Product.id == ProductVariant.product_id).filter(
        CartItem.cart_id == cart_id,
        Product.discount_type.isnot(None),
        Product.discount_value > 0,
    ).first() is not None


def calculate_discount(code: PromotionCode, subtotal: Decimal) -> Decimal:
    value = Decimal(str(code.discount_value))
    subtotal = max(Decimal(str(subtotal)), Decimal("0.00"))
    if code.discount_type == PromotionDiscountType.percentage.value:
        amount = subtotal * value / Decimal("100")
    else:
        if value > subtotal:
            raise ValueError("El descuento fijo no puede superar el subtotal")
        amount = value
    return min(amount, subtotal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def add_usage(db: Session, code_id: UUID, user_id: UUID) -> None:
    db.add(PromotionCodeUsage(promotion_code_id=code_id, user_id=user_id))
