"""Permit ORM models — PermitRecord and PermitRequirementMatrix."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, Uuid

from models.base import Base


class PermitRecord(Base):
    """A permit found, required, or tracked for a project site."""

    __tablename__ = "permit_records"

    id               = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id       = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
                               nullable=False, index=True)
    permit_type      = Column(String(200), nullable=False, index=True)
    permit_category  = Column(String(50),  nullable=False, index=True)
    permit_number    = Column(String(200), nullable=True)
    issuing_agency   = Column(String(200), nullable=True)
    jurisdiction     = Column(String(200), nullable=True)
    status           = Column(String(50),  nullable=False, default="unknown", index=True)
    issue_date       = Column(DateTime,    nullable=True)
    expiration_date  = Column(DateTime,    nullable=True)
    description      = Column(Text,        nullable=True)
    conditions_text  = Column(Text,        nullable=True)
    source_url       = Column(String(500), nullable=True)
    confidence       = Column(String(20),  nullable=False, default="medium")
    flag_level       = Column(String(20),  nullable=False, default="info", index=True)
    raw_response_json = Column(Text,       nullable=True)
    query_date       = Column(DateTime,    nullable=False, default=datetime.utcnow)


class PermitRequirementMatrix(Base):
    """Permit applicability determination for a project site."""

    __tablename__ = "permit_requirement_matrix"

    id                    = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id            = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
                                    nullable=False, index=True)
    permit_type           = Column(String(200), nullable=False)
    required              = Column(String(20),  nullable=False, default="unknown")
    reason                = Column(Text,        nullable=True)
    estimated_timeline_weeks = Column(Integer,  nullable=True)
    estimated_cost_low    = Column(Float,       nullable=True)
    estimated_cost_high   = Column(Float,       nullable=True)
    issuing_agency        = Column(String(200), nullable=True)
    application_url       = Column(String(500), nullable=True)
    notes                 = Column(Text,        nullable=True)
    created_at            = Column(DateTime,    nullable=False, default=datetime.utcnow)
