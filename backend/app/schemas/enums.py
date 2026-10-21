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
