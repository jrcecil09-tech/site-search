"""Observation and Photo ORM models."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import relationship

from models.base import Base


class Observation(Base):
    __tablename__ = "observations"

    id               = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id       = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
                               nullable=False, index=True)
    user_id          = Column(Uuid(as_uuid=True), ForeignKey("users.id"),
                               nullable=False, index=True)
    latitude         = Column(Float,       nullable=True)
    longitude        = Column(Float,       nullable=True)
    category         = Column(String(100), nullable=False, default="general")
    severity         = Column(String(50),  nullable=False, default="info")
    description      = Column(Text,        nullable=True)
    photo_paths_json = Column(Text,        nullable=True)  # JSON array of storage paths
    created_at       = Column(DateTime, nullable=False, default=datetime.utcnow)
    synced_at        = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="observations")
    user    = relationship("User",    back_populates="observations")


class Photo(Base):
    __tablename__ = "photos"

    id         = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
                         nullable=False, index=True)
    filepath   = Column(String(500), nullable=False)
    latitude   = Column(Float,       nullable=True)
    longitude  = Column(Float,       nullable=True)
    bearing    = Column(Float,       nullable=True)   # compass heading degrees
    altitude   = Column(Float,       nullable=True)   # meters above sea level
    category   = Column(String(100), nullable=True)
    notes      = Column(Text,        nullable=True)
    timestamp  = Column(DateTime,    nullable=True)   # EXIF capture time
    synced_at  = Column(DateTime,    nullable=True)

    project = relationship("Project", back_populates="photos")
