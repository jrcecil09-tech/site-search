"""Project ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import relationship

from models.base import Base


class Project(Base):
    __tablename__ = "projects"

    id                 = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name               = Column(String(255), nullable=False)
    project_number     = Column(String(100), nullable=True, index=True)
    client_name        = Column(String(255), nullable=True)
    site_address       = Column(Text,        nullable=True)
    state              = Column(String(2),   nullable=True, index=True)   # FIPS state code
    county_fips        = Column(String(5),   nullable=True, index=True)   # 5-digit FIPS
    latitude           = Column(Float,       nullable=True)
    longitude          = Column(Float,       nullable=True)
    acreage            = Column(Float,       nullable=True)
    status             = Column(String(50),  nullable=False, default="draft")
    due_date           = Column(DateTime,    nullable=True)
    boundary_geojson   = Column(Text,        nullable=True)  # GeoJSON string
    query_results_json = Column(Text,        nullable=True)  # Cached query results
    storage_tier       = Column(String(50),  nullable=False, default="local")
    storage_path       = Column(String(500), nullable=True)
    created_by         = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at         = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at         = Column(DateTime, nullable=False, default=datetime.utcnow,
                                onupdate=datetime.utcnow)

    owner        = relationship("User",        back_populates="projects",
                                foreign_keys=[created_by])
    members      = relationship("TeamMember",  back_populates="project",
                                cascade="all, delete-orphan")
    observations = relationship("Observation", back_populates="project",
                                cascade="all, delete-orphan")
    photos       = relationship("Photo",       back_populates="project",
                                cascade="all, delete-orphan")
    audit_logs   = relationship("AuditLog",    back_populates="project",
                                cascade="all, delete-orphan")
