from enum import Enum

class RolEnum(str, Enum):
    superadministrador = "superadministrador"
    administrador = "administrador"
    cliente = "cliente"
    proveedor = "proveedor"
    encargado = "encargado"
    cajero = "cajero"
    delivery = "delivery"

class GenderEnum(str, Enum):
    masculino = "masculino"
    femenino = "femenino"


class ProviderStatusEnum(str, Enum):
    active = "active"
    suspended = "suspended"


class TenantStatusEnum(str, Enum):
    active = "active"
    trial = "trial"
    suspended = "suspended"


class SubscriptionStatusEnum(str, Enum):
    active = "active"
    trialing = "trialing"
    past_due = "past_due"
    canceled = "canceled"


class BillingCycleEnum(str, Enum):
    monthly = "monthly"
    yearly = "yearly"


class SubscriptionPaymentMethodEnum(str, Enum):
    simulated_card = "simulated_card"
    cash = "cash"
    stripe = "stripe"

