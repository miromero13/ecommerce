from sqlalchemy import Column, String, Text, Numeric, Enum as SQLAlchemyEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.schemas.catalog_enums import ProductStatusEnum
import uuid


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    sku = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    status = Column(SQLAlchemyEnum(ProductStatusEnum), nullable=False, default=ProductStatusEnum.pending)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=True, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False, index=True)
    size_id = Column(UUID(as_uuid=True), ForeignKey("sizes.id"), nullable=True, index=True)
    color_id = Column(UUID(as_uuid=True), ForeignKey("colors.id"), nullable=True, index=True)
    season_id = Column(UUID(as_uuid=True), ForeignKey("seasons.id"), nullable=True, index=True)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id"), nullable=True, index=True)
