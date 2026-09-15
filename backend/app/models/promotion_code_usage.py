import uuid

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class PromotionCodeUsage(Base):
    __tablename__ = "promotion_code_usages"
    __table_args__ = (UniqueConstraint("promotion_code_id", "user_id", name="uq_promotion_code_usage_user"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    promotion_code_id = Column(UUID(as_uuid=True), ForeignKey("promotion_codes.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    used_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    promotion_code = relationship("PromotionCode", back_populates="usages")
