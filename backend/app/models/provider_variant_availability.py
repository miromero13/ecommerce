import uuid

from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ProviderVariantAvailability(Base):
    __tablename__ = "provider_variant_availability"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    provider_id = Column(UUID(as_uuid=True), ForeignKey("providers.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id = Column(UUID(as_uuid=True), ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("provider_id", "variant_id", name="uq_provider_variant_availability"),
        CheckConstraint("quantity >= 0", name="ck_provider_variant_availability_quantity_non_negative"),
    )
