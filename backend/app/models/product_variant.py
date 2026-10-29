from sqlalchemy import Column, String, Enum as SQLAlchemyEnum, ForeignKey, UniqueConstraint, Numeric, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.schemas.catalog_enums import ProductStatusEnum
import uuid


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False, index=True)
    sku = Column(String, nullable=False, unique=True, index=True)
    price = Column(Numeric(10, 2), nullable=False)
    size_id = Column(UUID(as_uuid=True), ForeignKey("sizes.id"), nullable=True, index=True)
    color_id = Column(UUID(as_uuid=True), ForeignKey("colors.id"), nullable=True, index=True)
    image_url = Column(String, nullable=True)
    image_public_id = Column(String, nullable=True)
    # CU5: transparent cut-out of the garment for the fitting rooms; the catalog shows image_url.
    try_on_image_url = Column(String, nullable=True)
    garment_points = Column(JSON, nullable=True)
    status = Column(SQLAlchemyEnum(ProductStatusEnum), nullable=False, default=ProductStatusEnum.pending)

    product = relationship("Product", back_populates="variants")
    inventory = relationship("Inventory", back_populates="variant", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("product_id", "size_id", "color_id", name="uq_product_variant_combo"),
    )
