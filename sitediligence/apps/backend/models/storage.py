"""SQLAlchemy ORM model for StorageObject metadata."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, JSON, String
from sqlalchemy.dialects.postgresql import UUID

from models.project import Base


class StorageObject(Base):
    __tablename__ = "storage_objects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    key = Column(String(500), nullable=False, unique=True)
    bucket = Column(String(255), nullable=True)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Float, nullable=False)
    storage_backend = Column(String(50), nullable=False)
    url = Column(String(1000), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(UUID(as_uuid=True), nullable=False)
    metadata_ = Column("metadata", JSON, default=dict)
