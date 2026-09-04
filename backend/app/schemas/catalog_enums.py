from enum import Enum


class ProductStatusEnum(str, Enum):
    pending = "pending"
    active = "active"
    inactive = "inactive"
