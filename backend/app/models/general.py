from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    type: Mapped[str] = mapped_column(String(32))  # annotation/invite/mention/system/workflow
    title: Mapped[str] = mapped_column(String(256))
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    target_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    team_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


# ── Knowledge Base ──
class PermissionRule(Base):
    __tablename__ = "permission_rules"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    action: Mapped[str] = mapped_column(String(32))  # read/write/admin
    effect: Mapped[str] = mapped_column(String(8), default="allow")  # allow/deny
    resource_type: Mapped[str] = mapped_column(String(32))  # file/folder
    resource_id: Mapped[str] = mapped_column(String(64))
    subject_type: Mapped[str] = mapped_column(String(32))  # user/role/team
    subject_id: Mapped[str] = mapped_column(String(64))
    priority: Mapped[int] = mapped_column(Integer, default=0)
    inherit: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


# ── Share Link ──
class ShareLink(Base):
    __tablename__ = "share_links"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    file_id: Mapped[str] = mapped_column(String(64), ForeignKey("files.id"))
    token: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    download_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    download_count: Mapped[int] = mapped_column(Integer, default=0)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


# ── File Annotation ──
class FileAnnotation(Base):
    __tablename__ = "file_annotations"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    file_id: Mapped[str] = mapped_column(String(64), ForeignKey("files.id"), index=True)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    author_name: Mapped[str] = mapped_column(String(128), default="")
    content: Mapped[str] = mapped_column(Text)
    parent_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # for replies
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


# ── Other ──
class DeletedFile(Base):
    __tablename__ = "deleted_files"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    file_id: Mapped[str] = mapped_column(String(64), ForeignKey("files.id"))
    deleted_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    deleted_by: Mapped[str] = mapped_column(String(128), default="system")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor: Mapped[str] = mapped_column(String(128))
    action: Mapped[str] = mapped_column(String(128))
    resource_type: Mapped[str] = mapped_column(String(64))
    resource_name: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(128), index=True)
    role: Mapped[str] = mapped_column(String(16))  # user/assistant
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)


class MultipartUpload(Base):
    __tablename__ = "multipart_uploads"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    filename: Mapped[str] = mapped_column(String(512))
    folder_id: Mapped[str] = mapped_column(String(64))
    size: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64))
    chunk_size: Mapped[int] = mapped_column(Integer)
    total_chunks: Mapped[int] = mapped_column(Integer)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
