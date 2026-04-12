"""StorageObject ORM model (file metadata)."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import UUID

from models.base import Base


class StorageObject(Base):
    __tablename__ = "storage_objects"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id      = Column(UUID(as_uuid=True), nullable=True, index=True)
    key             = Column(String(500), nullable=False, unique=True)
    bucket          = Column(String(255), nullable=True)
    content_type    = Column(String(100), nullable=False)
    size_bytes      = Column(Float,       nullable=False)
    storage_backend = Column(String(50),  nullable=False)
    url             = Column(Text,        nullable=True)
    uploaded_at     = Column(DateTime, nullable=False, default=datetime.utcnow)
    uploaded_by     = Column(UUID(as_uuid=True), nullable=True)
    metadata_json   = Column(Text, nullable=True)
