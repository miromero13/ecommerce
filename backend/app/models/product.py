from sqlalchemy import Column, String, Text, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
import uuid


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id"), nullable=True, index=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False, index=True)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id"), nullable=True, index=True)
    discount_type = Column(String(20), nullable=True)
    discount_value = Column(Numeric(10, 2), nullable=True)
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")


from app.models.provider import Provider  # noqa: E402, F401
from app.models.category import Category  # noqa: E402, F401
from app.models.collection import Collection  # noqa: E402, F401
from app.models.season import Season  # noqa: E402, F401
