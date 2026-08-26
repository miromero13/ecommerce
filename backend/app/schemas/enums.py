from enum import Enum

class RolEnum(str, Enum):
    administrador = "administrador"
    cliente = "cliente"
    delivery = "delivery"

class GenderEnum(str, Enum):
    masculino = "masculino"
    femenino = "femenino"
