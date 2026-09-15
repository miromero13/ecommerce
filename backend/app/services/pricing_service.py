from decimal import Decimal, ROUND_HALF_UP


def discounted_price(price, discount_type=None, discount_value=None) -> Decimal:
    original = Decimal(str(price or 0))
    value = Decimal(str(discount_value or 0))
    if not discount_type or value <= 0:
        return original.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if discount_type == "percentage":
        value = min(value, Decimal("100"))
        discount = original * value / Decimal("100")
    else:
        discount = value
    return max(original - discount, Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def discount_amount(price, discount_type=None, discount_value=None) -> Decimal:
    original = Decimal(str(price or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return max(original - discounted_price(original, discount_type, discount_value), Decimal("0.00"))
