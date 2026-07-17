from __future__ import annotations
from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AgentMessage, AgentPlanRevision, AgentTask, AgentTaskStep, AgentToolCall, Workflow, WorkflowDebugSession, WorkflowExecution, WorkflowVersion

class WorkflowRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def get_by_id(self, wid: str) -> Workflow | None: return await self._s.get(Workflow, wid)
    async def list_all(self) -> list[Workflow]:
        r = await self._s.execute(select(Workflow))
        return list(r.scalars().all())
    async def create(self, w: Workflow) -> Workflow: self._s.add(w); await self._s.flush(); return w
    async def update(self, w: Workflow) -> Workflow: await self._s.flush(); return w
    async def delete(self, w: Workflow) -> None: await self._s.delete(w); await self._s.flush()

class WorkflowVersionRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def get_by_id(self, version_id: str) -> WorkflowVersion | None: return await self._s.get(WorkflowVersion, version_id)
    async def list_by_workflow(self, workflow_id: str) -> list[WorkflowVersion]:
        r = await self._s.execute(select(WorkflowVersion).where(WorkflowVersion.workflow_id == workflow_id).order_by(WorkflowVersion.published_at.desc()))
        return list(r.scalars().all())
    async def create(self, item: WorkflowVersion) -> WorkflowVersion: self._s.add(item); await self._s.flush(); return item

class WorkflowExecutionRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def list_by_workflow(self, workflow_id: str) -> list[WorkflowExecution]:
        r = await self._s.execute(select(WorkflowExecution).where(WorkflowExecution.workflow_id == workflow_id).order_by(WorkflowExecution.created_at.desc()))
        return list(r.scalars().all())
    async def create(self, item: WorkflowExecution) -> WorkflowExecution: self._s.add(item); await self._s.flush(); return item

class WorkflowDebugSessionRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def get_by_id(self, session_id: str) -> WorkflowDebugSession | None: return await self._s.get(WorkflowDebugSession, session_id)
    async def create(self, item: WorkflowDebugSession) -> WorkflowDebugSession: self._s.add(item); await self._s.flush(); return item
    async def update(self, item: WorkflowDebugSession) -> WorkflowDebugSession: await self._s.flush(); return item
    async def delete(self, item: WorkflowDebugSession) -> None: await self._s.delete(item); await self._s.flush()
    async def claim(self, session_id: str, owner_id: int, token: str, now, lease_expires_at) -> bool:
        result = await self._s.execute(
            update(WorkflowDebugSession)
            .where(
                WorkflowDebugSession.id == session_id,
                WorkflowDebugSession.owner_id == owner_id,
                or_(WorkflowDebugSession.lease_token.is_(None), WorkflowDebugSession.lease_expires_at <= now),
            )
            .values(lease_token=token, lease_expires_at=lease_expires_at, updated_at=now)
            .execution_options(synchronize_session=False)
        )
        await self._s.commit()
        return bool(result.rowcount)
    async def release(self, session_id: str, token: str) -> None:
        await self._s.execute(
            update(WorkflowDebugSession)
            .where(WorkflowDebugSession.id == session_id, WorkflowDebugSession.lease_token == token)
            .values(lease_token=None, lease_expires_at=None)
            .execution_options(synchronize_session=False)
        )
        await self._s.commit()

class AgentTaskRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def get_by_id(self, task_id: str) -> AgentTask | None: return await self._s.get(AgentTask, task_id)
    async def list_by_owner(self, owner_id: int, limit: int = 50) -> list[AgentTask]:
        r = await self._s.execute(
            select(AgentTask)
            .where(AgentTask.owner_id == owner_id)
            .order_by(AgentTask.updated_at.desc(), AgentTask.created_at.desc())
            .limit(limit)
        )
        return list(r.scalars().all())
    async def create(self, task: AgentTask) -> AgentTask: self._s.add(task); await self._s.flush(); return task
    async def update(self, task: AgentTask) -> AgentTask: await self._s.flush(); return task
    async def delete(self, task: AgentTask) -> None:
        await self._s.execute(delete(AgentTaskStep).where(AgentTaskStep.task_id == task.id))
        await self._s.execute(delete(AgentMessage).where(AgentMessage.task_id == task.id))
        await self._s.execute(delete(AgentToolCall).where(AgentToolCall.task_id == task.id))
        await self._s.execute(delete(AgentPlanRevision).where(AgentPlanRevision.task_id == task.id))
        await self._s.delete(task)
        await self._s.flush()

class AgentTaskStepRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def list_by_task(self, task_id: str) -> list[AgentTaskStep]:
        r = await self._s.execute(
            select(AgentTaskStep)
            .where(AgentTaskStep.task_id == task_id)
            .order_by(AgentTaskStep.sequence.asc(), AgentTaskStep.id.asc())
        )
        return list(r.scalars().all())
    async def replace_for_task(self, task_id: str, steps: list[AgentTaskStep]) -> None:
        await self._s.execute(delete(AgentTaskStep).where(AgentTaskStep.task_id == task_id))
        for step in steps:
            self._s.add(step)
        await self._s.flush()

class AgentMessageRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def list_by_task(self, task_id: str) -> list[AgentMessage]:
        r = await self._s.execute(
            select(AgentMessage)
            .where(AgentMessage.task_id == task_id)
            .order_by(AgentMessage.sequence.asc(), AgentMessage.created_at.asc())
        )
        return list(r.scalars().all())
    async def replace_for_task(self, task_id: str, messages: list[AgentMessage]) -> None:
        await self._s.execute(delete(AgentMessage).where(AgentMessage.task_id == task_id))
        for message in messages:
            self._s.add(message)
        await self._s.flush()

class AgentToolCallRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def list_by_task(self, task_id: str) -> list[AgentToolCall]:
        r = await self._s.execute(
            select(AgentToolCall)
            .where(AgentToolCall.task_id == task_id)
            .order_by(AgentToolCall.step_sequence.asc(), AgentToolCall.created_at.asc())
        )
        return list(r.scalars().all())
    async def replace_for_task(self, task_id: str, calls: list[AgentToolCall]) -> None:
        await self._s.execute(delete(AgentToolCall).where(AgentToolCall.task_id == task_id))
        for call in calls:
            self._s.add(call)
        await self._s.flush()

class AgentPlanRevisionRepository:
    def __init__(self, session: AsyncSession): self._s = session
    async def list_by_task(self, task_id: str) -> list[AgentPlanRevision]:
        r = await self._s.execute(
            select(AgentPlanRevision)
            .where(AgentPlanRevision.task_id == task_id)
            .order_by(AgentPlanRevision.revision_no.asc(), AgentPlanRevision.created_at.asc())
        )
        return list(r.scalars().all())
    async def replace_for_task(self, task_id: str, revisions: list[AgentPlanRevision]) -> None:
        await self._s.execute(delete(AgentPlanRevision).where(AgentPlanRevision.task_id == task_id))
        for revision in revisions:
            self._s.add(revision)
        await self._s.flush()
