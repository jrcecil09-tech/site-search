"""AuditLog ORM model."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import relationship

from models.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id           = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id   = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL"),
                           nullable=True, index=True)
    user_id      = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
                           nullable=True, index=True)
    action       = Column(String(100), nullable=False, index=True)
    details_json = Column(Text,        nullable=True)  # JSON with extra context
    timestamp    = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    project = relationship("Project", back_populates="audit_logs")
    user    = relationship("User",    back_populates="audit_logs")
