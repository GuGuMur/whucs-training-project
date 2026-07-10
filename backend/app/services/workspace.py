from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import faiss
import numpy as np
from fastapi import UploadFile

from app.services import embedding
from app.services.llm import generate_rag_answer, llm_available, _get_llm
from app.services.parser import ParseError, parse_document
from app.services.websocket_manager import ws_manager
from app.domain.schemas import (
    AgentStep,
    AgentTaskRequest,
    AgentTaskResponse,
    AuditLogEntry,
    Citation,
    DashboardSummary,
    FileAnnotationCreate,
    FileAnnotationItem,
    FileAnnotationReplyCreate,
    FileAnnotationReplyItem,
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
    MultipartChunkResponse,
    MultipartUploadInitRequest,
    MultipartUploadSession,
    NotificationItem,
    NotificationType,
    PermissionRuleCreate,
    PermissionRulePublic,
    QARequest,
    QAResponse,
    RecycleBinItem,
    ShareLinkCreateRequest,
    ShareLinkPublic,
    TeamCreate,
    TeamDetail,
    TeamInviteCreate,
    TeamInvitePublic,
    TeamMessageCreate,
    TeamMessageItem,
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
MAX_SHARE_LINK_TTL_SECONDS = 3600


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
class StoredTeamMessage:
    id: str
    team_id: str
    sender_id: int
    receiver_id: int | None
    content: str
    message_type: str
    created_at: datetime


@dataclass
class StoredNotification:
    id: str
    user_id: int
    type: NotificationType
    title: str
    content: str | None
    target_type: str | None
    target_id: str | None
    team_id: str | None
    is_read: bool
    created_at: datetime


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


@dataclass
class StoredMultipartUpload:
    id: str
    filename: str
    folder_id: str
    size: int
    sha256: str
    chunk_size: int
    total_chunks: int
    tags: list[str]
    created_by: int
    created_at: datetime
    expires_at: datetime
    chunks: dict[int, bytes] = field(default_factory=dict)
    status: str = "uploading"


@dataclass
class StoredShareLink:
    id: str
    file_id: str
    token: str
    password_hash: str | None
    expires_at: datetime
    download_limit: int | None
    download_count: int
    created_by: int
    created_at: datetime


@dataclass
class StoredFileAnnotation:
    id: str
    file_id: str
    author_id: int
    content: str
    position: dict[str, Any] | None
    parent_id: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class StoredDeletedFile:
    file: FileItem
    deleted_at: datetime
    deleted_by: str


class WorkspaceService:
    def __init__(self) -> None:
        self._secret = "dev-workspace-secret"
        self._users_by_id: dict[int, StoredUser] = {}
        self._users_by_username: dict[str, StoredUser] = {}
        self._users_by_email: dict[str, StoredUser] = {}
        self._next_user_id = 1
        self._folders: dict[str, StoredFolder] = {}
        self._file_contents: dict[str, bytes] = {}
        self._files: list[FileItem] = []
        self._file_versions: dict[str, list[StoredFileVersion]] = {}
        self._knowledge_bases: dict[str, StoredKnowledgeBase] = {}
        self._knowledge_documents: dict[str, StoredKnowledgeDocument] = {}
        self._kb_faiss_indexes: dict[str, tuple[faiss.Index, list[str]]] = {}  # kb_id -> (index, chunk_ids)
        self._conversations: dict[str, list[dict[str, str]]] = {}  # session_id -> [{role, content}, ...]
        for kb_id in self._knowledge_bases:
            self._rebuild_kb_faiss_index(kb_id)
        self._workflows: dict[str, StoredWorkflow] = {}
        self._teams: dict[str, StoredTeam] = {}
        self._team_members: dict[str, StoredTeamMember] = {}
        self._team_invites: dict[str, StoredTeamInvite] = {}
        self._team_messages: dict[str, StoredTeamMessage] = {}
        self._permission_rules: dict[str, StoredPermissionRule] = {}
        self._multipart_uploads: dict[str, StoredMultipartUpload] = {}
        self._share_links: dict[str, StoredShareLink] = {}
        self._file_annotations: dict[str, StoredFileAnnotation] = {}
        self._notifications: dict[str, StoredNotification] = {}
        self._deleted_files: dict[str, StoredDeletedFile] = {}
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
        # Create personal root folder lazily on first registration
        if "personal-root" not in self._folders:
            self._folders["personal-root"] = StoredFolder(
                id="personal-root",
                name="个人空间",
                parent_id=None,
                scope="personal",
                permission="管理",
                team_id=None,
            )
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
        updated_from: datetime | None = None,
        updated_to: datetime | None = None,
    ) -> list[FileItem]:
        files = [file for file in self._files if self._can_read_file(file, actor)]
        if query:
            files = [file for file in files if query.lower() in file.name.lower()]
        if tag:
            files = [file for file in files if tag in file.tags]
        if file_type:
            files = [file for file in files if file.type == file_type]
        if updated_from:
            files = [file for file in files if file.updated_at >= updated_from]
        if updated_to:
            files = [file for file in files if file.updated_at <= updated_to]
        return files

    async def upload_file(self, upload: UploadFile, folder_id: str, tags: str | None, actor: UserPublic) -> FileItem:
        folder = self._find_folder(folder_id)
        self._ensure_can_write_folder(folder, actor)
        content = await upload.read()
        clean_tags = self._normalize_tags((tags or "").split(","))
        filename = self._clean_file_name(upload.filename or "未命名文件")
        return self._save_file_content(filename, folder, content, clean_tags, actor, "file.upload")

    def init_multipart_upload(self, payload: MultipartUploadInitRequest, actor: UserPublic) -> MultipartUploadSession:
        folder = self._find_folder(payload.folder_id)
        self._ensure_can_write_folder(folder, actor)
        filename = self._clean_file_name(payload.filename)
        tags = self._normalize_tags(payload.tags)
        total_chunks = (payload.size + payload.chunk_size - 1) // payload.chunk_size
        now = datetime.now(UTC)
        session = StoredMultipartUpload(
            id=f"upload-{secrets.token_hex(8)}",
            filename=filename,
            folder_id=folder.id,
            size=payload.size,
            sha256=payload.sha256,
            chunk_size=payload.chunk_size,
            total_chunks=total_chunks,
            tags=tags,
            created_by=actor.id,
            created_at=now,
            expires_at=now + timedelta(hours=1),
        )
        self._multipart_uploads[session.id] = session
        self._record_audit(actor.username, "file.multipart_init", "file", filename)
        return self._multipart_upload_session(session)

    async def upload_multipart_chunk(
        self,
        session_id: str,
        chunk_index: int,
        upload: UploadFile,
        chunk_sha256: str,
        actor: UserPublic,
    ) -> MultipartChunkResponse:
        session = self._find_multipart_upload(session_id, actor)
        self._ensure_multipart_uploading(session)
        if chunk_index < 0 or chunk_index >= session.total_chunks:
            raise WorkspaceError(
                422,
                "CHUNK_INDEX_INVALID",
                "分片序号超出上传会话范围",
                {"chunk_index": chunk_index, "total_chunks": session.total_chunks},
            )
        content = await upload.read()
        digest = hashlib.sha256(content).hexdigest()
        if digest != chunk_sha256:
            raise WorkspaceError(
                409,
                "CHUNK_HASH_MISMATCH",
                "分片 SHA256 校验失败",
                {"chunk_index": chunk_index, "expected": chunk_sha256, "actual": digest},
            )
        if chunk_index < session.total_chunks - 1 and len(content) != session.chunk_size:
            raise WorkspaceError(
                409,
                "CHUNK_SIZE_MISMATCH",
                "非末尾分片大小必须等于会话 chunk_size",
                {"chunk_index": chunk_index, "expected_size": session.chunk_size, "actual_size": len(content)},
            )
        session.chunks[chunk_index] = content
        return MultipartChunkResponse(
            session_id=session.id,
            chunk_index=chunk_index,
            received_chunks=sorted(session.chunks),
            total_chunks=session.total_chunks,
            status=session.status,  # type: ignore[arg-type]
        )

    def get_multipart_upload(self, session_id: str, actor: UserPublic) -> MultipartUploadSession:
        return self._multipart_upload_session(self._find_multipart_upload(session_id, actor))

    def complete_multipart_upload(self, session_id: str, actor: UserPublic) -> FileItem:
        session = self._find_multipart_upload(session_id, actor)
        self._ensure_multipart_uploading(session)
        missing_chunks = [index for index in range(session.total_chunks) if index not in session.chunks]
        if missing_chunks:
            raise WorkspaceError(
                409,
                "MULTIPART_UPLOAD_INCOMPLETE",
                "仍有分片未上传，不能完成合并",
                {"missing_chunks": missing_chunks},
            )
        folder = self._find_folder(session.folder_id)
        self._ensure_can_write_folder(folder, actor)
        content = b"".join(session.chunks[index] for index in range(session.total_chunks))
        digest = hashlib.sha256(content).hexdigest()
        if len(content) != session.size or digest != session.sha256:
            raise WorkspaceError(
                409,
                "MULTIPART_HASH_MISMATCH",
                "合并后的文件大小或 SHA256 与初始化信息不一致",
                {
                    "expected_size": session.size,
                    "actual_size": len(content),
                    "expected_sha256": session.sha256,
                    "actual_sha256": digest,
                },
            )
        session.status = "completed"
        item = self._save_file_content(
            session.filename,
            folder,
            content,
            session.tags,
            actor,
            "file.multipart_complete",
        )
        self._multipart_uploads.pop(session.id, None)
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

    def create_share_link(self, file_id: str, payload: ShareLinkCreateRequest, actor: UserPublic) -> ShareLinkPublic:
        if payload.expires_in_seconds > MAX_SHARE_LINK_TTL_SECONDS:
            raise WorkspaceError(
                422,
                "SHARE_LINK_EXPIRY_TOO_LONG",
                "分享链接有效期不能超过 1 小时",
                {"max_expires_in_seconds": MAX_SHARE_LINK_TTL_SECONDS},
            )
        file_item = self._find_file(file_id)
        self._ensure_can_read_file(file_item, actor)
        now = datetime.now(UTC)
        token = self._create_share_token(file_id, actor.id)
        share_link = StoredShareLink(
            id=f"share-{secrets.token_hex(8)}",
            file_id=file_id,
            token=token,
            password_hash=self._hash_password(payload.password) if payload.password else None,
            expires_at=now + timedelta(seconds=payload.expires_in_seconds),
            download_limit=payload.download_limit,
            download_count=0,
            created_by=actor.id,
            created_at=now,
        )
        self._share_links[token] = share_link
        self._record_audit(actor.username, "file.share_create", "file", file_item.name)
        return self._share_link_public(share_link)

    def list_file_annotations(self, file_id: str, actor: UserPublic) -> list[FileAnnotationItem]:
        file_item = self._find_file(file_id)
        self._ensure_can_read_file(file_item, actor)
        annotations = [
            annotation
            for annotation in self._file_annotations.values()
            if annotation.file_id == file_id and annotation.parent_id is None
        ]
        return [self._file_annotation_item(annotation) for annotation in sorted(annotations, key=lambda item: item.created_at)]

    def create_file_annotation(
        self,
        file_id: str,
        payload: FileAnnotationCreate,
        actor: UserPublic,
    ) -> FileAnnotationItem:
        file_item = self._find_file(file_id)
        self._ensure_can_read_file(file_item, actor)
        now = datetime.now(UTC)
        annotation = StoredFileAnnotation(
            id=f"anno-{secrets.token_hex(8)}",
            file_id=file_id,
            author_id=actor.id,
            content=payload.content.strip(),
            position=payload.position,
            parent_id=None,
            created_at=now,
            updated_at=now,
        )
        if not annotation.content:
            raise WorkspaceError(422, "ANNOTATION_CONTENT_REQUIRED", "批注内容不能为空", {"file_id": file_id})
        self._file_annotations[annotation.id] = annotation
        if "@" in annotation.content:
            self._notify_team_members_for_file(
                file_item,
                exclude_user_id=actor.id,
                notification_type="mention",
                title="文件批注提到了你",
                content=f"{actor.display_name} 在 {file_item.name} 的批注中提到了你",
                target_type="file",
                target_id=file_item.id,
            )
        self._record_audit(actor.username, "file.annotation_create", "file", file_item.name)
        return self._file_annotation_item(annotation)

    def reply_file_annotation(
        self,
        annotation_id: str,
        payload: FileAnnotationReplyCreate,
        actor: UserPublic,
    ) -> FileAnnotationReplyItem:
        parent = self._find_root_annotation(annotation_id)
        file_item = self._find_file(parent.file_id)
        self._ensure_can_read_file(file_item, actor)
        content = payload.content.strip()
        if not content:
            raise WorkspaceError(422, "ANNOTATION_CONTENT_REQUIRED", "回复内容不能为空", {"annotation_id": annotation_id})
        now = datetime.now(UTC)
        reply = StoredFileAnnotation(
            id=f"anno-{secrets.token_hex(8)}",
            file_id=parent.file_id,
            author_id=actor.id,
            content=content,
            position=None,
            parent_id=parent.id,
            created_at=now,
            updated_at=now,
        )
        self._file_annotations[reply.id] = reply
        if parent.author_id != actor.id:
            self._create_notification(
                user_id=parent.author_id,
                notification_type="annotation",
                title="批注收到回复",
                content=f"{actor.display_name} 回复了 {file_item.name} 的批注",
                target_type="file",
                target_id=file_item.id,
                team_id=self._team_id_for_file(file_item),
            )
        self._record_audit(actor.username, "file.annotation_reply", "file", file_item.name)
        return self._file_annotation_reply_item(reply)

    def delete_file_annotation(self, file_id: str, annotation_id: str, actor: UserPublic) -> None:
        file_item = self._find_file(file_id)
        self._ensure_can_read_file(file_item, actor)
        annotation = self._file_annotations.get(annotation_id)
        if not annotation or annotation.file_id != file_id:
            raise WorkspaceError(404, "ANNOTATION_NOT_FOUND", "批注不存在或无权访问", {"annotation_id": annotation_id})
        if not self._can_delete_annotation(file_item, annotation, actor):
            raise WorkspaceError(
                403,
                "ANNOTATION_DELETE_FORBIDDEN",
                "只能删除自己的批注，团队管理员可删除团队文件批注",
                {"annotation_id": annotation_id},
            )
        if annotation.parent_id is None:
            reply_ids = [
                reply.id
                for reply in self._file_annotations.values()
                if reply.parent_id == annotation.id
            ]
            for reply_id in reply_ids:
                self._file_annotations.pop(reply_id, None)
        self._file_annotations.pop(annotation.id, None)
        self._record_audit(actor.username, "file.annotation_delete", "file", file_item.name)

    def download_shared_file(self, token: str, password: str | None) -> tuple[FileItem, bytes]:
        share_link = self._find_share_link(token)
        now = datetime.now(UTC)
        if now >= share_link.expires_at:
            raise WorkspaceError(410, "SHARE_LINK_EXPIRED", "分享链接已过期", {"token": token})
        if share_link.download_limit is not None and share_link.download_count >= share_link.download_limit:
            raise WorkspaceError(410, "SHARE_LINK_LIMIT_REACHED", "分享链接下载次数已用尽", {"token": token})
        if share_link.password_hash and self._hash_password(password or "") != share_link.password_hash:
            raise WorkspaceError(403, "SHARE_LINK_PASSWORD_INVALID", "分享密码不正确", {"token": token})

        file_item = self._find_file(share_link.file_id)
        content = self._read_file_content(file_item.id)
        share_link.download_count += 1
        self._record_audit("public-share", "file.share_download", "file", file_item.name)
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

    def list_deleted_files(self, actor: UserPublic) -> list[RecycleBinItem]:
        return [
            RecycleBinItem(
                file=deleted.file,
                deleted_at=deleted.deleted_at,
                deleted_by=deleted.deleted_by,
            )
            for deleted in sorted(self._deleted_files.values(), key=lambda item: item.deleted_at, reverse=True)
            if self._can_read_file(deleted.file, actor)
        ]

    def delete_file(self, file_id: str, actor: UserPublic) -> None:
        file_item = self._find_file(file_id)
        self._ensure_can_write_file(file_item, actor)
        self._files = [candidate for candidate in self._files if candidate.id != file_id]
        self._deleted_files[file_id] = StoredDeletedFile(
            file=file_item,
            deleted_at=datetime.now(UTC),
            deleted_by=actor.username,
        )
        self._record_audit(actor.username, "file.delete", "file", file_item.name)

    def restore_deleted_file(self, file_id: str, actor: UserPublic) -> FileItem:
        deleted = self._deleted_files.get(file_id)
        if not deleted:
            raise WorkspaceError(404, "FILE_NOT_FOUND", "文件不存在或无权访问", {"file_id": file_id})
        self._ensure_can_write_file(deleted.file, actor)
        if any(file_item.id == file_id for file_item in self._files):
            raise WorkspaceError(409, "FILE_RESTORE_CONFLICT", "同名文件已恢复或存在冲突", {"file_id": file_id})
        self._files.insert(0, deleted.file)
        self._deleted_files.pop(file_id, None)
        self._record_audit(actor.username, "file.restore", "file", deleted.file.name)
        return deleted.file

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
        # Mark the file as parsing, run the real extractor, then settle on
        # indexed or failed so the workbench can show the true lifecycle.
        self._replace_file(file_item.model_copy(update={"parse_status": "parsing", "updated_at": now}))
        try:
            parsed = parse_document(file_item.name, content, file_item.type)
        except ParseError as exc:
            self._replace_file(
                file_item.model_copy(update={"parse_status": "failed", "updated_at": datetime.now(UTC)})
            )
            self._record_audit(actor.username, "knowledge_base.parse_failed", "file", file_item.name)
            raise WorkspaceError(
                422,
                "FILE_PARSE_FAILED",
                f"文件解析失败：{exc}",
                {"file_id": file_item.id, "file_name": file_item.name},
            ) from exc
        document = StoredKnowledgeDocument(
            id=document_id,
            kb_id=kb_id,
            file_id=file_item.id,
            file_name=file_item.name,
            index_status="indexed",
            chunks=[
                StoredKnowledgeChunk(
                    id=f"{document_id}-chunk-{index}",
                    content=segment.content,
                    page_no=segment.page_no,
                    paragraph_no=segment.paragraph_no,
                )
                for index, segment in enumerate(parsed.segments, start=1)
            ],
            updated_at=now,
        )
        self._knowledge_documents[document.id] = document
        # Build/update FAISS index for this knowledge base
        self._rebuild_kb_faiss_index(kb_id)
        knowledge_base.updated_at = now
        self._mark_file_indexed_in_knowledge_base(file_item, kb_id, now)
        self._record_audit(actor.username, "knowledge_base.add_document", "knowledge_base", knowledge_base.name)
        return self._knowledge_document_public(document)

    def answer_question(self, payload: QARequest, actor: UserPublic) -> QAResponse:
        knowledge_base = self._find_knowledge_base(payload.kb_id, actor)
        citations = self._retrieve_knowledge_citations(knowledge_base.id, payload.question, payload.top_k, actor)
        conv_id = payload.conversation_id or f"conv-{secrets.token_hex(4)}"
        # Store conversation history for multi-turn (FR-K10)
        history = self._conversations.setdefault(conv_id, [])
        history.append({"role": "user", "content": payload.question})
        answer = self._compose_rag_answer(knowledge_base, payload.question, citations)
        history.append({"role": "assistant", "content": answer})
        self._record_audit(actor.username, "qa.query", "knowledge_base", payload.kb_id)
        return QAResponse(
            conversation_id=conv_id,
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
            ToolDefinition(
                id="tool-file-compare",
                name="file_compare",
                version="1.0.0",
                category="文件操作",
                description="比对两个文件的内容差异并生成对比报告。",
                input_schema={"type": "object", "required": ["file_a", "file_b"], "properties": {"file_a": {"type": "string"}, "file_b": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"diff": {"type": "string"}}},
            ),
            ToolDefinition(
                id="tool-team-activity",
                name="team_activity",
                version="1.0.0",
                category="团队协作",
                description="获取团队近期活动动态，包括文件变更、成员操作和流程执行记录。",
                input_schema={"type": "object", "properties": {"team_id": {"type": "string"}, "limit": {"type": "integer"}}},
                output_schema={"type": "object", "properties": {"activities": {"type": "array"}}},
            ),
        ]

    def create_agent_task(self, payload: AgentTaskRequest, actor: UserPublic) -> AgentTaskResponse:
        if payload.kb_id:
            self._find_knowledge_base(payload.kb_id, actor)
        for file_id in payload.context_file_ids:
            self._ensure_can_read_file(self._find_file(file_id), actor)

        llm = _get_llm()
        if llm is None:
            raise WorkspaceError(503, "LLM_UNAVAILABLE", "LLM 服务暂不可用，请稍后重试")

        tools_desc = self._agent_tools_description()
        plan_prompt = (
            "你是一个智能任务规划助手。根据用户的任务描述和可用工具，生成一个分步执行计划。\n\n"
            f"【可用工具】\n{tools_desc}\n\n"
            f"【用户任务】{payload.task}\n\n"
            "请用 JSON 格式返回执行计划，格式如下：\n"
            '{"steps": [{"type": "thought|action|observation|answer", "title": "...", "content": "...", "tool_name": "..."}]}\n'
            "tool_name 仅在 type=action 时需要填写。最多 5 个步骤。只返回 JSON，不要其它内容。"
        )
        try:
            plan_response = llm.invoke(plan_prompt)
            plan_text = plan_response.content.strip() if hasattr(plan_response, "content") else str(plan_response).strip()
            if plan_text.startswith("```"):
                plan_text = plan_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            plan = json.loads(plan_text)
        except Exception:
            raise WorkspaceError(500, "AGENT_TASK_FAILED", "任务规划失败，请稍后重试")

        raw_steps: list[dict[str, Any]] = plan.get("steps", [])
        steps: list[AgentStep] = []
        final_answer = ""
        for raw in raw_steps:
            step_type = raw.get("type", "observation")
            step = AgentStep(
                type=step_type if step_type in ("thought", "action", "observation", "answer") else "observation",
                title=raw.get("title", ""),
                content=raw.get("content", ""),
                tool_name=raw.get("tool_name"),
            )
            if step.type == "action" and step.tool_name:
                step.content = self._execute_agent_tool(step.tool_name, payload, actor, step.content)
            if step.type == "answer":
                final_answer = step.content
            steps.append(step)

        if not final_answer and steps:
            final_answer = steps[-1].content
        self._record_audit(actor.username, "agent.create_task", "agent_task", payload.task)
        return AgentTaskResponse(
            id=f"agent-{secrets.token_hex(4)}",
            task=payload.task,
            status="completed",
            steps=steps,
            final_answer=final_answer,
        )

    def _agent_tools_description(self) -> str:
        tools = self.list_tools()
        lines: list[str] = []
        for tool in tools:
            lines.append(f"- {tool.name}: {tool.description}")
        return "\n".join(lines)

    def _execute_agent_tool(self, tool_name: str, payload: AgentTaskRequest, actor: UserPublic, context: str) -> str:
        import asyncio

        try:
            return self._run_agent_tool(tool_name, payload, actor, context)
        except TimeoutError:
            return f"工具 {tool_name} 执行超时，请重试。"
        except Exception as exc:
            return f"工具 {tool_name} 执行失败：{exc}"

    def _run_agent_tool(self, tool_name: str, payload: AgentTaskRequest, actor: UserPublic, context: str) -> str:
        if tool_name == "file_search":
            files = [f for f in self._files if self._can_read_file(f, actor)]
            if payload.context_file_ids:
                files = [f for f in files if f.id in payload.context_file_ids]
            if not files:
                return "未找到匹配的文件。"
            file_list = "\n".join(f"- {f.name} ({f.type}, {f.parse_status})" for f in files[:5])
            return f"找到 {len(files)} 个文件：\n{file_list}"
        elif tool_name == "knowledge_qa":
            kb_id = payload.kb_id or next(iter(self._knowledge_bases.keys()), "")
            if not kb_id:
                return "没有可用的知识库。"
            citations = self._retrieve_knowledge_citations(kb_id, payload.task, 3, actor)
            if not citations:
                return "知识库未检索到相关内容。"
            return "\n".join(f"[{c.title}] {c.snippet}" for c in citations)
        elif tool_name == "report_generate":
            llm = _get_llm()
            if llm is None:
                return "LLM 不可用，无法生成报告。"
            report_prompt = f"请根据以下上下文生成一份简短的 Markdown 报告：\n{context}"
            resp = llm.invoke(report_prompt)
            return resp.content.strip() if hasattr(resp, "content") else str(resp).strip()
        elif tool_name == "file_compare":
            return self._compare_files(payload, actor)
        elif tool_name == "team_activity":
            audit_logs = self._audit_logs[-20:] if self._audit_logs else []
            if not audit_logs:
                return "暂无团队活动记录。"
            return "\n".join(f"- {log.action}: {log.resource_name} ({log.actor})" for log in reversed(audit_logs[-10:]))
        elif tool_name == "image_ocr":
            return "OCR 服务暂不可用，请稍后重试。"
        return f"工具 {tool_name} 执行完成。"


    def _compare_files(self, payload: AgentTaskRequest, actor: UserPublic) -> str:
        """Simple file comparison by reading content and diffing."""
        files = [f for f in self._files if f.id in payload.context_file_ids and self._can_read_file(f, actor)]
        if len(files) < 2:
            return "需要至少两个文件进行比对。"
        content_a = self._read_file_content(files[0].id).decode("utf-8", errors="replace")
        content_b = self._read_file_content(files[1].id).decode("utf-8", errors="replace")
        lines_a = set(content_a.splitlines())
        lines_b = set(content_b.splitlines())
        only_a = lines_a - lines_b
        only_b = lines_b - lines_a
        common = lines_a & lines_b
        return f"比对 {files[0].name} vs {files[1].name}：共同行 {len(common)}，仅A {len(only_a)}，仅B {len(only_b)}。\n仅A示例：{next(iter(only_a), '无')[:80]}\n仅B示例：{next(iter(only_b), '无')[:80]}"

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
            summary = f"流程 {workflow.name} 执行完成，处理文件：{file_item.name}"
        else:
            summary = f"流程 {workflow.name} 执行完成，处理文件：{file_item.name}"
        self._broadcast_ws("workflow", "execution_completed", {"workflow_id": workflow_id, "workflow_name": workflow.name, "summary": summary})
        self._notify_team_members_for_file(
            file_item,
            exclude_user_id=actor.id,
            notification_type="workflow",
            title="流程执行完成",
            content=f"{workflow.name} 已基于 {file_item.name} 执行完成",
            target_type="workflow",
            target_id=workflow_id,
        )
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
        return [self._team_summary(self._find_team(member.team_id), member.role, actor.id) for member in memberships]

    def get_team_detail(self, team_id: str, actor: UserPublic) -> TeamDetail:
        team = self._find_team(team_id)
        membership = self._require_team_member(team_id, actor)
        return TeamDetail(
            id=team.id,
            name=team.name,
            description=team.description,
            role=membership.role,  # type: ignore[arg-type]
            member_count=self._active_team_member_count(team.id),
            unread_count=self._notification_unread_count(actor.id, team.id),
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
        invited_user = self._users_by_email.get(invite.email)
        if invited_user:
            self._create_notification(
                user_id=invited_user.public.id,
                notification_type="invite",
                title="团队邀请",
                content=f"{actor.display_name} 邀请你加入团队 {team.name}",
                target_type="team",
                target_id=team.id,
                team_id=team.id,
            )
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

    def list_team_messages(self, team_id: str, actor: UserPublic) -> list[TeamMessageItem]:
        self._find_team(team_id)
        self._require_team_member(team_id, actor)
        messages = [
            message
            for message in self._team_messages.values()
            if message.team_id == team_id
            and (message.receiver_id is None or message.sender_id == actor.id or message.receiver_id == actor.id)
        ]
        return [self._team_message_item(message) for message in sorted(messages, key=lambda item: item.created_at)]

    def create_team_message(self, team_id: str, payload: TeamMessageCreate, actor: UserPublic) -> TeamMessageItem:
        team = self._find_team(team_id)
        membership = self._require_team_member(team_id, actor)
        content = payload.content.strip()
        if not content:
            raise WorkspaceError(422, "TEAM_MESSAGE_EMPTY", "消息内容不能为空", {"team_id": team_id})
        if payload.receiver_id is not None:
            receiver_member = self._team_membership(team_id, self._require_user_by_id(payload.receiver_id))
            if not receiver_member:
                raise WorkspaceError(404, "TEAM_MESSAGE_RECEIVER_NOT_FOUND", "私聊接收者不是团队成员", {"team_id": team_id})

        message = StoredTeamMessage(
            id=f"msg-{secrets.token_hex(8)}",
            team_id=team.id,
            sender_id=actor.id,
            receiver_id=payload.receiver_id,
            content=content,
            message_type=payload.message_type,
            created_at=datetime.now(UTC),
        )
        self._team_messages[message.id] = message
        for mentioned_member in self._mentioned_team_members(team.id, content, actor.id, membership.role):
            self._create_notification(
                user_id=mentioned_member.user_id,
                notification_type="mention",
                title="团队聊天提到了你",
                content=f"{actor.display_name} 在 {team.name} 中提到了你：{content}",
                target_type="team_message",
                target_id=message.id,
                team_id=team.id,
            )
        self._record_audit(actor.username, "team.message_create", "team_message", team.name)
        self._broadcast_ws("chat", "new_message", {"team_id": team_id, "message": self._team_message_item(message).model_dump()})
        return self._team_message_item(message)

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

    def list_notifications(self, actor: UserPublic) -> list[NotificationItem]:
        notifications = [
            notification
            for notification in self._notifications.values()
            if notification.user_id == actor.id
        ]
        return [
            self._notification_item(notification)
            for notification in sorted(notifications, key=lambda item: item.created_at, reverse=True)
        ]

    def mark_notification_read(self, notification_id: str, actor: UserPublic) -> NotificationItem:
        notification = self._notifications.get(notification_id)
        if not notification or notification.user_id != actor.id:
            raise WorkspaceError(
                404,
                "NOTIFICATION_NOT_FOUND",
                "通知不存在或无权访问",
                {"notification_id": notification_id},
            )
        notification.is_read = True
        self._record_audit(actor.username, "notification.read", "notification", notification.title)
        return self._notification_item(notification)

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
                unread_notifications=self._notification_unread_count(actor.id),
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
        index_entry = self._kb_faiss_indexes.get(kb_id)
        if index_entry is None:
            return []
        faiss_index, chunk_ids = index_entry
        if faiss_index.ntotal == 0:
            return []

        # Retrieve top-3k candidates from FAISS, then rerank with BM25 (FR-K07)
        candidate_k = min(top_k * 3, faiss_index.ntotal)
        query_vec = embedding.embed_query(question).reshape(1, -1)
        distances, indices = faiss_index.search(query_vec.astype(np.float32), candidate_k)

        candidates: list[tuple[StoredKnowledgeDocument, StoredKnowledgeChunk, float]] = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx < 0 or idx >= len(chunk_ids):
                continue
            chunk_id = chunk_ids[idx]
            document, chunk = self._find_document_and_chunk(kb_id, chunk_id)
            if document is None:
                continue
            candidates.append((document, chunk, float(dist)))

        # BM25 reranking
        if len(candidates) > top_k:
            try:
                from rank_bm25 import BM25Okapi

                tokenized_question = question.split()
                tokenized_candidates = [c.content.split() for _, c, _ in candidates]
                bm25 = BM25Okapi(tokenized_candidates)
                bm25_scores = bm25.get_scores(tokenized_question)
                for i, score in enumerate(bm25_scores):
                    _, _, faiss_score = candidates[i]
                    candidates[i] = (candidates[i][0], candidates[i][1], faiss_score * 0.7 + float(score) * 0.01)
                candidates.sort(key=lambda x: x[2], reverse=True)
            except ImportError:
                pass

        citations: list[Citation] = []
        for document, chunk, _ in candidates[:top_k]:
            file_item = self._find_file(document.file_id)
            if not self._can_read_file(file_item, actor):
                continue
            citations.append(
                Citation(
                    file_id=document.file_id,
                    document_id=document.id,
                    chunk_id=chunk.id,
                    title=document.file_name,
                    page_no=chunk.page_no,
                    paragraph_no=chunk.paragraph_no,
                    snippet=chunk.content,
                )
            )
        return citations

    def _rebuild_kb_faiss_index(self, kb_id: str) -> None:
        chunks: list[StoredKnowledgeChunk] = []
        chunk_ids: list[str] = []
        for doc in self._knowledge_documents.values():
            if doc.kb_id != kb_id or doc.index_status != "indexed":
                continue
            for chunk in doc.chunks:
                chunk_ids.append(chunk.id)
                chunks.append(chunk)

        if not chunks:
            self._kb_faiss_indexes.pop(kb_id, None)
            return

        texts = [c.content for c in chunks]
        vecs = embedding.embed_documents(texts)
        dim = vecs.shape[1]
        faiss_index = faiss.IndexFlatIP(dim)
        faiss_index.add(vecs.astype(np.float32))
        self._kb_faiss_indexes[kb_id] = (faiss_index, chunk_ids)

    def _find_document_and_chunk(
        self, kb_id: str, chunk_id: str,
    ) -> tuple[StoredKnowledgeDocument | None, StoredKnowledgeChunk | None]:
        for doc in self._knowledge_documents.values():
            if doc.kb_id != kb_id:
                continue
            for chunk in doc.chunks:
                if chunk.id == chunk_id:
                    return doc, chunk
        return None, None

    def _compose_rag_answer(
        self,
        knowledge_base: StoredKnowledgeBase,
        question: str,
        citations: list[Citation],
    ) -> str:
        snippets = [c.snippet for c in citations[:5]]
        return generate_rag_answer(question, snippets, knowledge_base.name)


    def _team_summary(self, team: StoredTeam, role: str, actor_id: int | None = None) -> TeamSummary:
        return TeamSummary(
            id=team.id,
            name=team.name,
            description=team.description,
            role=role,
            member_count=self._active_team_member_count(team.id),
            unread_count=self._notification_unread_count(actor_id, team.id) if actor_id is not None else team.unread_count,
            root_folder_id=team.root_folder_id,
        )

    def _create_notification(
        self,
        *,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        content: str | None,
        target_type: str | None,
        target_id: str | None,
        team_id: str | None,
    ) -> StoredNotification:
        notification = StoredNotification(
            id=f"noti-{secrets.token_hex(8)}",
            user_id=user_id,
            type=notification_type,
            title=title,
            content=content,
            target_type=target_type,
            target_id=target_id,
            team_id=team_id,
            is_read=False,
            created_at=datetime.now(UTC),
        )
        self._notifications[notification.id] = notification
        self._broadcast_ws("activity", "notification", {"user_id": user_id, "type": notification_type, "title": title})
        return notification

    def _notification_item(self, notification: StoredNotification) -> NotificationItem:
        return NotificationItem(
            id=notification.id,
            user_id=notification.user_id,
            type=notification.type,
            title=notification.title,
            content=notification.content,
            target_type=notification.target_type,
            target_id=notification.target_id,
            is_read=notification.is_read,
            created_at=notification.created_at,
        )

    def _notification_unread_count(self, user_id: int | None, team_id: str | None = None) -> int:
        if user_id is None:
            return 0
        return sum(
            1
            for notification in self._notifications.values()
            if notification.user_id == user_id
            and not notification.is_read
            and (team_id is None or notification.team_id == team_id)
        )

    def _team_message_item(self, message: StoredTeamMessage) -> TeamMessageItem:
        sender = self._users_by_id.get(message.sender_id)
        return TeamMessageItem(
            id=message.id,
            team_id=message.team_id,
            sender_id=message.sender_id,
            sender_name=sender.public.username if sender else "unknown",
            receiver_id=message.receiver_id,
            content=message.content,
            message_type=message.message_type,  # type: ignore[arg-type]
            created_at=message.created_at,
        )

    def _file_annotation_item(self, annotation: StoredFileAnnotation) -> FileAnnotationItem:
        return FileAnnotationItem(
            id=annotation.id,
            file_id=annotation.file_id,
            author_id=annotation.author_id,
            author_name=self._annotation_author_name(annotation.author_id),
            content=annotation.content,
            position=annotation.position,
            created_at=annotation.created_at,
            updated_at=annotation.updated_at,
            replies=[
                self._file_annotation_reply_item(reply)
                for reply in sorted(
                    (
                        candidate
                        for candidate in self._file_annotations.values()
                        if candidate.parent_id == annotation.id
                    ),
                    key=lambda item: item.created_at,
                )
            ],
        )

    def _file_annotation_reply_item(self, annotation: StoredFileAnnotation) -> FileAnnotationReplyItem:
        if annotation.parent_id is None:
            raise WorkspaceError(500, "ANNOTATION_REPLY_INVALID", "批注回复结构异常", {"annotation_id": annotation.id})
        return FileAnnotationReplyItem(
            id=annotation.id,
            annotation_id=annotation.parent_id,
            file_id=annotation.file_id,
            author_id=annotation.author_id,
            author_name=self._annotation_author_name(annotation.author_id),
            content=annotation.content,
            created_at=annotation.created_at,
            updated_at=annotation.updated_at,
        )

    def _annotation_author_name(self, user_id: int) -> str:
        stored = self._users_by_id.get(user_id)
        if not stored:
            return "unknown"
        return stored.public.username

    def _require_user_by_id(self, user_id: int) -> UserPublic:
        stored = self._users_by_id.get(user_id)
        if not stored:
            raise WorkspaceError(404, "USER_NOT_FOUND", "用户不存在", {"user_id": user_id})
        return stored.public

    def _find_root_annotation(self, annotation_id: str) -> StoredFileAnnotation:
        annotation = self._file_annotations.get(annotation_id)
        if not annotation or annotation.parent_id is not None:
            raise WorkspaceError(404, "ANNOTATION_NOT_FOUND", "批注不存在或无权访问", {"annotation_id": annotation_id})
        return annotation

    def _can_delete_annotation(
        self,
        file_item: FileItem,
        annotation: StoredFileAnnotation,
        actor: UserPublic,
    ) -> bool:
        if annotation.author_id == actor.id:
            return True
        folder = self._folders.get(file_item.folder_id)
        if not folder or folder.scope != "team" or not folder.team_id:
            return False
        membership = self._team_membership(folder.team_id, actor)
        return bool(membership and membership.role in {"owner", "admin"})

    def _team_id_for_file(self, file_item: FileItem) -> str | None:
        folder = self._folders.get(file_item.folder_id)
        if not folder:
            return None
        return folder.team_id

    def _notify_team_members_for_file(
        self,
        file_item: FileItem,
        *,
        exclude_user_id: int,
        notification_type: NotificationType,
        title: str,
        content: str,
        target_type: str,
        target_id: str,
    ) -> None:
        team_id = self._team_id_for_file(file_item)
        if not team_id:
            return
        for member in self._team_members.values():
            if member.team_id != team_id or member.status != "active" or member.user_id == exclude_user_id:
                continue
            self._create_notification(
                user_id=member.user_id,
                notification_type=notification_type,
                title=title,
                content=content,
                target_type=target_type,
                target_id=target_id,
                team_id=team_id,
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

    def _mentioned_team_members(
        self,
        team_id: str,
        content: str,
        actor_id: int,
        actor_role: str,
    ) -> list[StoredTeamMember]:
        mention_all = "@all" in content and actor_role in {"owner", "admin"}
        mentioned: list[StoredTeamMember] = []
        seen_user_ids: set[int] = set()
        for member in self._team_members.values():
            if member.team_id != team_id or member.status != "active" or member.user_id == actor_id:
                continue
            user = self._users_by_id.get(member.user_id)
            if not user:
                continue
            if mention_all or f"@{user.public.username}" in content or f"@{user.public.display_name}" in content:
                if member.user_id not in seen_user_ids:
                    mentioned.append(member)
                    seen_user_ids.add(member.user_id)
        return mentioned

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
        try:
            if node.type == "condition":
                condition = node.parameters.get("expression", "true")
                passed = condition not in ("false", "0", "")
                output = {"condition_passed": passed}
            elif node.type == "loop":
                iterations = min(int(node.parameters.get("max_iterations", "3")), 10)
                output = {"iterations": iterations, "completed": True}
            elif node.tool_name == "file_search":
                file = self._find_file(payload.file_id) if payload.file_id else None
                output = {"matched_files": 1 if file else 0, "file_name": file.name if file else None}
            elif node.tool_name == "knowledge_qa":
                kb_id = payload.target_kb_id or next(iter(self._knowledge_bases.keys()), "")
                if kb_id and self._users_by_id:
                    user = next(iter(self._users_by_id.values()))
                    citations = self._retrieve_knowledge_citations(kb_id, str(node.parameters.get("question", "总结内容")), 3, user.public)
                    output = {"citations": len(citations), "kb_id": kb_id}
                else:
                    output = {"citations": 0, "kb_id": kb_id}
            elif node.tool_name == "report_generate":
                fmt = node.parameters.get("format", "markdown")
                file = self._find_file(payload.file_id) if payload.file_id else None
                output = {"format": fmt, "generated": True, "source_file": file.name if file else None}
            elif node.type == "output":
                output = {"stored": True}
            else:
                output = {"accepted": True}
        except Exception as exc:
            return WorkflowNodeExecution(
                node_id=node.id, name=node.name, tool_name=tool_name,
                status="failed", input=node_input,
                output={"error": str(exc)},
            )
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
            for file_item in [*self._files, *(deleted.file for deleted in self._deleted_files.values())]:
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
            file_item = self._find_file_for_permission(resource_id)
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

    def _broadcast_ws(self, channel: str, event: str, data: dict[str, object]) -> None:
        """Fire-and-forget WebSocket broadcast."""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(ws_manager.broadcast(channel, event, data))
        except Exception:
            pass

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

    def _find_file_for_permission(self, file_id: str) -> FileItem:
        for file_item in self._files:
            if file_item.id == file_id:
                return file_item
        deleted = self._deleted_files.get(file_id)
        if deleted:
            return deleted.file
        raise WorkspaceError(404, "FILE_NOT_FOUND", "文件不存在或无权访问", {"file_id": file_id})

    def _read_file_content(self, file_id: str) -> bytes:
        content = self._file_contents.get(file_id)
        if content is None:
            raise WorkspaceError(404, "FILE_NOT_FOUND", "文件不存在或无权访问", {"file_id": file_id})
        return content

    def _create_share_token(self, file_id: str, actor_id: int) -> str:
        payload = {
            "file_id": file_id,
            "sub": str(actor_id),
            "jti": secrets.token_hex(8),
            "iat": int(datetime.now(UTC).timestamp()),
        }
        signing_input = self._b64(payload)
        signature = hmac.new(self._secret.encode(), signing_input.encode(), hashlib.sha256).digest()
        return f"{signing_input}.{self._b64_bytes(signature)}"

    def _find_share_link(self, token: str) -> StoredShareLink:
        share_link = self._share_links.get(token)
        if not share_link:
            raise WorkspaceError(404, "SHARE_LINK_NOT_FOUND", "分享链接不存在或已失效", {"token": token})
        return share_link

    def _share_link_public(self, share_link: StoredShareLink) -> ShareLinkPublic:
        return ShareLinkPublic(
            id=share_link.id,
            file_id=share_link.file_id,
            token=share_link.token,
            url=f"/api/v1/share-links/{share_link.token}/download",
            expires_at=share_link.expires_at,
            download_limit=share_link.download_limit,
            download_count=share_link.download_count,
            has_password=share_link.password_hash is not None,
        )

    def _find_file_by_name_in_folder(self, name: str, folder_id: str) -> FileItem | None:
        for file_item in self._files:
            if file_item.folder_id == folder_id and file_item.name == name:
                return file_item
        return None

    def _save_file_content(
        self,
        filename: str,
        folder: StoredFolder,
        content: bytes,
        tags: list[str],
        actor: UserPublic,
        audit_action: str,
    ) -> FileItem:
        digest = hashlib.sha256(content).hexdigest()
        existing_file = self._find_file_by_name_in_folder(filename, folder.id)
        if existing_file:
            self._append_file_version(existing_file, filename, content, actor.username)
            updated = existing_file.model_copy(
                update={
                    "name": filename,
                    "type": self._file_type(filename),
                    "size": len(content),
                    "sha256": digest,
                    "parse_status": "queued",
                    "tags": tags,
                    "updated_at": datetime.now(UTC),
                    "permission_scope": self._permission_scope_for_folder(folder),
                }
            )
            self._file_contents[updated.id] = content
            self._replace_file(updated, move_to_front=True)
            self._record_audit(actor.username, audit_action, "file", updated.name)
            return updated

        item = FileItem(
            id=self._new_file_id(digest),
            name=filename,
            folder_id=folder.id,
            type=self._file_type(filename),
            size=len(content),
            sha256=digest,
            parse_status="queued",
            tags=tags,
            updated_at=datetime.now(UTC),
            permission_scope=self._permission_scope_for_folder(folder),
            knowledge_base_ids=[],
        )
        self._files.insert(0, item)
        self._file_contents[item.id] = content
        self._append_file_version(item, item.name, content, actor.username)
        self._record_audit(actor.username, audit_action, "file", item.name)
        return item

    def _find_multipart_upload(self, session_id: str, actor: UserPublic) -> StoredMultipartUpload:
        session = self._multipart_uploads.get(session_id)
        if not session or session.created_by != actor.id:
            raise WorkspaceError(404, "MULTIPART_UPLOAD_NOT_FOUND", "分片上传会话不存在", {"session_id": session_id})
        return session

    def _ensure_multipart_uploading(self, session: StoredMultipartUpload) -> None:
        now = datetime.now(UTC)
        if now >= session.expires_at:
            session.status = "expired"
        if session.status != "uploading":
            raise WorkspaceError(
                409,
                "MULTIPART_UPLOAD_NOT_ACTIVE",
                "分片上传会话已结束或过期",
                {"session_id": session.id, "status": session.status},
            )

    def _multipart_upload_session(self, session: StoredMultipartUpload) -> MultipartUploadSession:
        self._ensure_multipart_session_status(session)
        return MultipartUploadSession(
            id=session.id,
            filename=session.filename,
            folder_id=session.folder_id,
            size=session.size,
            sha256=session.sha256,
            chunk_size=session.chunk_size,
            total_chunks=session.total_chunks,
            received_chunks=sorted(session.chunks),
            status=session.status,  # type: ignore[arg-type]
            expires_at=session.expires_at,
        )

    def _ensure_multipart_session_status(self, session: StoredMultipartUpload) -> None:
        if session.status == "uploading" and datetime.now(UTC) >= session.expires_at:
            session.status = "expired"

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
        existing_ids.update(self._deleted_files)
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


workspace_service = WorkspaceService()
