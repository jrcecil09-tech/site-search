"""User and TeamMember ORM models."""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Uuid
from sqlalchemy.orm import relationship

from models.base import Base


class User(Base):
    __tablename__ = "users"

    id               = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email            = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password  = Column(String(255), nullable=False)
    full_name        = Column(String(255), nullable=False, default="")
    role             = Column(String(50),  nullable=False, default="user")   # user | admin
    plan             = Column(String(50),  nullable=False, default="free")   # free | pro | enterprise
    storage_quota_gb = Column(Float, nullable=False, default=5.0)
    storage_used_gb  = Column(Float, nullable=False, default=0.0)
    created_at       = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login       = Column(DateTime, nullable=True)

    projects = relationship(
        "Project", back_populates="owner", foreign_keys="Project.created_by",
        cascade="all, delete-orphan",
    )
    memberships = relationship("TeamMember", back_populates="user", cascade="all, delete-orphan")
    observations = relationship("Observation", back_populates="user")
    audit_logs   = relationship("AuditLog", back_populates="user")


class TeamMember(Base):
    __tablename__ = "team_members"

    project_id = Column(Uuid(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"),
                        primary_key=True)
    user_id    = Column(Uuid(as_uuid=True), ForeignKey("users.id",    ondelete="CASCADE"),
                        primary_key=True)
    role       = Column(String(50), nullable=False, default="viewer")  # owner|admin|editor|viewer

    project = relationship("Project",    back_populates="members")
    user    = relationship("User",       back_populates="memberships")
