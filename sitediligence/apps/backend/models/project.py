"""SQLAlchemy ORM models for Project and Site."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    status = Column(String(50), default="active")
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    metadata_ = Column("metadata", JSON, default=dict)

    sites = relationship("Site", back_populates="project", cascade="all, delete-orphan")


class Site(Base):
    __tablename__ = "sites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    status = Column(String(50), default="pending")
    address = Column(JSON, default=dict)
    coordinates = Column(JSON, nullable=True)   # [lon, lat]
    bbox = Column(JSON, nullable=True)          # [minLon, minLat, maxLon, maxLat]
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(UUID(as_uuid=True), nullable=False)
    metadata_ = Column("metadata", JSON, default=dict)

    project = relationship("Project", back_populates="sites")
