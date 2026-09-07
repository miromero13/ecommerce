import uuid

from sqlalchemy import Column, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    sale_id = Column(UUID(as_uuid=True), ForeignKey("sales.id"), nullable=False, index=True)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    line_total = Column(Numeric(10, 2), nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    product_name = Column(String, nullable=False)
    variant_sku = Column(String, nullable=False)
    size_id = Column(UUID(as_uuid=True), nullable=True)
    color_id = Column(UUID(as_uuid=True), nullable=True)
    image_url = Column(String, nullable=True)
    image_public_id = Column(String, nullable=True)

    sale = relationship("Sale", back_populates="items")
    variant = relationship("ProductVariant")

    __table_args__ = (UniqueConstraint("sale_id", "variant_id", name="uq_sale_item_sale_variant"),)
