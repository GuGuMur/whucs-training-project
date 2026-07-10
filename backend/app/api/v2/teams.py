from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.api.v2._deps import get_svc, current_user
from app.domain.schemas import (
    TeamCreate,
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
    TeamUpdate,
    UserPublic,
)
from app.services.workspace_db import WorkspaceServiceDB

router = APIRouter()


@router.post("/teams", response_model=TeamDetail, status_code=status.HTTP_201_CREATED)
async def create_team(
    payload: TeamCreate,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> TeamDetail:
    return await svc.create_team(payload, user)


@router.get("/teams", response_model=TeamListResponse)
async def list_teams(
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> TeamListResponse:
    return TeamListResponse(items=await svc.list_teams(user))


@router.get("/teams/{team_id}", response_model=TeamDetail)
async def team_detail(
    team_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> TeamDetail:
    return await svc.get_team_detail(team_id, user)


@router.patch("/teams/{team_id}", response_model=TeamDetail)
async def update_team(
    team_id: str,
    payload: TeamUpdate,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> TeamDetail:
    return await svc.update_team(team_id, payload, user)


@router.delete("/teams/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> Response:
    await svc.delete_team(team_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/teams/{team_id}/members/me", status_code=status.HTTP_204_NO_CONTENT)
async def leave_team(
    team_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> Response:
    await svc.leave_team(team_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/teams/{team_id}/messages", response_model=TeamMessageListResponse)
async def team_messages(
    team_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> TeamMessageListResponse:
    items = await svc.list_team_messages(team_id, user)
    return TeamMessageListResponse(items=items, total=len(items))


@router.post("/teams/{team_id}/messages", response_model=TeamMessageItem, status_code=status.HTTP_201_CREATED)
async def create_team_message(
    team_id: str,
    payload: TeamMessageCreate,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> TeamMessageItem:
    return await svc.create_team_message(team_id, payload, user)


@router.post("/teams/{team_id}/invites", response_model=TeamInvitePublic, status_code=status.HTTP_201_CREATED)
async def create_team_invite(
    team_id: str,
    payload: TeamInviteCreate,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> TeamInvitePublic:
    return await svc.create_team_invite(team_id, payload, user)


@router.post("/teams/{team_id}/members", response_model=TeamMemberPublic, status_code=status.HTTP_201_CREATED)
async def join_team(
    team_id: str,
    payload: TeamMemberJoin,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> TeamMemberPublic:
    return await svc.join_team(team_id, payload, user)


@router.patch("/teams/{team_id}/members/{member_id}", response_model=TeamMemberPublic)
async def update_team_member(
    team_id: str,
    member_id: str,
    payload: TeamMemberUpdate,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> TeamMemberPublic:
    return await svc.update_team_member(team_id, member_id, payload, user)


@router.delete("/teams/{team_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: str,
    member_id: str,
    user: Annotated[UserPublic, Depends(current_user)],
    svc: WorkspaceServiceDB = Depends(get_svc),
) -> Response:
    await svc.remove_team_member(team_id, member_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
