"""SQLAlchemy ORM models for Observation and ObservationAttachment."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from models.project import Base


class Observation(Base):
    __tablename__ = "observations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    category_id = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    status = Column(String(50), default="draft")
    severity = Column(String(50), default="info")
    coordinates = Column(JSON, nullable=True)   # [lon, lat]
    tags = Column(JSON, default=list)
    custom_fields = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)

    attachments = relationship(
        "ObservationAttachment", back_populates="observation", cascade="all, delete-orphan"
    )


class ObservationAttachment(Base):
    __tablename__ = "observation_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    observation_id = Column(UUID(as_uuid=True), ForeignKey("observations.id"), nullable=False)
    type = Column(String(50), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Float, nullable=False)
    content_type = Column(String(100), nullable=False)
    storage_key = Column(String(500), nullable=False)
    captured_at = Column(DateTime, nullable=True)
    capture_location = Column(JSON, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    uploaded_by = Column(UUID(as_uuid=True), nullable=False)

    observation = relationship("Observation", back_populates="attachments")
