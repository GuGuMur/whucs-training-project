from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class File(Base):
    __tablename__ = "files"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(512))
    folder_id: Mapped[str] = mapped_column(String(64), ForeignKey("folders.id"))
    type: Mapped[str] = mapped_column(String(32))
    size: Mapped[int] = mapped_column(Integer, default=0)
    sha256: Mapped[str] = mapped_column(String(64))
    content_type: Mapped[str] = mapped_column(String(128), default="application/octet-stream")
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, default=None)
    team_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    permission_scope: Mapped[str] = mapped_column(String(16), default="个人")
    parse_status: Mapped[str] = mapped_column(String(16), default="queued")
    tags: Mapped[str] = mapped_column(String(1024), default="")
    knowledge_base_ids: Mapped[str] = mapped_column(String(512), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
    created_by: Mapped[str] = mapped_column(String(128), default="system")


# ── FileVersion ──
class FileVersion(Base):
    __tablename__ = "file_versions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    file_id: Mapped[str] = mapped_column(String(64), ForeignKey("files.id"), index=True)
    version_no: Mapped[int] = mapped_column(Integer, default=1)
    name: Mapped[str] = mapped_column(String(512))
    size: Mapped[int] = mapped_column(Integer, default=0)
    sha256: Mapped[str] = mapped_column(String(64))
    content_key: Mapped[str] = mapped_column(String(256), default="")  # S3 key for file content
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    created_by: Mapped[str] = mapped_column(String(128), default="system")


# ── Team ──
