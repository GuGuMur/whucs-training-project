from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.v1.auth import current_user
from app.domain.schemas import (
    FolderItem,
    TeamCreate,
    TeamUpdate,
    TeamDetail,
    TeamInviteCreate,
    TeamInvitePublic,
    TeamListResponse,
    TeamMemberJoin,
    TeamMemberPublic,
    TeamMemberUpdate,
    TeamMessageCreate,
    TeamMessageItem,
    TeamMessageListResponse,
    UserPublic,
)
from app.services.workspace import workspace_service

router = APIRouter()


@router.post("/teams", response_model=TeamDetail, status_code=status.HTTP_201_CREATED)
def create_team(payload: TeamCreate, user: Annotated[UserPublic, Depends(current_user)]) -> TeamDetail:
    return workspace_service.create_team(payload, user)


@router.get("/teams", response_model=TeamListResponse)
def teams(user: Annotated[UserPublic, Depends(current_user)]) -> TeamListResponse:
    return TeamListResponse(items=workspace_service.list_teams(user))


@router.get("/teams/{team_id}", response_model=TeamDetail)
def team_detail(team_id: str, user: Annotated[UserPublic, Depends(current_user)]) -> TeamDetail:
    return workspace_service.get_team_detail(team_id, user)


@router.get("/teams/{team_id}/messages", response_model=TeamMessageListResponse)
def team_messages(team_id: str, user: Annotated[UserPublic, Depends(current_user)]) -> TeamMessageListResponse:
    items = workspace_service.list_team_messages(team_id, user)
    return TeamMessageListResponse(items=items, total=len(items))


@router.post("/teams/{team_id}/messages", response_model=TeamMessageItem, status_code=status.HTTP_201_CREATED)
def create_team_message(
    team_id: str,
    payload: TeamMessageCreate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> TeamMessageItem:
    return workspace_service.create_team_message(team_id, payload, user)


@router.post("/teams/{team_id}/invites", response_model=TeamInvitePublic, status_code=status.HTTP_201_CREATED)
def create_team_invite(
    team_id: str,
    payload: TeamInviteCreate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> TeamInvitePublic:
    return workspace_service.create_team_invite(team_id, payload, user)


@router.post("/teams/{team_id}/members", response_model=TeamMemberPublic, status_code=status.HTTP_201_CREATED)
def join_team(
    team_id: str,
    payload: TeamMemberJoin,
    user: Annotated[UserPublic, Depends(current_user)],
) -> TeamMemberPublic:
    return workspace_service.join_team(team_id, payload, user)


@router.patch("/teams/{team_id}/members/{member_id}", response_model=TeamMemberPublic)
def update_team_member(
    team_id: str,
    member_id: str,
    payload: TeamMemberUpdate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> TeamMemberPublic:
    return workspace_service.update_team_member(team_id, member_id, payload, user)


@router.delete("/teams/{team_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_team_member(
    team_id: str,
    member_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
) -> Response:
    workspace_service.remove_team_member(team_id, member_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/teams/{team_id}", response_model=TeamDetail)
def update_team(
    team_id: str,
    payload: TeamUpdate,
    user: Annotated[UserPublic, Depends(current_user)],
) -> TeamDetail:
    return workspace_service.update_team(team_id, payload, user)


@router.delete("/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(team_id: str, user: Annotated[UserPublic, Depends(current_user)]) -> Response:
    workspace_service.delete_team(team_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/teams/{team_id}/members/me", status_code=status.HTTP_204_NO_CONTENT)
def leave_team(team_id: str, user: Annotated[UserPublic, Depends(current_user)]) -> Response:
    workspace_service.leave_team(team_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
