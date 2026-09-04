from sqlalchemy import Column, String, Text, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
import uuid


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=True, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False, index=True)
    season_id = Column(UUID(as_uuid=True), ForeignKey("seasons.id"), nullable=True, index=True)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id"), nullable=True, index=True)

    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
