from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class FolderItem(BaseModel):
    id: str
    name: str
    parent_id: str | None = None
    scope: Literal["personal", "team"]
    permission: str
    team_id: str | None = None
    children: list["FolderItem"] = Field(default_factory=list)


class FolderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    parent_id: str | None = None
    scope: Literal["personal", "team"] = "personal"


class FolderUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    parent_id: str | None = None


class FolderTreeResponse(BaseModel):
    items: list[FolderItem]
