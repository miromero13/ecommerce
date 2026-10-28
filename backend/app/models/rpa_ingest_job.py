"""CU10 RPA ingestion: a supplier document read by AI into a stock income draft."""
import uuid

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.core.database import Base


class RpaIngestJob(Base):
    __tablename__ = "rpa_ingest_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(80), nullable=False)
    status = Column(String(12), nullable=False, default="processing")  # processing | completed | failed | committed
    # [{sku, name, size, color, quantity, unit_cost, variant_id, recognized}]
    extracted_items = Column(JSON, nullable=False, default=list)
    error_message = Column(Text, nullable=True)
    target_branch_id = Column(UUID(as_uuid=True), ForeignKey("branches.id"), nullable=True)
    committed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    committed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
