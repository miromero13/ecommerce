import uuid

from sqlalchemy import Column, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserBodyProfile(Base):
    __tablename__ = "user_body_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    top_size = Column(String(32), nullable=True)
    bottom_size = Column(String(32), nullable=True)
    shoe_size = Column(String(32), nullable=True)
    body_shape = Column(String(64), nullable=True)
    fit_preference = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="body_profile")

    __table_args__ = (UniqueConstraint("user_id", name="uq_user_body_profiles_user_id"),)
