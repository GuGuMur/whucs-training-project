from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


TeamMessageType = Literal["text", "file", "system"]


class TeamMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    receiver_id: int | None = None
    message_type: TeamMessageType = "text"


class TeamMessageItem(BaseModel):
    id: str
    team_id: str
    sender_id: int
    sender_name: str
    receiver_id: int | None = None
    content: str
    message_type: TeamMessageType
    created_at: datetime


class TeamMessageListResponse(BaseModel):
    items: list[TeamMessageItem]
    total: int


class TeamSummary(BaseModel):
    id: str
    name: str
    description: str = ""
    role: str
    member_count: int
    unread_count: int
    root_folder_id: str | None = None


class TeamListResponse(BaseModel):
    items: list[TeamSummary]


TeamRole = Literal["owner", "admin", "member", "guest"]
TeamMemberStatus = Literal["active", "invited", "removed"]
TeamInviteStatus = Literal["pending", "accepted", "revoked", "expired"]


class TeamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=500)


class TeamUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=500)


class TeamInviteCreate(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    role: TeamRole = "member"


class TeamMemberJoin(BaseModel):
    invite_token: str = Field(min_length=1)


class TeamMemberUpdate(BaseModel):
    role: TeamRole


class TeamMemberPublic(BaseModel):
    id: str
    team_id: str
    user_id: int
    username: str
    email: str
    display_name: str
    role: TeamRole
    status: TeamMemberStatus
    joined_at: datetime


class TeamInvitePublic(BaseModel):
    id: str
    team_id: str
    email: str
    role: TeamRole
    status: TeamInviteStatus
    token: str
    created_at: datetime
    expires_at: datetime


class TeamDetail(BaseModel):
    id: str
    name: str
    description: str
    role: TeamRole
    member_count: int
    unread_count: int
    root_folder: "FolderItem"
    members: list[TeamMemberPublic]
    invites: list[TeamInvitePublic]

# Rebuild models with forward references
from app.domain.folder import FolderItem
TeamDetail.model_rebuild()
