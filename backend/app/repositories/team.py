from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Team, TeamMember, TeamInvite, TeamMessage

class TeamRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def get_by_id(self, tid: str) -> Team | None: return await self._s.get(Team, tid)
    async def list_all(self) -> list[Team]:
        r = await self._s.execute(select(Team))
        return list(r.scalars().all())
    async def create(self, t: Team) -> Team: self._s.add(t); await self._s.flush(); return t
    async def delete(self, t: Team) -> None: await self._s.delete(t); await self._s.flush()

class TeamMemberRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def get_by_id(self, mid: str) -> TeamMember | None: return await self._s.get(TeamMember, mid)
    async def get_by_team_and_user(self, team_id: str, user_id: int) -> TeamMember | None:
        r = await self._s.execute(select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.user_id == user_id, TeamMember.status == "active"))
        return r.scalar_one_or_none()
    async def list_by_team(self, team_id: str) -> list[TeamMember]:
        r = await self._s.execute(select(TeamMember).where(TeamMember.team_id == team_id, TeamMember.status == "active"))
        return list(r.scalars().all())
    async def create(self, m: TeamMember) -> TeamMember: self._s.add(m); await self._s.flush(); return m
    async def update(self, m: TeamMember) -> TeamMember: await self._s.flush(); return m

class TeamInviteRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def get_by_token(self, token: str) -> TeamInvite | None:
        r = await self._s.execute(select(TeamInvite).where(TeamInvite.token == token))
        return r.scalar_one_or_none()
    async def list_by_team(self, team_id: str) -> list[TeamInvite]:
        r = await self._s.execute(select(TeamInvite).where(TeamInvite.team_id == team_id, TeamInvite.status == "pending"))
        return list(r.scalars().all())
    async def create(self, inv: TeamInvite) -> TeamInvite: self._s.add(inv); await self._s.flush(); return inv

class TeamMessageRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def list_by_team(self, team_id: str) -> list[TeamMessage]:
        r = await self._s.execute(select(TeamMessage).where(TeamMessage.team_id == team_id).order_by(TeamMessage.created_at))
        return list(r.scalars().all())
    async def create(self, msg: TeamMessage) -> TeamMessage: self._s.add(msg); await self._s.flush(); return msg
