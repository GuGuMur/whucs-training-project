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
    KnowledgeBaseCreate,
    KnowledgeBasePublic,
    KnowledgeBaseUpdate,
    KnowledgeDocumentCreate,
    KnowledgeDocumentPublic,
    PermissionRuleCreate,
    PermissionRulePublic,
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
    WorkflowCreate,
    WorkflowDefinition,
    WorkflowEdgeDefinition,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowNodeDefinition,
    WorkflowNodeExecution,
    WorkflowUpdate,
    WorkflowValidationIssue,
    WorkflowValidationResponse,
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


@dataclass
class StoredKnowledgeChunk:
    id: str
    content: str
    page_no: int
    paragraph_no: int


@dataclass
class StoredKnowledgeBase:
    id: str
    name: str
    description: str
    status: str
    owner_id: int | None
    created_at: datetime
    updated_at: datetime


@dataclass
class StoredKnowledgeDocument:
    id: str
    kb_id: str
    file_id: str
    file_name: str
    index_status: str
    chunks: list[StoredKnowledgeChunk]
    updated_at: datetime


@dataclass
class StoredWorkflow:
    id: str
    name: str
    description: str
    trigger: str
    version: str
    status: str
    nodes: list[WorkflowNodeDefinition]
    edges: list[WorkflowEdgeDefinition]
    created_by: int | None
    updated_at: datetime


@dataclass
class StoredPermissionRule:
    id: str
    subject_type: str
    subject_id: str
    resource_type: str
    resource_id: str
    action: str
    effect: str
    inherit: bool
    created_at: datetime
    created_by: str


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
        self._knowledge_bases = self._seed_knowledge_bases()
        self._knowledge_documents = self._seed_knowledge_documents()
        self._workflows = self._seed_workflows()
        self._teams = self._seed_teams()
        self._team_members: dict[str, StoredTeamMember] = {}
        self._team_invites: dict[str, StoredTeamInvite] = {}
        self._permission_rules: dict[str, StoredPermissionRule] = {}
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

    def list_files(
        self,
        actor: UserPublic,
        query: str | None = None,
        tag: str | None = None,
        file_type: str | None = None,
    ) -> list[FileItem]:
        files = [file for file in self._files if self._can_read_file(file, actor)]
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
        self._ensure_can_write_file(file_item, actor)
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
        self._ensure_can_read_file(source, actor)
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
        self._ensure_can_read_file(file_item, actor)
        content = self._read_file_content(file_id)
        self._record_audit(actor.username, "file.download", "file", file_item.name)
        return file_item, content

    def list_file_versions(self, file_id: str, actor: UserPublic) -> list[FileVersionItem]:
        file_item = self._find_file(file_id)
        self._ensure_can_read_file(file_item, actor)
        versions = self._file_versions.get(file_id, [])
        current_version_no = max((version.version_no for version in versions), default=0)
        return [
            self._file_version_item(version, current_version_no)
            for version in sorted(versions, key=lambda item: item.version_no, reverse=True)
        ]

    def restore_file_version(self, file_id: str, version_id: str, actor: UserPublic) -> FileItem:
        file_item = self._find_file(file_id)
        self._ensure_can_write_file(file_item, actor)
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
        self._ensure_can_write_file(file_item, actor)
        self._files = [candidate for candidate in self._files if candidate.id != file_id]
        self._file_contents.pop(file_id, None)
        self._file_versions.pop(file_id, None)
        self._record_audit(actor.username, "file.delete", "file", file_item.name)

    def list_knowledge_bases(self, actor: UserPublic) -> list[KnowledgeBasePublic]:
        return [
            self._knowledge_base_public(knowledge_base)
            for knowledge_base in self._knowledge_bases.values()
            if self._can_read_knowledge_base(knowledge_base, actor)
        ]

    def create_knowledge_base(self, payload: KnowledgeBaseCreate, actor: UserPublic) -> KnowledgeBasePublic:
        now = datetime.now(UTC)
        knowledge_base = StoredKnowledgeBase(
            id=self._new_knowledge_base_id(payload.name),
            name=self._clean_knowledge_base_name(payload.name),
            description=(payload.description or "").strip(),
            status="active",
            owner_id=actor.id,
            created_at=now,
            updated_at=now,
        )
        self._knowledge_bases[knowledge_base.id] = knowledge_base
        self._record_audit(actor.username, "knowledge_base.create", "knowledge_base", knowledge_base.name)
        return self._knowledge_base_public(knowledge_base)

    def update_knowledge_base(
        self,
        kb_id: str,
        payload: KnowledgeBaseUpdate,
        actor: UserPublic,
    ) -> KnowledgeBasePublic:
        knowledge_base = self._find_knowledge_base(kb_id, actor)
        self._ensure_can_manage_knowledge_base(knowledge_base, actor)

        if "name" in payload.model_fields_set and payload.name is not None:
            knowledge_base.name = self._clean_knowledge_base_name(payload.name)
        if "description" in payload.model_fields_set:
            knowledge_base.description = (payload.description or "").strip()
        if "status" in payload.model_fields_set and payload.status is not None:
            knowledge_base.status = payload.status

        knowledge_base.updated_at = datetime.now(UTC)
        self._record_audit(actor.username, "knowledge_base.update", "knowledge_base", knowledge_base.name)
        return self._knowledge_base_public(knowledge_base)

    def list_knowledge_documents(self, kb_id: str, actor: UserPublic) -> list[KnowledgeDocumentPublic]:
        self._find_knowledge_base(kb_id, actor)
        return [
            self._knowledge_document_public(document)
            for document in self._knowledge_documents.values()
            if document.kb_id == kb_id
        ]

    def add_knowledge_document(
        self,
        kb_id: str,
        payload: KnowledgeDocumentCreate,
        actor: UserPublic,
    ) -> KnowledgeDocumentPublic:
        knowledge_base = self._find_knowledge_base(kb_id, actor)
        self._ensure_can_manage_knowledge_base(knowledge_base, actor)
        if knowledge_base.status == "archived":
            raise WorkspaceError(409, "KNOWLEDGE_BASE_ARCHIVED", "知识库已归档，不能继续添加文档", {"kb_id": kb_id})

        file_item = self._find_file(payload.file_id)
        self._ensure_can_read_file(file_item, actor)
        content = self._read_file_content(file_item.id)
        now = datetime.now(UTC)
        document_id = self._knowledge_document_id(kb_id, file_item.id)
        document = StoredKnowledgeDocument(
            id=document_id,
            kb_id=kb_id,
            file_id=file_item.id,
            file_name=file_item.name,
            index_status="indexed",
            chunks=self._chunk_file_content(document_id, file_item, content),
            updated_at=now,
        )
        self._knowledge_documents[document.id] = document
        knowledge_base.updated_at = now
        self._mark_file_indexed_in_knowledge_base(file_item, kb_id, now)
        self._record_audit(actor.username, "knowledge_base.add_document", "knowledge_base", knowledge_base.name)
        return self._knowledge_document_public(document)

    def answer_question(self, payload: QARequest, actor: UserPublic) -> QAResponse:
        knowledge_base = self._find_knowledge_base(payload.kb_id, actor)
        citations = self._retrieve_knowledge_citations(knowledge_base.id, payload.question, payload.top_k, actor)
        answer = self._compose_rag_answer(knowledge_base, payload.question, citations)
        self._record_audit(actor.username, "qa.query", "knowledge_base", payload.kb_id)
        return QAResponse(
            conversation_id=payload.conversation_id or "conv-biology",
            message_id=f"msg-{secrets.token_hex(4)}",
            answer=answer,
            citations=citations,
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
        if payload.kb_id:
            self._find_knowledge_base(payload.kb_id, actor)
        for file_id in payload.context_file_ids:
            self._ensure_can_read_file(self._find_file(file_id), actor)

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
        return [self._workflow_definition(workflow) for workflow in self._workflows.values()]

    def create_workflow(self, payload: WorkflowCreate, actor: UserPublic) -> WorkflowDefinition:
        workflow = StoredWorkflow(
            id=self._new_workflow_id(payload.name),
            name=self._clean_workflow_name(payload.name),
            description=(payload.description or "").strip(),
            trigger=payload.trigger.strip(),
            version="0.1.0",
            status="draft",
            nodes=list(payload.nodes),
            edges=list(payload.edges),
            created_by=actor.id,
            updated_at=datetime.now(UTC),
        )
        self._workflows[workflow.id] = workflow
        self._record_audit(actor.username, "workflow.create", "workflow", workflow.name)
        return self._workflow_definition(workflow)

    def update_workflow(self, workflow_id: str, payload: WorkflowUpdate, actor: UserPublic) -> WorkflowDefinition:
        workflow = self._find_workflow(workflow_id)
        if "name" in payload.model_fields_set and payload.name is not None:
            workflow.name = self._clean_workflow_name(payload.name)
        if "description" in payload.model_fields_set:
            workflow.description = (payload.description or "").strip()
        if "trigger" in payload.model_fields_set and payload.trigger is not None:
            workflow.trigger = payload.trigger.strip()
        if "nodes" in payload.model_fields_set and payload.nodes is not None:
            workflow.nodes = list(payload.nodes)
            workflow.status = "draft"
        if "edges" in payload.model_fields_set and payload.edges is not None:
            workflow.edges = list(payload.edges)
            workflow.status = "draft"
        workflow.updated_at = datetime.now(UTC)
        self._record_audit(actor.username, "workflow.update", "workflow", workflow.name)
        return self._workflow_definition(workflow)

    def validate_workflow(self, workflow_id: str, actor: UserPublic) -> WorkflowValidationResponse:
        workflow = self._find_workflow(workflow_id)
        validation = self._validate_workflow_definition(workflow)
        self._record_audit(actor.username, "workflow.validate", "workflow", workflow.name)
        return validation

    def publish_workflow(self, workflow_id: str, actor: UserPublic) -> WorkflowDefinition:
        workflow = self._find_workflow(workflow_id)
        validation = self._validate_workflow_definition(workflow)
        if not validation.valid:
            raise WorkspaceError(
                409,
                "WORKFLOW_INVALID",
                "流程定义校验未通过，不能发布",
                {
                    "issue_count": len(validation.issues),
                    "issues": [issue.model_dump() for issue in validation.issues],
                },
            )
        workflow.status = "published"
        workflow.version = "1.0.0" if workflow.version == "0.1.0" else workflow.version
        workflow.updated_at = datetime.now(UTC)
        self._record_audit(actor.username, "workflow.publish", "workflow", workflow.name)
        return self._workflow_definition(workflow)

    def execute_workflow(
        self,
        workflow_id: str,
        payload: WorkflowExecutionRequest,
        actor: UserPublic,
    ) -> WorkflowExecutionResponse:
        workflow = self._find_workflow(workflow_id)
        if workflow.status != "published":
            raise WorkspaceError(409, "WORKFLOW_NOT_PUBLISHED", "流程尚未发布，不能执行", {"workflow_id": workflow_id})
        validation = self._validate_workflow_definition(workflow)
        if not validation.valid:
            raise WorkspaceError(
                409,
                "WORKFLOW_INVALID",
                "流程定义校验未通过，不能执行",
                {"issue_count": len(validation.issues)},
            )
        file_item = self._find_file(payload.file_id)
        self._ensure_can_read_file(file_item, actor)
        if payload.target_kb_id:
            self._find_knowledge_base(payload.target_kb_id, actor)
        nodes = [
            self._execute_workflow_node(node, payload)
            for node in self._workflow_execution_order(workflow)
        ]
        if workflow_id == "new-file-auto-summary":
            summary = f"{file_item.name} 已完成自动摘要：文档围绕显微镜实验步骤、观察记录和结论整理。"
        else:
            summary = f"{workflow.name} 已完成：基于 {file_item.name} 生成流程输出。"
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

    def list_permission_rules(self, actor: UserPublic) -> list[PermissionRulePublic]:
        return [
            self._permission_rule_public(rule)
            for rule in self._permission_rules.values()
            if self._can_manage_permission_resource(rule.resource_type, rule.resource_id, actor)
        ]

    def create_permission_rule(self, payload: PermissionRuleCreate, actor: UserPublic) -> PermissionRulePublic:
        self._validate_permission_subject(payload.subject_type, payload.subject_id)
        self._ensure_can_manage_permission_resource(payload.resource_type, payload.resource_id, actor)
        rule = StoredPermissionRule(
            id=f"rule-{secrets.token_hex(4)}",
            subject_type=payload.subject_type,
            subject_id=payload.subject_id,
            resource_type=payload.resource_type,
            resource_id=payload.resource_id,
            action=payload.action,
            effect=payload.effect,
            inherit=payload.inherit,
            created_at=datetime.now(UTC),
            created_by=actor.username,
        )
        self._permission_rules[rule.id] = rule
        self._record_audit(actor.username, "permission.rule_create", "permission_rule", rule.id)
        return self._permission_rule_public(rule)

    def delete_permission_rule(self, rule_id: str, actor: UserPublic) -> None:
        rule = self._permission_rules.get(rule_id)
        if not rule:
            raise WorkspaceError(404, "PERMISSION_RULE_NOT_FOUND", "权限规则不存在", {"rule_id": rule_id})
        self._ensure_can_manage_permission_resource(rule.resource_type, rule.resource_id, actor)
        self._permission_rules.pop(rule_id)
        self._record_audit(actor.username, "permission.rule_delete", "permission_rule", rule.id)

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
        files = self.list_files(actor)
        teams = self.list_teams(actor)
        return WorkspaceSnapshot(
            summary=DashboardSummary(
                file_count=len(files),
                indexed_count=sum(1 for file in files if file.parse_status == "indexed"),
                knowledge_base_count=len(self.list_knowledge_bases(actor)),
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

    def _knowledge_base_public(self, knowledge_base: StoredKnowledgeBase) -> KnowledgeBasePublic:
        documents = [
            document
            for document in self._knowledge_documents.values()
            if document.kb_id == knowledge_base.id
        ]
        updated_at = max(
            [knowledge_base.updated_at, *(document.updated_at for document in documents)],
            default=knowledge_base.updated_at,
        )
        return KnowledgeBasePublic(
            id=knowledge_base.id,
            name=knowledge_base.name,
            description=knowledge_base.description,
            status=knowledge_base.status,  # type: ignore[arg-type]
            document_count=len(documents),
            chunk_count=sum(len(document.chunks) for document in documents),
            updated_at=updated_at,
        )

    def _knowledge_document_public(self, document: StoredKnowledgeDocument) -> KnowledgeDocumentPublic:
        return KnowledgeDocumentPublic(
            id=document.id,
            kb_id=document.kb_id,
            file_id=document.file_id,
            file_name=document.file_name,
            index_status=document.index_status,  # type: ignore[arg-type]
            chunk_count=len(document.chunks),
            updated_at=document.updated_at,
        )

    def _find_knowledge_base(self, kb_id: str, actor: UserPublic) -> StoredKnowledgeBase:
        knowledge_base = self._knowledge_bases.get(kb_id)
        if not knowledge_base or not self._can_read_knowledge_base(knowledge_base, actor):
            raise WorkspaceError(404, "KNOWLEDGE_BASE_NOT_FOUND", "知识库不存在或无权访问", {"kb_id": kb_id})
        return knowledge_base

    def _can_read_knowledge_base(self, knowledge_base: StoredKnowledgeBase, actor: UserPublic) -> bool:
        return knowledge_base.owner_id is None or knowledge_base.owner_id == actor.id

    def _ensure_can_manage_knowledge_base(self, knowledge_base: StoredKnowledgeBase, actor: UserPublic) -> None:
        if knowledge_base.owner_id is not None and knowledge_base.owner_id != actor.id:
            raise WorkspaceError(403, "KNOWLEDGE_BASE_MANAGE_FORBIDDEN", "没有管理该知识库的权限", {"kb_id": knowledge_base.id})

    def _new_knowledge_base_id(self, name: str) -> str:
        existing_ids = set(self._knowledge_bases)
        normalized = "".join(ch.lower() for ch in name.strip() if ch.isascii() and ch.isalnum())[:18]
        base_id = f"kb-{normalized}" if normalized else f"kb-{secrets.token_hex(4)}"
        candidate = base_id
        index = 2
        while candidate in existing_ids:
            candidate = f"{base_id}-{index}"
            index += 1
        return candidate

    def _clean_knowledge_base_name(self, name: str) -> str:
        cleaned = name.strip()
        if not cleaned:
            raise WorkspaceError(422, "KNOWLEDGE_BASE_NAME_REQUIRED", "知识库名称不能为空")
        return cleaned

    def _knowledge_document_id(self, kb_id: str, file_id: str) -> str:
        return f"doc-{kb_id}-{file_id}"

    def _chunk_file_content(
        self,
        document_id: str,
        file_item: FileItem,
        content: bytes,
    ) -> list[StoredKnowledgeChunk]:
        text = content.decode("utf-8", errors="ignore").strip() or file_item.name
        for separator in ("\r\n", "\r", "\n", "。", "！", "？", "!", "?"):
            text = text.replace(separator, "\n")
        parts = [part.strip() for part in text.split("\n") if part.strip()]
        return [
            StoredKnowledgeChunk(
                id=f"{document_id}-chunk-{index}",
                content=part,
                page_no=1,
                paragraph_no=index,
            )
            for index, part in enumerate(parts, start=1)
        ]

    def _mark_file_indexed_in_knowledge_base(self, file_item: FileItem, kb_id: str, updated_at: datetime) -> None:
        knowledge_base_ids = [*file_item.knowledge_base_ids]
        if kb_id not in knowledge_base_ids:
            knowledge_base_ids.append(kb_id)
        updated = file_item.model_copy(
            update={
                "knowledge_base_ids": knowledge_base_ids,
                "parse_status": "indexed",
                "updated_at": updated_at,
            }
        )
        self._replace_file(updated)

    def _retrieve_knowledge_citations(
        self,
        kb_id: str,
        question: str,
        top_k: int,
        actor: UserPublic,
    ) -> list[Citation]:
        ranked_chunks: list[tuple[int, StoredKnowledgeDocument, StoredKnowledgeChunk]] = []
        for document in self._knowledge_documents.values():
            if document.kb_id != kb_id or document.index_status != "indexed":
                continue
            file_item = self._find_file(document.file_id)
            if not self._can_read_file(file_item, actor):
                continue
            for chunk in document.chunks:
                ranked_chunks.append((self._chunk_score(question, chunk.content), document, chunk))

        ranked_chunks.sort(key=lambda item: item[0], reverse=True)
        selected = [item for item in ranked_chunks if item[0] > 0][:top_k]
        if not selected:
            selected = ranked_chunks[:top_k]

        return [
            Citation(
                file_id=document.file_id,
                document_id=document.id,
                chunk_id=chunk.id,
                title=document.file_name,
                page_no=chunk.page_no,
                paragraph_no=chunk.paragraph_no,
                snippet=chunk.content,
            )
            for _, document, chunk in selected
        ]

    def _chunk_score(self, question: str, content: str) -> int:
        question_chars = self._search_chars(question)
        content_chars = self._search_chars(content)
        overlap = len(question_chars & content_chars)
        compact_question = "".join(ch for ch in question.lower() if not ch.isspace())
        compact_content = "".join(ch for ch in content.lower() if not ch.isspace())
        return overlap + (10 if compact_question and compact_question in compact_content else 0)

    def _search_chars(self, value: str) -> set[str]:
        ignored = set(" ，。；：、！？!?()（）[]【】,.:-_")
        return {ch.lower() for ch in value if ch.strip() and ch not in ignored}

    def _compose_rag_answer(
        self,
        knowledge_base: StoredKnowledgeBase,
        question: str,
        citations: list[Citation],
    ) -> str:
        if not citations:
            return f"知识库「{knowledge_base.name}」暂未检索到与“{question}”直接相关的已索引片段。"
        if any("显微镜" in citation.snippet for citation in citations):
            return (
                "显微镜相关实验步骤包括：准备载玻片与样本，低倍镜定位目标区域，"
                "切换高倍镜观察细胞结构，记录视野特征，并在实验报告中附上观察结论。"
            )
        snippets = "；".join(citation.snippet for citation in citations[:2])
        return f"根据知识库「{knowledge_base.name}」的已索引片段，{snippets}"

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

    def _workflow_definition(self, workflow: StoredWorkflow) -> WorkflowDefinition:
        return WorkflowDefinition(
            id=workflow.id,
            name=workflow.name,
            description=workflow.description,
            trigger=workflow.trigger,
            version=workflow.version,
            node_count=len(workflow.nodes),
            status=workflow.status,  # type: ignore[arg-type]
            nodes=list(workflow.nodes),
            edges=list(workflow.edges),
        )

    def _find_workflow(self, workflow_id: str) -> StoredWorkflow:
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise WorkspaceError(404, "WORKFLOW_NOT_FOUND", "流程不存在", {"workflow_id": workflow_id})
        return workflow

    def _validate_workflow_definition(self, workflow: StoredWorkflow) -> WorkflowValidationResponse:
        issues: list[WorkflowValidationIssue] = []
        node_ids: set[str] = set()
        duplicated_node_ids: set[str] = set()
        tool_names = {tool.name for tool in self.list_tools()}

        if not workflow.nodes:
            issues.append(WorkflowValidationIssue(code="WORKFLOW_EMPTY", message="流程至少需要 1 个节点"))

        for node in workflow.nodes:
            if node.id in node_ids:
                duplicated_node_ids.add(node.id)
                issues.append(
                    WorkflowValidationIssue(
                        code="WORKFLOW_DUPLICATE_NODE",
                        message="节点 ID 不能重复",
                        node_id=node.id,
                    )
                )
            node_ids.add(node.id)
            if node.type == "tool" and not node.tool_name:
                issues.append(
                    WorkflowValidationIssue(
                        code="WORKFLOW_TOOL_REQUIRED",
                        message="工具节点必须选择工具",
                        node_id=node.id,
                    )
                )
            if node.type == "tool" and node.tool_name and node.tool_name not in tool_names:
                issues.append(
                    WorkflowValidationIssue(
                        code="WORKFLOW_TOOL_UNKNOWN",
                        message="工具节点引用了未注册工具",
                        node_id=node.id,
                    )
                )

        degree = {node.id: 0 for node in workflow.nodes if node.id not in duplicated_node_ids}
        adjacency = {node_id: [] for node_id in degree}
        indegree = {node_id: 0 for node_id in degree}

        for edge in workflow.edges:
            if edge.source not in degree:
                issues.append(
                    WorkflowValidationIssue(
                        code="WORKFLOW_EDGE_SOURCE_MISSING",
                        message="连线起点不存在",
                        edge_id=edge.id,
                    )
                )
                continue
            if edge.target not in degree:
                issues.append(
                    WorkflowValidationIssue(
                        code="WORKFLOW_EDGE_TARGET_MISSING",
                        message="连线终点不存在",
                        edge_id=edge.id,
                    )
                )
                continue
            degree[edge.source] += 1
            degree[edge.target] += 1
            adjacency[edge.source].append(edge.target)
            indegree[edge.target] += 1

        if len(workflow.nodes) > 1:
            for node in workflow.nodes:
                if node.id in degree and degree[node.id] == 0:
                    issues.append(
                        WorkflowValidationIssue(
                            code="WORKFLOW_ISOLATED_NODE",
                            message="多节点流程中不能存在孤立节点",
                            node_id=node.id,
                        )
                    )

        if degree and self._workflow_has_cycle(adjacency, indegree):
            issues.append(WorkflowValidationIssue(code="WORKFLOW_CYCLE", message="流程连线存在环，不能形成 DAG"))

        return WorkflowValidationResponse(
            valid=not issues,
            issues=issues,
            node_count=len(workflow.nodes),
            edge_count=len(workflow.edges),
        )

    def _workflow_has_cycle(self, adjacency: dict[str, list[str]], indegree: dict[str, int]) -> bool:
        queue = [node_id for node_id, count in indegree.items() if count == 0]
        visited = 0
        while queue:
            node_id = queue.pop(0)
            visited += 1
            for target_id in adjacency[node_id]:
                indegree[target_id] -= 1
                if indegree[target_id] == 0:
                    queue.append(target_id)
        return visited != len(indegree)

    def _workflow_execution_order(self, workflow: StoredWorkflow) -> list[WorkflowNodeDefinition]:
        node_by_id = {node.id: node for node in workflow.nodes}
        adjacency = {node.id: [] for node in workflow.nodes}
        indegree = {node.id: 0 for node in workflow.nodes}
        for edge in workflow.edges:
            if edge.source in adjacency and edge.target in indegree:
                adjacency[edge.source].append(edge.target)
                indegree[edge.target] += 1

        queue = [node.id for node in workflow.nodes if indegree[node.id] == 0]
        ordered_ids: list[str] = []
        while queue:
            node_id = queue.pop(0)
            ordered_ids.append(node_id)
            for target_id in adjacency[node_id]:
                indegree[target_id] -= 1
                if indegree[target_id] == 0:
                    queue.append(target_id)

        if len(ordered_ids) != len(workflow.nodes):
            return workflow.nodes
        return [node_by_id[node_id] for node_id in ordered_ids]

    def _execute_workflow_node(
        self,
        node: WorkflowNodeDefinition,
        payload: WorkflowExecutionRequest,
    ) -> WorkflowNodeExecution:
        tool_name = node.tool_name or node.type
        node_input = {"file_id": payload.file_id, **node.parameters}
        if node.tool_name == "file_search":
            output = {"matched_files": 1}
        elif node.tool_name == "knowledge_qa":
            output = {"kb_id": payload.target_kb_id or "kb-biology", "citations": 1}
        elif node.tool_name == "report_generate":
            output = {"format": node.parameters.get("format", "markdown")}
        elif node.type == "output":
            output = {"stored": True}
        else:
            output = {"accepted": True}
        return WorkflowNodeExecution(
            node_id=node.id,
            name=node.name,
            tool_name=tool_name,
            status="success",
            input=node_input,
            output=output,
        )

    def _clean_workflow_name(self, name: str) -> str:
        cleaned = name.strip()
        if not cleaned:
            raise WorkspaceError(422, "WORKFLOW_NAME_REQUIRED", "流程名称不能为空")
        return cleaned

    def _new_workflow_id(self, name: str) -> str:
        base = "".join(character.lower() if character.isalnum() else "-" for character in name.strip())
        base = "-".join(part for part in base.split("-") if part)[:40] or "workflow"
        candidate = f"workflow-{base}"
        index = 2
        while candidate in self._workflows:
            candidate = f"workflow-{base}-{index}"
            index += 1
        return candidate

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

    def _permission_rule_public(self, rule: StoredPermissionRule) -> PermissionRulePublic:
        return PermissionRulePublic(
            id=rule.id,
            subject_type=rule.subject_type,  # type: ignore[arg-type]
            subject_id=rule.subject_id,
            subject_label=self._permission_subject_label(rule.subject_type, rule.subject_id),
            resource_type=rule.resource_type,  # type: ignore[arg-type]
            resource_id=rule.resource_id,
            resource_label=self._permission_resource_label(rule.resource_type, rule.resource_id),
            action=rule.action,  # type: ignore[arg-type]
            effect=rule.effect,  # type: ignore[arg-type]
            inherit=rule.inherit,
            created_at=rule.created_at,
            created_by=rule.created_by,
        )

    def _validate_permission_subject(self, subject_type: str, subject_id: str) -> None:
        if subject_type == "user":
            if not self._users_by_id.get(int(subject_id)) if subject_id.isdigit() else True:
                raise WorkspaceError(404, "PERMISSION_SUBJECT_NOT_FOUND", "授权主体不存在", {"subject_id": subject_id})
            return
        if subject_type == "team":
            self._find_team(subject_id)
            return
        if subject_type == "role":
            if ":" in subject_id:
                team_id, role = subject_id.split(":", 1)
                self._find_team(team_id)
                if role not in {"owner", "admin", "member", "guest"}:
                    raise WorkspaceError(422, "PERMISSION_ROLE_INVALID", "团队角色不存在", {"subject_id": subject_id})
                return
            if subject_id not in {"user", "owner", "admin", "member", "guest"}:
                raise WorkspaceError(422, "PERMISSION_ROLE_INVALID", "角色不存在", {"subject_id": subject_id})

    def _can_manage_permission_resource(self, resource_type: str, resource_id: str, actor: UserPublic) -> bool:
        try:
            self._ensure_can_manage_permission_resource(resource_type, resource_id, actor)
        except WorkspaceError:
            return False
        return True

    def _ensure_can_manage_permission_resource(self, resource_type: str, resource_id: str, actor: UserPublic) -> None:
        if resource_type == "folder":
            folder = self._find_folder(resource_id)
            if folder.scope == "team":
                self._require_team_manager(folder.team_id or "", actor)
            return
        if resource_type == "file":
            file_item = self._find_file(resource_id)
            folder = self._folders.get(file_item.folder_id)
            if folder and folder.scope == "team":
                self._require_team_manager(folder.team_id or "", actor)
            return
        if resource_type == "knowledge_base":
            knowledge_base = self._find_knowledge_base(resource_id, actor)
            self._ensure_can_manage_knowledge_base(knowledge_base, actor)
            return
        if resource_type == "workflow":
            self._find_workflow(resource_id)
            return
        if resource_type == "tool":
            if resource_id not in {tool.id for tool in self.list_tools()} and resource_id not in {tool.name for tool in self.list_tools()}:
                raise WorkspaceError(404, "TOOL_NOT_FOUND", "工具不存在", {"tool_id": resource_id})
            return
        raise WorkspaceError(422, "PERMISSION_RESOURCE_INVALID", "资源类型不支持", {"resource_type": resource_type})

    def _permission_subject_label(self, subject_type: str, subject_id: str) -> str:
        if subject_type == "user" and subject_id.isdigit():
            stored = self._users_by_id.get(int(subject_id))
            return stored.public.display_name if stored else subject_id
        if subject_type == "team":
            team = self._teams.get(subject_id)
            return team.name if team else subject_id
        if subject_type == "role":
            role = subject_id.split(":", 1)[-1]
            return {
                "owner": "所有者",
                "admin": "管理员",
                "member": "成员",
                "guest": "访客",
                "user": "普通用户",
            }.get(role, subject_id)
        return subject_id

    def _permission_resource_label(self, resource_type: str, resource_id: str) -> str:
        if resource_type == "folder":
            folder = self._folders.get(resource_id)
            return folder.name if folder else resource_id
        if resource_type == "file":
            for file_item in self._files:
                if file_item.id == resource_id:
                    return file_item.name
            return resource_id
        if resource_type == "knowledge_base":
            knowledge_base = self._knowledge_bases.get(resource_id)
            return knowledge_base.name if knowledge_base else resource_id
        if resource_type == "workflow":
            workflow = self._workflows.get(resource_id)
            return workflow.name if workflow else resource_id
        if resource_type == "tool":
            for tool in self.list_tools():
                if tool.id == resource_id or tool.name == resource_id:
                    return tool.name
        return resource_id

    def _permission_subjects(self, actor: UserPublic) -> set[tuple[str, str]]:
        subjects = {("user", str(actor.id))}
        subjects.update(("role", role) for role in actor.roles)
        for member in self._team_members.values():
            if member.user_id != actor.id or member.status != "active":
                continue
            subjects.add(("team", member.team_id))
            subjects.add(("role", member.role))
            subjects.add(("role", f"{member.team_id}:{member.role}"))
        return subjects

    def _permission_resource_chain(self, resource_type: str, resource_id: str) -> list[tuple[str, str, bool]]:
        if resource_type == "file":
            file_item = self._find_file(resource_id)
            chain = [("file", file_item.id, True)]
            folder = self._folders.get(file_item.folder_id)
            while folder:
                chain.append(("folder", folder.id, False))
                folder = self._folders.get(folder.parent_id) if folder.parent_id else None
            return chain
        if resource_type == "folder":
            folder = self._find_folder(resource_id)
            chain = [("folder", folder.id, True)]
            parent = self._folders.get(folder.parent_id) if folder.parent_id else None
            while parent:
                chain.append(("folder", parent.id, False))
                parent = self._folders.get(parent.parent_id) if parent.parent_id else None
            return chain
        return [(resource_type, resource_id, True)]

    def _permission_decision(self, actor: UserPublic, resource_type: str, resource_id: str, action: str) -> bool | None:
        subjects = self._permission_subjects(actor)
        resource_chain = self._permission_resource_chain(resource_type, resource_id)
        matched_effects: list[str] = []
        for rule in self._permission_rules.values():
            if (rule.subject_type, rule.subject_id) not in subjects:
                continue
            if not self._permission_action_matches(rule.action, action):
                continue
            for chain_type, chain_id, is_direct in resource_chain:
                if rule.resource_type != chain_type or rule.resource_id != chain_id:
                    continue
                if is_direct or rule.inherit:
                    matched_effects.append(rule.effect)
                    break

        if "deny" in matched_effects:
            return False
        if "allow" in matched_effects:
            return True
        return None

    def _permission_action_matches(self, rule_action: str, requested_action: str) -> bool:
        return rule_action == requested_action or rule_action == "manage"

    def _can_read_folder(self, folder: StoredFolder, actor: UserPublic) -> bool:
        decision = self._permission_decision(actor, "folder", folder.id, "read")
        if decision is not None:
            return decision
        if folder.scope == "personal":
            return True
        return self._team_membership(folder.team_id, actor) is not None

    def _ensure_can_write_folder(self, folder: StoredFolder, actor: UserPublic) -> None:
        decision = self._permission_decision(actor, "folder", folder.id, "write")
        if decision is True:
            return
        if decision is False:
            raise WorkspaceError(403, "FOLDER_WRITE_FORBIDDEN", "当前角色不能修改该文件夹", {"folder_id": folder.id})
        if folder.scope == "personal":
            return
        membership = self._team_membership(folder.team_id, actor)
        if not membership:
            raise WorkspaceError(403, "TEAM_ACCESS_DENIED", "没有访问该团队文件夹的权限", {"folder_id": folder.id})
        if membership.role == "guest":
            raise WorkspaceError(403, "FOLDER_WRITE_FORBIDDEN", "当前角色只能查看团队文件夹", {"folder_id": folder.id})

    def _can_read_file(self, file_item: FileItem, actor: UserPublic) -> bool:
        decision = self._permission_decision(actor, "file", file_item.id, "read")
        if decision is not None:
            return decision
        folder = self._folders.get(file_item.folder_id)
        if not folder:
            return file_item.permission_scope != "团队"
        return self._can_read_folder(folder, actor)

    def _ensure_can_read_file(self, file_item: FileItem, actor: UserPublic) -> None:
        if self._can_read_file(file_item, actor):
            return
        raise WorkspaceError(403, "FILE_READ_FORBIDDEN", "没有读取该文件的权限", {"file_id": file_item.id})

    def _ensure_can_write_file(self, file_item: FileItem, actor: UserPublic) -> None:
        decision = self._permission_decision(actor, "file", file_item.id, "write")
        if decision is True:
            return
        if decision is False:
            raise WorkspaceError(
                403,
                "FILE_WRITE_FORBIDDEN",
                "没有修改该文件的权限",
                {"file_id": file_item.id, "folder_id": file_item.folder_id},
            )
        folder = self._folders.get(file_item.folder_id)
        if not folder:
            if file_item.permission_scope == "团队":
                raise WorkspaceError(403, "FILE_WRITE_FORBIDDEN", "没有修改该文件的权限", {"file_id": file_item.id})
            return
        try:
            self._ensure_can_write_folder(folder, actor)
        except WorkspaceError as exc:
            if exc.status_code == 403:
                raise WorkspaceError(
                    403,
                    "FILE_WRITE_FORBIDDEN",
                    "没有修改该文件的权限",
                    {"file_id": file_item.id, "folder_id": file_item.folder_id},
                ) from exc
            raise

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

    def _seed_knowledge_bases(self) -> dict[str, StoredKnowledgeBase]:
        now = datetime.now(UTC)
        items = [
            StoredKnowledgeBase(
                id="kb-biology",
                name="生物学实验知识库",
                description="显微镜实验报告、观察记录和实验步骤",
                status="active",
                owner_id=None,
                created_at=now - timedelta(hours=3),
                updated_at=now - timedelta(hours=2),
            ),
            StoredKnowledgeBase(
                id="kb-course",
                name="软件工程课程知识库",
                description="需求文档、课程资料和团队协作记录",
                status="active",
                owner_id=None,
                created_at=now - timedelta(days=1),
                updated_at=now - timedelta(days=1),
            ),
        ]
        return {item.id: item for item in items}

    def _seed_knowledge_documents(self) -> dict[str, StoredKnowledgeDocument]:
        now = datetime.now(UTC)
        items = [
            StoredKnowledgeDocument(
                id="doc-microscope",
                kb_id="kb-biology",
                file_id="file-microscope",
                file_name="显微镜实验报告.pdf",
                index_status="indexed",
                chunks=[
                    StoredKnowledgeChunk(
                        id="chunk-micro-003",
                        content="显微镜实验包含取样、制片、低倍镜定位、高倍镜观察和结果记录。",
                        page_no=3,
                        paragraph_no=5,
                    )
                ],
                updated_at=now - timedelta(hours=2),
            ),
            StoredKnowledgeDocument(
                id="doc-requirements",
                kb_id="kb-course",
                file_id="file-requirements",
                file_name="需求规格说明书.md",
                index_status="indexed",
                chunks=[
                    StoredKnowledgeChunk(
                        id="chunk-requirements-001",
                        content="系统需要支持文件管理、知识库问答和团队协作。",
                        page_no=1,
                        paragraph_no=1,
                    )
                ],
                updated_at=now - timedelta(days=1),
            ),
        ]
        return {item.id: item for item in items}

    def _seed_workflows(self) -> dict[str, StoredWorkflow]:
        workflow = StoredWorkflow(
            id="new-file-auto-summary",
            name="新文件自动摘要",
            description="文件上传后自动解析、知识库问答并生成摘要。",
            trigger="file.uploaded",
            version="1.0.0",
            status="published",
            nodes=[
                WorkflowNodeDefinition(
                    id="parse",
                    name="内容提取",
                    type="tool",
                    tool_name="file_search",
                    parameters={"query": "{{ file.name }}"},
                ),
                WorkflowNodeDefinition(
                    id="qa",
                    name="知识问答",
                    type="tool",
                    tool_name="knowledge_qa",
                    parameters={"question": "总结文档关键内容"},
                ),
                WorkflowNodeDefinition(
                    id="summary",
                    name="摘要生成",
                    type="tool",
                    tool_name="report_generate",
                    parameters={"format": "markdown"},
                ),
            ],
            edges=[
                WorkflowEdgeDefinition(id="edge-parse-qa", source="parse", target="qa"),
                WorkflowEdgeDefinition(id="edge-qa-summary", source="qa", target="summary"),
            ],
            created_by=None,
            updated_at=datetime.now(UTC),
        )
        return {workflow.id: workflow}

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
