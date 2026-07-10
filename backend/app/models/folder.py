from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Folder(Base):
    __tablename__ = "folders"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    parent_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("folders.id"), nullable=True)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, default=None)
    scope: Mapped[str] = mapped_column(String(16), default="personal")
    team_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
    children: Mapped[list["Folder"]] = relationship("Folder", back_populates="parent", remote_side="Folder.id")
    parent: Mapped[Optional["Folder"]] = relationship("Folder", back_populates="children", remote_side="Folder.parent_id")


# ── File ──
