from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import UploadFile

from app.domain.schemas import (
    AgentStep,
    AgentTaskRequest,
    AgentTaskResponse,
    AuditLogEntry,
    Citation,
    DashboardSummary,
    FileCopyRequest,
    FileItem,
    FileUpdate,
    FileVersionItem,
    FolderCreate,
    FolderItem,
    FolderUpdate,
    QARequest,
    QAResponse,
    TeamCreate,
    TeamDetail,
    TeamInviteCreate,
    TeamInvitePublic,
    TeamSummary,
    TeamMemberJoin,
    TeamMemberPublic,
    TeamMemberUpdate,
    ToolDefinition,
    UserCreate,
    UserPublic,
    UserUpdate,
    WorkflowDefinition,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowNodeExecution,
    WorkspaceSnapshot,
)


class WorkspaceError(Exception):
    def __init__(self, status_code: int, code: str, message: str, detail: dict[str, Any] | None = None) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.detail = detail or {}
        super().__init__(message)


LOGIN_FAILURE_LIMIT = 5
LOGIN_LOCKOUT_DURATION = timedelta(minutes=5)


@dataclass
class LoginSecurityState:
    failed_attempts: int = 0
    locked_until: datetime | None = None


@dataclass
class StoredUser:
    public: UserPublic
    password_hash: str
    security: LoginSecurityState = field(default_factory=LoginSecurityState)


@dataclass
class StoredFolder:
    id: str
    name: str
    parent_id: str | None
    scope: str
    permission: str
    team_id: str | None = None


@dataclass
class StoredFileVersion:
    id: str
    file_id: str
    version_no: int
    name: str
    content: bytes
    sha256: str
    size: int
    created_at: datetime
    created_by: str


@dataclass
class StoredTeam:
    id: str
    name: str
    description: str
    root_folder_id: str
    created_by: int
    created_at: datetime
    unread_count: int = 0


@dataclass
class StoredTeamMember:
    id: str
    team_id: str
    user_id: int
    role: str
    status: str
    joined_at: datetime


@dataclass
class StoredTeamInvite:
    id: str
    team_id: str
    email: str
    role: str
    token: str
    status: str
    created_by: int
    created_at: datetime
    expires_at: datetime


class WorkspaceService:
    def __init__(self) -> None:
        self._secret = "dev-workspace-secret"
        self._users_by_id: dict[int, StoredUser] = {}
        self._users_by_username: dict[str, StoredUser] = {}
        self._users_by_email: dict[str, StoredUser] = {}
        self._next_user_id = 1
        self._folders = self._seed_folders()
        self._files = self._seed_files()
        self._file_contents = self._seed_file_contents()
        self._file_versions = self._seed_file_versions()
        self._teams = self._seed_teams()
        self._team_members: dict[str, StoredTeamMember] = {}
        self._team_invites: dict[str, StoredTeamInvite] = {}
        self._audit_logs: list[AuditLogEntry] = []

    def register_user(self, payload: UserCreate) -> tuple[UserPublic, str, str]:
        if payload.username in self._users_by_username:
            raise WorkspaceError(
                409,
                "USERNAME_EXISTS",
                "用户名已存在",
                {"username": payload.username},
            )
        if str(payload.email) in self._users_by_email:
            raise WorkspaceError(409, "EMAIL_EXISTS", "邮箱已存在", {"email": str(payload.email)})

        user = UserPublic(
            id=self._next_user_id,
            username=payload.username,
            email=payload.email,
            display_name=payload.username,
            roles=["user"],
        )
        self._next_user_id += 1
        stored = StoredUser(public=user, password_hash=self._hash_password(payload.password))
        self._users_by_id[user.id] = stored
        self._users_by_username[user.username] = stored
        self._users_by_email[str(user.email)] = stored
        self._record_audit(user.username, "auth.register", "user", user.username)
        return user, self._create_token(user.id, "access"), self._create_token(user.id, "refresh")

    def login_user(self, account: str, password: str) -> tuple[UserPublic, str, str]:
        stored = self._users_by_username.get(account) or self._users_by_email.get(account)
        now = datetime.now(UTC)
        if stored:
            self._ensure_login_not_locked(stored, now)
        if not stored or not hmac.compare_digest(stored.password_hash, self._hash_password(password)):
            if stored:
                self._record_failed_login(stored, now)
            raise WorkspaceError(401, "INVALID_CREDENTIALS", "用户名、邮箱或密码不正确")
        stored.security = LoginSecurityState()
        self._record_audit(stored.public.username, "auth.login", "user", stored.public.username)
        return stored.public, self._create_token(stored.public.id, "access"), self._create_token(stored.public.id, "refresh")

    def refresh_session(self, refresh_token: str) -> tuple[UserPublic, str, str]:
        user_id = self._read_token(refresh_token, expected_kind="refresh")
        stored = self._users_by_id.get(user_id)
        if not stored:
            raise WorkspaceError(401, "INVALID_TOKEN", "登录状态无效，请重新登录")
        self._record_audit(stored.public.username, "auth.refresh", "user", stored.public.username)
        return stored.public, self._create_token(stored.public.id, "access"), self._create_token(stored.public.id, "refresh")

    def require_user(self, authorization: str | None) -> UserPublic:
        if not authorization or not authorization.startswith("Bearer "):
            raise WorkspaceError(401, "AUTH_REQUIRED", "请先登录后再访问该资源")
        token = authorization.removeprefix("Bearer ").strip()
        user_id = self._read_token(token, expected_kind="access")
        stored = self._users_by_id.get(user_id)
        if not stored:
            raise WorkspaceError(401, "INVALID_TOKEN", "登录状态无效，请重新登录")
        return stored.public

    def update_user_profile(self, user_id: int, payload: UserUpdate) -> UserPublic:
        stored = self._users_by_id.get(user_id)
        if not stored:
            raise WorkspaceError(404, "USER_NOT_FOUND", "用户不存在")

        next_email = payload.email
        if next_email and next_email != stored.public.email:
            existing = self._users_by_email.get(next_email)
            if existing and existing.public.id != user_id:
                raise WorkspaceError(409, "EMAIL_EXISTS", "邮箱已存在", {"email": next_email})
            self._users_by_email.pop(stored.public.email, None)

        stored.public = stored.public.model_copy(
            update={
                "display_name": payload.display_name or stored.public.display_name,
                "email": next_email or stored.public.email,
            }
        )
        self._users_by_id[user_id] = stored
        self._users_by_username[stored.public.username] = stored
        self._users_by_email[stored.public.email] = stored
        self._record_audit(stored.public.username, "user.update_profile", "user", stored.public.username)
        return stored.public

    def folder_tree(self, actor: UserPublic) -> list[FolderItem]:
        return [
            self._folder_item(folder, actor)
            for folder in self._folders.values()
            if folder.parent_id is None and self._can_read_folder(folder, actor)
        ]

    def create_folder(self, payload: FolderCreate, actor: UserPublic) -> FolderItem:
        parent_id = payload.parent_id or ("team-root" if payload.scope == "team" else "personal-root")
        parent = self._find_folder(parent_id)
        if parent.scope != payload.scope:
            raise WorkspaceError(
                409,
                "FOLDER_SCOPE_MISMATCH",
                "目标父文件夹与新文件夹空间不一致",
                {"parent_id": parent_id, "scope": payload.scope},
            )
        self._ensure_can_write_folder(parent, actor)
        folder = StoredFolder(
            id=f"folder-{secrets.token_hex(4)}",
            name=self._clean_folder_name(payload.name),
            parent_id=parent_id,
            scope=payload.scope,
            permission=parent.permission,
            team_id=parent.team_id,
        )
        self._folders[folder.id] = folder
        self._record_audit(actor.username, "folder.create", "folder", folder.name)
        return self._folder_item(folder, actor)

    def update_folder(self, folder_id: str, payload: FolderUpdate, actor: UserPublic) -> FolderItem:
        folder = self._find_folder(folder_id)
        self._ensure_mutable_folder(folder)
        self._ensure_can_write_folder(folder, actor)
        old_name = folder.name
        old_parent_id = folder.parent_id

        if "name" in payload.model_fields_set and payload.name is not None:
            folder.name = self._clean_folder_name(payload.name)

        if "parent_id" in payload.model_fields_set:
            next_parent_id = payload.parent_id or ("team-root" if folder.scope == "team" else "personal-root")
            self._ensure_valid_folder_move(folder, next_parent_id)
            folder.parent_id = next_parent_id

        if folder.name != old_name:
            self._record_audit(actor.username, "folder.rename", "folder", folder.name)
        if folder.parent_id != old_parent_id:
            self._record_audit(actor.username, "folder.move", "folder", folder.name)
        return self._folder_item(folder, actor)

    def delete_folder(self, folder_id: str, actor: UserPublic) -> None:
        folder = self._find_folder(folder_id)
        self._ensure_mutable_folder(folder)
        self._ensure_can_write_folder(folder, actor)
        child_count = sum(1 for candidate in self._folders.values() if candidate.parent_id == folder_id)
        file_count = sum(1 for file_item in self._files if file_item.folder_id == folder_id)
        if child_count or file_count:
            raise WorkspaceError(
                409,
                "FOLDER_NOT_EMPTY",
                "文件夹非空，不能直接删除",
                {"folder_id": folder_id, "child_count": child_count, "file_count": file_count},
            )
        self._folders.pop(folder_id)
        self._record_audit(actor.username, "folder.delete", "folder", folder.name)

    def list_files(self, query: str | None = None, tag: str | None = None, file_type: str | None = None) -> list[FileItem]:
        files = self._files
        if query:
            files = [file for file in files if query.lower() in file.name.lower()]
        if tag:
            files = [file for file in files if tag in file.tags]
        if file_type:
            files = [file for file in files if file.type == file_type]
        return files

    async def upload_file(self, upload: UploadFile, folder_id: str, tags: str | None, actor: UserPublic) -> FileItem:
        folder = self._find_folder(folder_id)
        self._ensure_can_write_folder(folder, actor)
        content = await upload.read()
        digest = hashlib.sha256(content).hexdigest()
        clean_tags = self._normalize_tags((tags or "").split(","))
        filename = self._clean_file_name(upload.filename or "未命名文件")
        existing_file = self._find_file_by_name_in_folder(filename, folder_id)
        if existing_file:
            self._append_file_version(existing_file, filename, content, actor.username)
            updated = existing_file.model_copy(
                update={
                    "name": filename,
                    "type": self._file_type(filename),
                    "size": len(content),
                    "sha256": digest,
                    "parse_status": "queued",
                    "tags": clean_tags,
                    "updated_at": datetime.now(UTC),
                    "permission_scope": self._permission_scope_for_folder(folder),
                }
            )
            self._file_contents[updated.id] = content
            self._replace_file(updated, move_to_front=True)
            self._record_audit(actor.username, "file.upload", "file", updated.name)
            return updated

        item = FileItem(
            id=self._new_file_id(digest),
            name=filename,
            folder_id=folder_id,
            type=self._file_type(filename),
            size=len(content),
            sha256=digest,
            parse_status="queued",
            tags=clean_tags,
            updated_at=datetime.now(UTC),
            permission_scope=self._permission_scope_for_folder(folder),
            knowledge_base_ids=[],
        )
        self._files.insert(0, item)
        self._file_contents[item.id] = content
        self._append_file_version(item, item.name, content, actor.username)
        self._record_audit(actor.username, "file.upload", "file", item.name)
        return item

    def update_file(self, file_id: str, payload: FileUpdate, actor: UserPublic) -> FileItem:
        file_item = self._find_file(file_id)
        updates: dict[str, Any] = {}
        next_name = file_item.name
        next_folder_id = file_item.folder_id
        next_tags = file_item.tags
        target_folder: StoredFolder | None = None

        if "name" in payload.model_fields_set and payload.name is not None:
            next_name = self._clean_file_name(payload.name)
            updates["name"] = next_name
            updates["type"] = self._file_type(next_name)

        if "folder_id" in payload.model_fields_set and payload.folder_id is not None:
            target_folder = self._ensure_file_target_folder(file_item, payload.folder_id, actor)
            next_folder_id = target_folder.id
            updates["folder_id"] = next_folder_id
            updates["permission_scope"] = self._permission_scope_for_folder(target_folder)

        if "tags" in payload.model_fields_set and payload.tags is not None:
            next_tags = self._normalize_tags(payload.tags)
            updates["tags"] = next_tags

        if not updates:
            return file_item

        updates["updated_at"] = datetime.now(UTC)
        updated = file_item.model_copy(update=updates)
        self._replace_file(updated)

        if next_name != file_item.name:
            self._record_audit(actor.username, "file.rename", "file", updated.name)
        if next_folder_id != file_item.folder_id:
            self._record_audit(actor.username, "file.move", "file", updated.name)
        if next_tags != file_item.tags:
            self._record_audit(actor.username, "file.update_tags", "file", updated.name)
        return updated

    def copy_file(self, file_id: str, payload: FileCopyRequest, actor: UserPublic) -> FileItem:
        source = self._find_file(file_id)
        target_folder = self._ensure_file_target_folder(source, payload.target_folder_id, actor)
        content = self._read_file_content(file_id)
        name = self._clean_file_name(payload.name or self._copy_file_name(source.name))
        tags = self._normalize_tags(payload.tags) if payload.tags is not None else list(source.tags)
        digest = hashlib.sha256(content).hexdigest()
        copied = source.model_copy(
            update={
                "id": self._new_file_id(digest),
                "name": name,
                "folder_id": target_folder.id,
                "type": self._file_type(name),
                "size": len(content),
                "sha256": digest,
                "tags": tags,
                "updated_at": datetime.now(UTC),
                "permission_scope": self._permission_scope_for_folder(target_folder),
                "knowledge_base_ids": [],
            }
        )
        self._files.insert(0, copied)
        self._file_contents[copied.id] = content
        self._file_versions[copied.id] = [self._make_file_version(copied, copied.name, content, actor.username)]
        self._record_audit(actor.username, "file.copy", "file", copied.name)
        return copied

    def download_file(self, file_id: str, actor: UserPublic) -> tuple[FileItem, bytes]:
        file_item = self._find_file(file_id)
        content = self._read_file_content(file_id)
        self._record_audit(actor.username, "file.download", "file", file_item.name)
        return file_item, content

    def list_file_versions(self, file_id: str, _: UserPublic) -> list[FileVersionItem]:
        self._find_file(file_id)
        versions = self._file_versions.get(file_id, [])
        current_version_no = max((version.version_no for version in versions), default=0)
        return [
            self._file_version_item(version, current_version_no)
            for version in sorted(versions, key=lambda item: item.version_no, reverse=True)
        ]

    def restore_file_version(self, file_id: str, version_id: str, actor: UserPublic) -> FileItem:
        file_item = self._find_file(file_id)
        version = self._find_file_version(file_id, version_id)
        self._append_file_version(file_item, file_item.name, version.content, actor.username)
        restored = file_item.model_copy(
            update={
                "size": version.size,
                "sha256": version.sha256,
                "parse_status": "queued",
                "updated_at": datetime.now(UTC),
            }
        )
        self._file_contents[file_id] = version.content
        self._replace_file(restored, move_to_front=True)
        self._record_audit(actor.username, "file.version_restore", "file", restored.name)
        return restored

    def delete_file(self, file_id: str, actor: UserPublic) -> None:
        file_item = self._find_file(file_id)
        self._files = [candidate for candidate in self._files if candidate.id != file_id]
        self._file_contents.pop(file_id, None)
        self._file_versions.pop(file_id, None)
        self._record_audit(actor.username, "file.delete", "file", file_item.name)

    def answer_question(self, payload: QARequest, actor: UserPublic) -> QAResponse:
        citation = Citation(
            file_id="file-microscope",
            document_id="doc-microscope",
            chunk_id="chunk-micro-003",
            title="显微镜实验报告.pdf",
            page_no=3,
            paragraph_no=5,
            snippet="显微镜实验包含取样、制片、低倍镜定位、高倍镜观察和结果记录。",
        )
        answer = (
            "显微镜相关实验步骤包括：准备载玻片与样本，低倍镜定位目标区域，"
            "切换高倍镜观察细胞结构，记录视野特征，并在实验报告中附上观察结论。"
        )
        self._record_audit(actor.username, "qa.query", "knowledge_base", payload.kb_id)
        return QAResponse(
            conversation_id=payload.conversation_id or "conv-biology",
            message_id=f"msg-{secrets.token_hex(4)}",
            answer=answer,
            citations=[citation],
        )

    def list_tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                id="tool-file-search",
                name="file_search",
                version="1.0.0",
                category="文件操作",
                description="按文件名、标签和解析状态搜索用户可访问文件。",
                input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"files": {"type": "array"}}},
            ),
            ToolDefinition(
                id="tool-knowledge-qa",
                name="knowledge_qa",
                version="1.0.0",
                category="AI处理",
                description="基于知识库检索片段生成带引用的回答。",
                input_schema={"type": "object", "required": ["kb_id", "question"]},
                output_schema={"type": "object", "properties": {"answer": {"type": "string"}, "citations": {"type": "array"}}},
            ),
            ToolDefinition(
                id="tool-report-generate",
                name="report_generate",
                version="1.0.0",
                category="AI处理",
                description="将检索结果和活动动态整理为 Markdown 报告。",
                input_schema={"type": "object", "properties": {"topic": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"report": {"type": "string"}}},
            ),
            ToolDefinition(
                id="tool-image-ocr",
                name="image_ocr",
                version="1.0.0",
                category="文档解析",
                description="提取图片或扫描件中的文字。",
                input_schema={"type": "object", "properties": {"file_id": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"text": {"type": "string"}}},
            ),
        ]

    def create_agent_task(self, payload: AgentTaskRequest, actor: UserPublic) -> AgentTaskResponse:
        final_answer = "已汇总 1 份实验报告，生成包含实验目的、显微镜步骤、观察结果和待补充数据的周报草稿。"
        steps = [
            AgentStep(type="thought", title="任务理解", content="需要先找到相关团队/个人文件，再生成结构化报告。"),
            AgentStep(type="action", title="搜索文件", content="按生物实验和显微镜关键词检索文件。", tool_name="file_search"),
            AgentStep(type="observation", title="文件结果", content="找到 显微镜实验报告.pdf，已入库，可用于问答。"),
            AgentStep(type="action", title="生成报告", content="根据检索结果生成团队周报草稿。", tool_name="report_generate"),
            AgentStep(type="observation", title="报告草稿", content="报告包含 4 个章节和 1 条待确认事项。"),
            AgentStep(type="answer", title="最终结果", content=final_answer),
        ]
        self._record_audit(actor.username, "agent.create_task", "agent_task", payload.task)
        return AgentTaskResponse(
            id=f"agent-{secrets.token_hex(4)}",
            task=payload.task,
            status="completed",
            steps=steps,
            final_answer=final_answer,
        )

    def list_workflows(self) -> list[WorkflowDefinition]:
        return [
            WorkflowDefinition(
                id="new-file-auto-summary",
                name="新文件自动摘要",
                description="文件上传后自动解析、知识库问答并生成摘要。",
                trigger="file.uploaded",
                version="1.0.0",
                node_count=3,
                status="published",
            )
        ]

    def execute_workflow(
        self,
        workflow_id: str,
        payload: WorkflowExecutionRequest,
        actor: UserPublic,
    ) -> WorkflowExecutionResponse:
        if workflow_id != "new-file-auto-summary":
            raise WorkspaceError(404, "WORKFLOW_NOT_FOUND", "流程不存在", {"workflow_id": workflow_id})
        file_item = self._find_file(payload.file_id)
        nodes = [
            WorkflowNodeExecution(
                node_id="parse",
                name="内容提取",
                tool_name="file_search",
                status="success",
                input={"file_id": payload.file_id},
                output={"chunks": 8},
            ),
            WorkflowNodeExecution(
                node_id="qa",
                name="知识问答",
                tool_name="knowledge_qa",
                status="success",
                input={"kb_id": payload.target_kb_id or "kb-biology"},
                output={"citations": 1},
            ),
            WorkflowNodeExecution(
                node_id="summary",
                name="摘要生成",
                tool_name="report_generate",
                status="success",
                input={"file_id": payload.file_id},
                output={"format": "markdown"},
            ),
        ]
        summary = f"{file_item.name} 已完成自动摘要：文档围绕显微镜实验步骤、观察记录和结论整理。"
        self._record_audit(actor.username, "workflow.execute", "workflow", workflow_id)
        return WorkflowExecutionResponse(
            id=f"exec-{secrets.token_hex(4)}",
            workflow_id=workflow_id,
            status="completed",
            node_executions=nodes,
            output={"summary": summary},
        )

    def create_team(self, payload: TeamCreate, actor: UserPublic) -> TeamDetail:
        team_id = f"team-{secrets.token_hex(4)}"
        root_folder_id = f"{team_id}-root"
        team = StoredTeam(
            id=team_id,
            name=self._clean_team_name(payload.name),
            description=(payload.description or "").strip(),
            root_folder_id=root_folder_id,
            created_by=actor.id,
            created_at=datetime.now(UTC),
        )
        self._teams[team.id] = team
        self._folders[root_folder_id] = StoredFolder(
            id=root_folder_id,
            name=team.name,
            parent_id=None,
            scope="team",
            permission="管理",
            team_id=team.id,
        )
        self._team_members[self._team_member_id(team.id, actor.id)] = StoredTeamMember(
            id=self._team_member_id(team.id, actor.id),
            team_id=team.id,
            user_id=actor.id,
            role="owner",
            status="active",
            joined_at=datetime.now(UTC),
        )
        self._record_audit(actor.username, "team.create", "team", team.name)
        return self.get_team_detail(team.id, actor)

    def list_teams(self, actor: UserPublic) -> list[TeamSummary]:
        memberships = [
            member
            for member in self._team_members.values()
            if member.user_id == actor.id and member.status == "active"
        ]
        return [self._team_summary(self._find_team(member.team_id), member.role) for member in memberships]

    def get_team_detail(self, team_id: str, actor: UserPublic) -> TeamDetail:
        team = self._find_team(team_id)
        membership = self._require_team_member(team_id, actor)
        return TeamDetail(
            id=team.id,
            name=team.name,
            description=team.description,
            role=membership.role,  # type: ignore[arg-type]
            member_count=self._active_team_member_count(team.id),
            unread_count=team.unread_count,
            root_folder=self._folder_item(self._find_folder(team.root_folder_id), actor),
            members=[
                self._team_member_public(member)
                for member in self._team_members.values()
                if member.team_id == team.id and member.status == "active"
            ],
            invites=[
                self._team_invite_public(invite)
                for invite in self._team_invites.values()
                if invite.team_id == team.id and invite.status == "pending"
            ],
        )

    def create_team_invite(self, team_id: str, payload: TeamInviteCreate, actor: UserPublic) -> TeamInvitePublic:
        team = self._find_team(team_id)
        self._require_team_manager(team_id, actor)
        invite = StoredTeamInvite(
            id=f"invite-{secrets.token_hex(4)}",
            team_id=team.id,
            email=payload.email,
            role=payload.role,
            token=secrets.token_urlsafe(18),
            status="pending",
            created_by=actor.id,
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        self._team_invites[invite.id] = invite
        self._record_audit(actor.username, "team.invite_create", "team", team.name)
        return self._team_invite_public(invite)

    def join_team(self, team_id: str, payload: TeamMemberJoin, actor: UserPublic) -> TeamMemberPublic:
        team = self._find_team(team_id)
        invite = self._find_invite_by_token(payload.invite_token)
        if invite.team_id != team.id or invite.status != "pending":
            raise WorkspaceError(404, "TEAM_INVITE_NOT_FOUND", "邀请不存在或已失效", {"team_id": team_id})
        if invite.email != actor.email:
            raise WorkspaceError(403, "TEAM_INVITE_EMAIL_MISMATCH", "当前账号与邀请邮箱不一致", {"team_id": team_id})
        if invite.expires_at < datetime.now(UTC):
            invite.status = "expired"
            raise WorkspaceError(410, "TEAM_INVITE_EXPIRED", "邀请已过期", {"team_id": team_id})

        member_id = self._team_member_id(team.id, actor.id)
        member = StoredTeamMember(
            id=member_id,
            team_id=team.id,
            user_id=actor.id,
            role=invite.role,
            status="active",
            joined_at=datetime.now(UTC),
        )
        self._team_members[member_id] = member
        invite.status = "accepted"
        self._record_audit(actor.username, "team.member_join", "team", team.name)
        return self._team_member_public(member)

    def update_team_member(self, team_id: str, member_id: str, payload: TeamMemberUpdate, actor: UserPublic) -> TeamMemberPublic:
        team = self._find_team(team_id)
        self._require_team_manager(team_id, actor)
        member = self._find_team_member(team_id, member_id)
        if member.role == "owner" and member.user_id != actor.id:
            raise WorkspaceError(409, "TEAM_OWNER_PROTECTED", "不能修改团队所有者角色", {"member_id": member_id})
        member.role = payload.role
        self._record_audit(actor.username, "team.member_role_update", "team", team.name)
        return self._team_member_public(member)

    def remove_team_member(self, team_id: str, member_id: str, actor: UserPublic) -> None:
        team = self._find_team(team_id)
        self._require_team_manager(team_id, actor)
        member = self._find_team_member(team_id, member_id)
        if member.role == "owner":
            raise WorkspaceError(409, "TEAM_OWNER_PROTECTED", "不能移除团队所有者", {"member_id": member_id})
        member.status = "removed"
        self._record_audit(actor.username, "team.member_remove", "team", team.name)

    def list_audit_logs(self) -> list[AuditLogEntry]:
        seeded = [
            AuditLogEntry(
                id="audit-seed-1",
                actor="system",
                action="tool.publish",
                resource_type="tool",
                resource_name="knowledge_qa",
                created_at=datetime.now(UTC) - timedelta(hours=4),
            )
        ]
        return [*self._audit_logs[-8:], *seeded]

    def snapshot(self, actor: UserPublic) -> WorkspaceSnapshot:
        files = self.list_files()
        teams = self.list_teams(actor)
        return WorkspaceSnapshot(
            summary=DashboardSummary(
                file_count=len(files),
                indexed_count=sum(1 for file in files if file.parse_status == "indexed"),
                knowledge_base_count=2,
                running_workflows=0,
                unread_notifications=sum(team.unread_count for team in teams),
                tools_enabled=sum(1 for tool in self.list_tools() if tool.enabled),
            ),
            files=files[:5],
            tools=self.list_tools(),
            workflows=self.list_workflows(),
            teams=teams,
            audit_logs=self.list_audit_logs(),
        )

    def _team_summary(self, team: StoredTeam, role: str) -> TeamSummary:
        return TeamSummary(
            id=team.id,
            name=team.name,
            description=team.description,
            role=role,
            member_count=self._active_team_member_count(team.id),
            unread_count=team.unread_count,
            root_folder_id=team.root_folder_id,
        )

    def _team_member_public(self, member: StoredTeamMember) -> TeamMemberPublic:
        stored = self._users_by_id.get(member.user_id)
        if not stored:
            raise WorkspaceError(404, "USER_NOT_FOUND", "用户不存在", {"user_id": member.user_id})
        return TeamMemberPublic(
            id=member.id,
            team_id=member.team_id,
            user_id=member.user_id,
            username=stored.public.username,
            email=stored.public.email,
            display_name=stored.public.display_name,
            role=member.role,  # type: ignore[arg-type]
            status=member.status,  # type: ignore[arg-type]
            joined_at=member.joined_at,
        )

    def _team_invite_public(self, invite: StoredTeamInvite) -> TeamInvitePublic:
        return TeamInvitePublic(
            id=invite.id,
            team_id=invite.team_id,
            email=invite.email,
            role=invite.role,  # type: ignore[arg-type]
            status=invite.status,  # type: ignore[arg-type]
            token=invite.token,
            created_at=invite.created_at,
            expires_at=invite.expires_at,
        )

    def _active_team_member_count(self, team_id: str) -> int:
        return sum(
            1
            for member in self._team_members.values()
            if member.team_id == team_id and member.status == "active"
        )

    def _team_member_id(self, team_id: str, user_id: int) -> str:
        return f"{team_id}-member-{user_id}"

    def _find_team(self, team_id: str) -> StoredTeam:
        team = self._teams.get(team_id)
        if not team:
            raise WorkspaceError(404, "TEAM_NOT_FOUND", "团队不存在或无权访问", {"team_id": team_id})
        return team

    def _find_team_member(self, team_id: str, member_id: str) -> StoredTeamMember:
        member = self._team_members.get(member_id)
        if not member or member.team_id != team_id or member.status != "active":
            raise WorkspaceError(404, "TEAM_MEMBER_NOT_FOUND", "团队成员不存在", {"team_id": team_id, "member_id": member_id})
        return member

    def _find_invite_by_token(self, token: str) -> StoredTeamInvite:
        for invite in self._team_invites.values():
            if hmac.compare_digest(invite.token, token):
                return invite
        raise WorkspaceError(404, "TEAM_INVITE_NOT_FOUND", "邀请不存在或已失效")

    def _team_membership(self, team_id: str | None, actor: UserPublic) -> StoredTeamMember | None:
        if not team_id:
            return None
        member = self._team_members.get(self._team_member_id(team_id, actor.id))
        if member and member.status == "active":
            return member
        return None

    def _require_team_member(self, team_id: str, actor: UserPublic) -> StoredTeamMember:
        membership = self._team_membership(team_id, actor)
        if not membership:
            raise WorkspaceError(403, "TEAM_ACCESS_DENIED", "没有访问该团队的权限", {"team_id": team_id})
        return membership

    def _require_team_manager(self, team_id: str, actor: UserPublic) -> StoredTeamMember:
        membership = self._require_team_member(team_id, actor)
        if membership.role not in {"owner", "admin"}:
            raise WorkspaceError(403, "TEAM_MANAGE_FORBIDDEN", "没有管理该团队的权限", {"team_id": team_id})
        return membership

    def _can_read_folder(self, folder: StoredFolder, actor: UserPublic) -> bool:
        if folder.scope == "personal":
            return True
        return self._team_membership(folder.team_id, actor) is not None

    def _ensure_can_write_folder(self, folder: StoredFolder, actor: UserPublic) -> None:
        if folder.scope == "personal":
            return
        membership = self._team_membership(folder.team_id, actor)
        if not membership:
            raise WorkspaceError(403, "TEAM_ACCESS_DENIED", "没有访问该团队文件夹的权限", {"folder_id": folder.id})
        if membership.role == "guest":
            raise WorkspaceError(403, "FOLDER_WRITE_FORBIDDEN", "当前角色只能查看团队文件夹", {"folder_id": folder.id})

    def _clean_team_name(self, name: str) -> str:
        cleaned = name.strip()
        if not cleaned:
            raise WorkspaceError(422, "TEAM_NAME_REQUIRED", "团队名称不能为空")
        return cleaned

    def _hash_password(self, password: str) -> str:
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), b"whu-workspace", 120_000)
        return base64.urlsafe_b64encode(digest).decode()

    def _create_token(self, user_id: int, kind: str) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": str(user_id),
            "kind": kind,
            "jti": secrets.token_hex(8),
            "exp": int((datetime.now(UTC) + timedelta(minutes=30)).timestamp()),
        }
        signing_input = f"{self._b64(header)}.{self._b64(payload)}"
        signature = hmac.new(self._secret.encode(), signing_input.encode(), hashlib.sha256).digest()
        return f"{signing_input}.{self._b64_bytes(signature)}"

    def _read_token(self, token: str, expected_kind: str) -> int:
        try:
            header_part, payload_part, signature_part = token.split(".")
        except ValueError as exc:
            raise WorkspaceError(401, "INVALID_TOKEN", "登录状态无效，请重新登录") from exc
        expected_signature = self._b64_bytes(
            hmac.new(self._secret.encode(), f"{header_part}.{payload_part}".encode(), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(signature_part, expected_signature):
            raise WorkspaceError(401, "INVALID_TOKEN", "登录状态无效，请重新登录")
        payload = json.loads(self._b64_decode(payload_part))
        if payload.get("kind") != expected_kind:
            raise WorkspaceError(401, "INVALID_TOKEN", "登录状态无效，请重新登录")
        if int(payload.get("exp", 0)) < int(datetime.now(UTC).timestamp()):
            raise WorkspaceError(401, "TOKEN_EXPIRED", "登录已过期，请重新登录")
        return int(payload["sub"])

    def _b64(self, payload: dict[str, Any]) -> str:
        return self._b64_bytes(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode())

    def _b64_bytes(self, payload: bytes) -> str:
        return base64.urlsafe_b64encode(payload).decode().rstrip("=")

    def _b64_decode(self, value: str) -> str:
        padded = value + "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode(padded.encode()).decode()

    def _record_audit(self, actor: str, action: str, resource_type: str, resource_name: str) -> None:
        self._audit_logs.append(
            AuditLogEntry(
                id=f"audit-{secrets.token_hex(4)}",
                actor=actor,
                action=action,
                resource_type=resource_type,
                resource_name=resource_name,
                created_at=datetime.now(UTC),
            )
        )

    def _ensure_login_not_locked(self, stored: StoredUser, now: datetime) -> None:
        locked_until = stored.security.locked_until
        if not locked_until:
            return
        if locked_until <= now:
            stored.security = LoginSecurityState()
            return
        raise WorkspaceError(423, "ACCOUNT_LOCKED", "账户已被临时锁定，请稍后再试", self._lockout_detail(stored.security, now))

    def _record_failed_login(self, stored: StoredUser, now: datetime) -> None:
        stored.security.failed_attempts += 1
        self._record_audit(stored.public.username, "auth.login_failed", "user", stored.public.username)
        if stored.security.failed_attempts >= LOGIN_FAILURE_LIMIT:
            stored.security.locked_until = now + LOGIN_LOCKOUT_DURATION
            self._record_audit(stored.public.username, "auth.account_locked", "user", stored.public.username)
            raise WorkspaceError(423, "ACCOUNT_LOCKED", "账户已被临时锁定，请稍后再试", self._lockout_detail(stored.security, now))
        raise WorkspaceError(
            401,
            "INVALID_CREDENTIALS",
            "用户名、邮箱或密码不正确",
            {
                "failed_attempts": stored.security.failed_attempts,
                "max_attempts": LOGIN_FAILURE_LIMIT,
                "remaining_attempts": LOGIN_FAILURE_LIMIT - stored.security.failed_attempts,
            },
        )

    def _lockout_detail(self, state: LoginSecurityState, now: datetime) -> dict[str, Any]:
        locked_until = state.locked_until or now
        retry_after_seconds = max(0, int((locked_until - now).total_seconds()))
        return {
            "failed_attempts": state.failed_attempts,
            "locked_until": locked_until.isoformat(),
            "max_attempts": LOGIN_FAILURE_LIMIT,
            "retry_after_seconds": retry_after_seconds,
        }

    def _find_file(self, file_id: str) -> FileItem:
        for file_item in self._files:
            if file_item.id == file_id:
                return file_item
        raise WorkspaceError(404, "FILE_NOT_FOUND", "文件不存在或无权访问", {"file_id": file_id})

    def _read_file_content(self, file_id: str) -> bytes:
        content = self._file_contents.get(file_id)
        if content is None:
            raise WorkspaceError(404, "FILE_NOT_FOUND", "文件不存在或无权访问", {"file_id": file_id})
        return content

    def _find_file_by_name_in_folder(self, name: str, folder_id: str) -> FileItem | None:
        for file_item in self._files:
            if file_item.folder_id == folder_id and file_item.name == name:
                return file_item
        return None

    def _replace_file(self, file_item: FileItem, move_to_front: bool = False) -> None:
        remaining = [candidate for candidate in self._files if candidate.id != file_item.id]
        if move_to_front:
            self._files = [file_item, *remaining]
            return
        self._files = [file_item if candidate.id == file_item.id else candidate for candidate in self._files]

    def _ensure_file_target_folder(self, file_item: FileItem, target_folder_id: str, actor: UserPublic) -> StoredFolder:
        target_folder = self._find_folder(target_folder_id)
        source_scope = self._file_scope(file_item)
        if target_folder.scope != source_scope:
            raise WorkspaceError(
                409,
                "FILE_SCOPE_MISMATCH",
                "不能跨个人空间和团队空间移动或复制文件",
                {"file_id": file_item.id, "target_folder_id": target_folder_id},
            )
        self._ensure_can_write_folder(target_folder, actor)
        return target_folder

    def _file_scope(self, file_item: FileItem) -> str:
        folder = self._folders.get(file_item.folder_id)
        if folder:
            return folder.scope
        return "team" if file_item.permission_scope == "团队" else "personal"

    def _find_folder(self, folder_id: str) -> StoredFolder:
        folder = self._folders.get(folder_id)
        if not folder:
            raise WorkspaceError(404, "FOLDER_NOT_FOUND", "文件夹不存在或无权访问", {"folder_id": folder_id})
        return folder

    def _folder_item(self, folder: StoredFolder, actor: UserPublic) -> FolderItem:
        return FolderItem(
            id=folder.id,
            name=folder.name,
            parent_id=folder.parent_id,
            scope=folder.scope,  # type: ignore[arg-type]
            permission=folder.permission,
            team_id=folder.team_id,
            children=[
                self._folder_item(child, actor)
                for child in self._folders.values()
                if child.parent_id == folder.id and self._can_read_folder(child, actor)
            ],
        )

    def _ensure_mutable_folder(self, folder: StoredFolder) -> None:
        if folder.parent_id is None:
            raise WorkspaceError(
                409,
                "FOLDER_ROOT_PROTECTED",
                "根文件夹不能重命名、移动或删除",
                {"folder_id": folder.id},
            )

    def _ensure_valid_folder_move(self, folder: StoredFolder, parent_id: str) -> None:
        parent = self._find_folder(parent_id)
        if parent.scope != folder.scope:
            raise WorkspaceError(
                409,
                "FOLDER_SCOPE_MISMATCH",
                "不能跨个人空间和团队空间移动文件夹",
                {"folder_id": folder.id, "parent_id": parent_id},
            )
        if parent.id == folder.id or self._is_descendant(parent.id, folder.id):
            raise WorkspaceError(
                409,
                "FOLDER_CYCLE",
                "不能把文件夹移动到自己或子文件夹下",
                {"folder_id": folder.id, "parent_id": parent_id},
            )

    def _is_descendant(self, candidate_id: str, ancestor_id: str) -> bool:
        current = self._folders.get(candidate_id)
        while current and current.parent_id:
            if current.parent_id == ancestor_id:
                return True
            current = self._folders.get(current.parent_id)
        return False

    def _clean_folder_name(self, name: str) -> str:
        cleaned = name.strip()
        if not cleaned:
            raise WorkspaceError(422, "FOLDER_NAME_REQUIRED", "文件夹名称不能为空")
        return cleaned

    def _clean_file_name(self, name: str) -> str:
        cleaned = name.strip()
        if not cleaned:
            raise WorkspaceError(422, "FILE_NAME_REQUIRED", "文件名不能为空")
        if "/" in cleaned or "\\" in cleaned:
            raise WorkspaceError(422, "FILE_NAME_INVALID", "文件名不能包含路径分隔符", {"name": name})
        return cleaned

    def _normalize_tags(self, tags: list[str]) -> list[str]:
        normalized: list[str] = []
        for tag in tags:
            cleaned = tag.strip()
            if cleaned and cleaned not in normalized:
                normalized.append(cleaned)
        return normalized

    def _permission_scope_for_folder(self, folder: StoredFolder) -> str:
        return "团队" if folder.scope == "team" else "个人"

    def _copy_file_name(self, filename: str) -> str:
        if "." not in filename:
            return f"{filename} 副本"
        stem, suffix = filename.rsplit(".", 1)
        return f"{stem} 副本.{suffix}"

    def _file_type(self, filename: str) -> str:
        suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else "unknown"
        return {"md": "markdown", "txt": "text", "pdf": "pdf", "docx": "docx", "pptx": "pptx", "csv": "csv"}.get(
            suffix, suffix
        )

    def _new_file_id(self, digest: str) -> str:
        existing_ids = {file_item.id for file_item in self._files}
        base_id = f"file-{digest[:12]}"
        candidate = base_id
        index = 2
        while candidate in existing_ids:
            candidate = f"{base_id}-{index}"
            index += 1
        return candidate

    def _append_file_version(self, file_item: FileItem, name: str, content: bytes, actor: str) -> StoredFileVersion:
        version = self._make_file_version(file_item, name, content, actor)
        self._file_versions.setdefault(file_item.id, []).append(version)
        self._record_audit(actor, "file.version_create", "file", file_item.name)
        return version

    def _make_file_version(self, file_item: FileItem, name: str, content: bytes, actor: str) -> StoredFileVersion:
        existing_versions = self._file_versions.get(file_item.id, [])
        version_no = max((version.version_no for version in existing_versions), default=0) + 1
        digest = hashlib.sha256(content).hexdigest()
        return StoredFileVersion(
            id=f"{file_item.id}-v{version_no}-{secrets.token_hex(3)}",
            file_id=file_item.id,
            version_no=version_no,
            name=name,
            content=content,
            sha256=digest,
            size=len(content),
            created_at=datetime.now(UTC),
            created_by=actor,
        )

    def _find_file_version(self, file_id: str, version_id: str) -> StoredFileVersion:
        self._find_file(file_id)
        for version in self._file_versions.get(file_id, []):
            if version.id == version_id:
                return version
        raise WorkspaceError(
            404,
            "FILE_VERSION_NOT_FOUND",
            "文件版本不存在或无权访问",
            {"file_id": file_id, "version_id": version_id},
        )

    def _file_version_item(self, version: StoredFileVersion, current_version_no: int) -> FileVersionItem:
        return FileVersionItem(
            id=version.id,
            file_id=version.file_id,
            version_no=version.version_no,
            name=version.name,
            size=version.size,
            sha256=version.sha256,
            created_at=version.created_at,
            created_by=version.created_by,
            is_current=version.version_no == current_version_no,
        )

    def _seed_files(self) -> list[FileItem]:
        now = datetime.now(UTC)
        return [
            FileItem(
                id="file-microscope",
                name="显微镜实验报告.pdf",
                folder_id="folder-biology",
                type="pdf",
                size=2_430_112,
                sha256="8b73c9d2d4c02b4b4f0e1c7a8dbf1023f44e8d9e7a10f24b15a02d983ff42d91",
                parse_status="indexed",
                tags=["实验", "显微镜"],
                updated_at=now - timedelta(hours=2),
                permission_scope="个人",
                knowledge_base_ids=["kb-biology"],
            ),
            FileItem(
                id="file-requirements",
                name="需求规格说明书.md",
                folder_id="folder-course",
                type="markdown",
                size=96_418,
                sha256="fb8bd33418f0d6a73f83341f1f3bbef710c66f6a73e4c4afece8e7dfcb71b884",
                parse_status="indexed",
                tags=["课程", "需求"],
                updated_at=now - timedelta(days=1),
                permission_scope="团队",
                knowledge_base_ids=["kb-course"],
            ),
            FileItem(
                id="file-weekly",
                name="小组周报.docx",
                folder_id="team-root",
                type="docx",
                size=384_200,
                sha256="d654611a21f65bbdcad7f0c96da59e267674b0d806f65220b46fbf35d94a826b",
                parse_status="parsing",
                tags=["周报", "团队"],
                updated_at=now - timedelta(minutes=35),
                permission_scope="团队",
                knowledge_base_ids=[],
            ),
        ]

    def _seed_folders(self) -> dict[str, StoredFolder]:
        folders = [
            StoredFolder(id="personal-root", name="个人文件", parent_id=None, scope="personal", permission="管理"),
            StoredFolder(id="folder-biology", name="生物学实验", parent_id="personal-root", scope="personal", permission="管理"),
            StoredFolder(id="folder-course", name="软件工程课程", parent_id="personal-root", scope="personal", permission="管理"),
            StoredFolder(
                id="team-root",
                name="团队文件",
                parent_id=None,
                scope="team",
                permission="读写",
                team_id="team-demo",
            ),
        ]
        return {folder.id: folder for folder in folders}

    def _seed_teams(self) -> dict[str, StoredTeam]:
        return {
            "team-demo": StoredTeam(
                id="team-demo",
                name="团队文件",
                description="演示团队空间",
                root_folder_id="team-root",
                created_by=0,
                created_at=datetime.now(UTC),
                unread_count=0,
            )
        }

    def _seed_file_contents(self) -> dict[str, bytes]:
        return {
            "file-microscope": "显微镜实验报告.pdf\n显微镜实验包含取样、制片、观察和结果记录。".encode(),
            "file-requirements": "需求规格说明书.md\n系统需要支持文件管理、知识库问答和团队协作。".encode(),
            "file-weekly": "小组周报.docx\n本周完成文件解析、RAG 问答和工作流联调。".encode(),
        }

    def _seed_file_versions(self) -> dict[str, list[StoredFileVersion]]:
        versions: dict[str, list[StoredFileVersion]] = {}
        for file_item in self._files:
            content = self._file_contents[file_item.id]
            versions[file_item.id] = [
                StoredFileVersion(
                    id=f"{file_item.id}-v1",
                    file_id=file_item.id,
                    version_no=1,
                    name=file_item.name,
                    content=content,
                    sha256=file_item.sha256,
                    size=file_item.size,
                    created_at=file_item.updated_at,
                    created_by="system",
                )
            ]
        return versions


workspace_service = WorkspaceService()
