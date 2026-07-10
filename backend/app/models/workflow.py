from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Workflow(Base):
    __tablename__ = "workflows"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text, default="")
    trigger: Mapped[str] = mapped_column(String(256), default="manual")
    version: Mapped[str] = mapped_column(String(16), default="0.1.0")
    status: Mapped[str] = mapped_column(String(16), default="draft")  # draft/published/archived
    nodes: Mapped[str] = mapped_column(Text, default="[]")  # JSON
    edges: Mapped[str] = mapped_column(Text, default="[]")  # JSON
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)


# ── Permission Rule ──
