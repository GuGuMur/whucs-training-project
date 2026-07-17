"""WorkspaceService backed by SQLAlchemy — full DB migration."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domain.schemas import (
    FileItem, FolderItem, FolderTreeResponse, UserCreate, UserPublic, UserUpdate,
    TeamDetail, TeamSummary, WorkspaceSnapshot, ToolDefinition, QAResponse, QARequest,
    NotificationItem, Citation, AuditLogEntry, FileAnnotationItem, FileContentResponse, FileVersionItem,
    ShareLinkPublic, RecycleBinItem, KnowledgeBasePublic, KnowledgeDocumentPublic,
    KnowledgeConversationDetailResponse, KnowledgeConversationListResponse,
    KnowledgeConversationPublic, KnowledgeMessagePublic,
    PermissionRulePublic, WorkflowDefinition, WorkflowExecutionResponse, WorkflowExecutionRecord,
    WorkflowVersionPublic, AgentTaskRequest,
    AgentMessage as AgentMessageSchema, AgentPlanRevision as AgentPlanRevisionSchema,
    AgentPlanPreviewResponse, AgentTaskListResponse, AgentTaskResponse, AgentStep,
    AgentToolCall as AgentToolCallSchema,
)
from app.models import (
    User, File, Folder, FileVersion, DeletedFile, FileAnnotation, ShareLink,
    Team, TeamMember, TeamInvite, TeamMessage,
    KnowledgeBase, KnowledgeCitationSnapshot, KnowledgeConversation,
    KnowledgeDocument, KnowledgeChunk, KnowledgeMessage,
    Workflow, WorkflowDebugSession, WorkflowExecution, WorkflowVersion, AgentMessage, AgentPlanRevision, AgentTask, AgentTaskStep, AgentToolCall,
    PermissionRule, Notification, AuditLog, Conversation, MultipartUpload,
)
from app.repositories import (
    UserRepository, FileRepository, FileVersionRepository, AnnotationRepository,
    DeletedFileRepository, ShareLinkRepository, FolderRepository,
    TeamRepository, TeamMemberRepository, TeamInviteRepository, TeamMessageRepository,
    KnowledgeBaseRepository, KnowledgeCitationSnapshotRepository, KnowledgeChunkRepository,
    KnowledgeConversationRepository, KnowledgeDocumentRepository, KnowledgeMessageRepository,
    WorkflowRepository, WorkflowDebugSessionRepository, WorkflowExecutionRepository, WorkflowVersionRepository,
    AgentMessageRepository, AgentPlanRevisionRepository, AgentTaskRepository,
    AgentTaskStepRepository, AgentToolCallRepository, PermissionRepository, NotificationRepository,
    AuditLogRepository, ConversationRepository, MultipartUploadRepository,
)
from app.services.llm import _get_llm
from app.services.parser import parse_document, ParseError
from app.services.workspace import WorkspaceError
from app.services.agent_executor import AgentExecutor
from app.services.rag_pipeline import RagPipeline
from app.services.tool_registry import ToolRegistry
import faiss

SECRET = "dev-workspace-secret"
_FILE_CONTENTS: dict[str, bytes] = {}
_MULTIPART_CHUNKS: dict[str, dict[int, bytes]] = {}
_MULTIPART_TAGS: dict[str, list[str]] = {}
_CONTENT_STORAGE_DIR = Path(__file__).resolve().parents[2] / ".data" / "file-contents"
_EDITABLE_FILE_TYPES = {"txt", "md", "markdown", "csv", "json", "log", "xml", "html", "htm"}


def _content_path(sha256: str) -> Path:
    if len(sha256) != 64 or any(ch not in "0123456789abcdef" for ch in sha256.lower()):
        raise ValueError("INVALID_CONTENT_SHA256")
    return _CONTENT_STORAGE_DIR / sha256[:2] / sha256


def _store_file_content(file_id: str, sha256: str, content: bytes) -> None:
    _FILE_CONTENTS[file_id] = content
    path = _content_path(sha256)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(content)


def _read_file_content(f: File) -> bytes | None:
    content = _FILE_CONTENTS.get(f.id)
    if content is not None and hashlib.sha256(content).hexdigest() == f.sha256:
        path = _content_path(f.sha256)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        return content

    try:
        path = _content_path(f.sha256)
    except ValueError:
        return None
    if not path.exists():
        return None
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != f.sha256:
        return None
    _FILE_CONTENTS[f.id] = content
    return content


def _extract_document_outline(text: str) -> list[str]:
    headings: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            headings.append(line.lstrip("#").strip())
        elif len(line) <= 40 and not line.endswith(("。", ".", "！", "!", "？", "?")):
            headings.append(line)
        if len(headings) >= 12:
            break
    return headings


def _extract_document_keywords(text: str, filename: str) -> list[str]:
    seeds = [part for part in filename.replace(".", " ").replace("-", " ").replace("_", " ").split() if part]
    for token in ("算法", "动态规划", "复杂度", "数据库", "事务", "索引", "网络", "TCP", "HTTP", "缓存", "实验", "需求", "报告"):
        if token in text:
            seeds.append(token)
    keywords: list[str] = []
    for seed in seeds:
        if seed not in keywords:
            keywords.append(seed)
        if len(keywords) >= 12:
            break
    return keywords


def _summarize_document_text(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ""
    joined = " ".join(lines[:4])
    return joined if len(joined) <= 260 else f"{joined[:260].rstrip()}..."


def _estimate_document_tokens(text: str) -> int:
    ascii_words = sum(1 for part in text.split() if part.isascii())
    non_ascii_chars = sum(1 for char in text if not char.isascii() and not char.isspace())
    return ascii_words + max(1, non_ascii_chars // 2)


def _read_content_by_sha(sha256: str) -> bytes | None:
    try:
        path = _content_path(sha256)
    except ValueError:
        return None
    if not path.exists():
        return None
    content = path.read_bytes()
    if hashlib.sha256(content).hexdigest() != sha256:
        return None
    return content


def _json_loads_object(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _json_loads_list(raw: str | None) -> list[Any]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return value if isinstance(value, list) else []


def _jsonable_list(items: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in list(items or []):
        if hasattr(item, "model_dump"):
            dumped = item.model_dump()
            if isinstance(dumped, dict):
                result.append(dumped)
        elif isinstance(item, dict):
            result.append(dict(item))
    return result


async def _safe_list_members(svc, team_id: str):
    try:
        return await svc._members.list_by_team(team_id)
    except Exception:
        return []


class WorkspaceServiceDB:
    def __init__(self, session: AsyncSession):
        self._s = session
        self._users = UserRepository(session)
        self._files = FileRepository(session)
        self._versions = FileVersionRepository(session)
        self._annotations = AnnotationRepository(session)
        self._deleted = DeletedFileRepository(session)
        self._shares = ShareLinkRepository(session)
        self._folders = FolderRepository(session)
        self._teams = TeamRepository(session)
        self._members = TeamMemberRepository(session)
        self._invites = TeamInviteRepository(session)
        self._messages = TeamMessageRepository(session)
        self._kbs = KnowledgeBaseRepository(session)
        self._docs = KnowledgeDocumentRepository(session)
        self._chunks = KnowledgeChunkRepository(session)
        self._knowledge_conversations = KnowledgeConversationRepository(session)
        self._knowledge_messages = KnowledgeMessageRepository(session)
        self._knowledge_citations = KnowledgeCitationSnapshotRepository(session)
        self._workflows = WorkflowRepository(session)
        self._workflow_versions = WorkflowVersionRepository(session)
        self._workflow_executions = WorkflowExecutionRepository(session)
        self._workflow_debug_sessions = WorkflowDebugSessionRepository(session)
        self._agent_tasks = AgentTaskRepository(session)
        self._agent_steps = AgentTaskStepRepository(session)
        self._agent_messages = AgentMessageRepository(session)
        self._agent_tool_calls = AgentToolCallRepository(session)
        self._agent_plan_revisions = AgentPlanRevisionRepository(session)
        self._perms = PermissionRepository(session)
        self._notifs = NotificationRepository(session)
        self._audit = AuditLogRepository(session)
        self._convs = ConversationRepository(session)
        self._uploads = MultipartUploadRepository(session)
        self._faiss: dict[str, tuple[faiss.Index, list[str], dict]] = {}
        self._rag_pipeline = RagPipeline(self._docs, self._chunks, self._faiss)
        self._tool_registry = ToolRegistry()
        self._agent_executor = AgentExecutor(
            self._tool_registry,
            max_runtime_seconds=settings.AGENT_MAX_RUNTIME_SECONDS,
        )

    # ── Auth ──
    def _hash(self, pw: str) -> str:
        """PBKDF2-HMAC-SHA256 with per-user 128-bit random salt (120 000 iterations)."""
        salt = secrets.token_bytes(16)
        dk = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 120_000)
        return base64.b64encode(salt + dk).decode()

    @staticmethod
    def _is_legacy_hash(stored: str) -> bool:
        """Detect legacy SHA-256 hex digests (64 hex chars, no base64 padding)."""
        return len(stored) == 64 and all(ch in "0123456789abcdef" for ch in stored)

    def _verify(self, stored: str, pw: str) -> bool:
        """Verify password against stored hash. Returns True on match."""
        if self._is_legacy_hash(stored):
            expected = hashlib.sha256(f"{SECRET}:{pw}".encode()).hexdigest()
            return hmac.compare_digest(expected, stored)
        try:
            raw = base64.b64decode(stored)
        except Exception:
            return False
        if len(raw) < 48:  # minimum: 16-byte salt + 32-byte dk
            return False
        salt, dk = raw[:16], raw[16:]
        expected = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 120_000)
        return hmac.compare_digest(dk, expected)

    def _create_token(self, user_id: int, kind: str) -> str:
        exp = int((datetime.now(UTC) + timedelta(seconds=1800 if kind ==
                  "access" else 86400)).timestamp())
        header = self._b64({"alg": "HS256", "typ": "JWT"})
        payload = self._b64({"sub": user_id, "kind": kind, "exp": exp, "iat": int(
            datetime.now(UTC).timestamp())})
        sig = self._b64_bytes(hmac.new(
            SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
        return f"{header}.{payload}.{sig}"

    def _b64(self, d: dict) -> str:
        return self._b64_bytes(json.dumps(d, separators=(",", ":"), ensure_ascii=False).encode())

    def _b64_bytes(self, b: bytes) -> str:
        return base64.urlsafe_b64encode(b).decode().rstrip("=")

    def _read_token(self, token: str, expected_kind: str) -> int:
        try:
            hp, pp, sp = token.split(".")
        except ValueError:
            raise ValueError("INVALID_TOKEN")
        expected = self._b64_bytes(
            hmac.new(SECRET.encode(), f"{hp}.{pp}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sp, expected):
            raise ValueError("INVALID_TOKEN")
        payload = json.loads(self._b64_decode(pp))
        if payload.get("kind") != expected_kind:
            raise ValueError("INVALID_TOKEN")
        if int(payload.get("exp", 0)) < int(datetime.now(UTC).timestamp()):
            raise ValueError("TOKEN_EXPIRED")
        return int(payload["sub"])

    def _b64_decode(self, v: str) -> str:
        padded = v + "=" * (-len(v) % 4)
        return base64.urlsafe_b64decode(padded).decode()

    async def register_user(self, payload: UserCreate) -> tuple[UserPublic, str, str]:
        if await self._users.get_by_username(payload.username):
            raise ValueError("USERNAME_EXISTS")
        if await self._users.get_by_email(str(payload.email)):
            raise ValueError("EMAIL_EXISTS")
        db_user = User(username=payload.username, email=str(payload.email),
                       hashed_password=self._hash(payload.password), display_name=payload.username)
        await self._users.create(db_user)
        await self._s.commit()
        pub = UserPublic(id=db_user.id, username=db_user.username,
                         email=db_user.email, display_name=db_user.display_name, roles=["user"])
        await self._ensure_personal_root(pub)
        return pub, self._create_token(db_user.id, "access"), self._create_token(db_user.id, "refresh")

    async def login_user(self, account: str, password: str) -> tuple[UserPublic, str, str]:
        db_user = await self._users.get_by_username(account) or await self._users.get_by_email(account)
        if not db_user or not self._verify(db_user.hashed_password, password):
            raise ValueError("INVALID_CREDENTIALS")
        # Transparently upgrade legacy SHA-256 hashes to PBKDF2 on successful login
        if self._is_legacy_hash(db_user.hashed_password):
            db_user.hashed_password = self._hash(password)
            await self._users.update(db_user)
            await self._s.commit()
        pub = UserPublic(id=db_user.id, username=db_user.username, email=db_user.email,
                         display_name=db_user.display_name, roles=db_user.roles.split(",") if db_user.roles else ["user"])
        return pub, self._create_token(db_user.id, "access"), self._create_token(db_user.id, "refresh")

    async def require_user(self, authorization: str | None) -> UserPublic:
        if not authorization or not authorization.startswith("Bearer "):
            raise ValueError("AUTH_REQUIRED")
        user_id = self._read_token(
            authorization.removeprefix("Bearer ").strip(), "access")
        db_user = await self._users.get_by_id(user_id)
        if not db_user:
            raise ValueError("INVALID_TOKEN")
        return UserPublic(id=db_user.id, username=db_user.username, email=db_user.email, display_name=db_user.display_name, roles=db_user.roles.split(",") if db_user.roles else ["user"])

    async def _ensure_personal_root(self, user: UserPublic) -> str:
        """Create (if needed) and return the user's personal root folder ID."""
        root_id = f"personal-root-{user.id}"
        if not await self._folders.get_by_id(root_id):
            await self._folders.create(Folder(id=root_id, name="个人空间", scope="personal", owner_id=user.id))
            await self._s.commit()
        return root_id

    async def _resolve_upload_folder(self, folder_id: str | None, user: UserPublic) -> Folder:
        root_id = await self._ensure_personal_root(user)
        requested_id = (folder_id or "").strip()
        effective_id = root_id if requested_id in {"", "personal-root"} else requested_id
        folder = await self._folders.get_by_id(effective_id)
        if not folder:
            raise WorkspaceError(404, "FOLDER_NOT_FOUND", "文件夹不存在", {"folder_id": requested_id})
        if folder.scope == "personal" and folder.owner_id != user.id:
            raise WorkspaceError(403, "FOLDER_WRITE_FORBIDDEN", "无权写入该个人文件夹", {"folder_id": folder.id})
        if folder.scope == "team" and folder.team_id:
            members = await _safe_list_members(self, folder.team_id)
            member = next((m for m in members if m.user_id == user.id and m.status == "active"), None)
            if member is None or member.role == "guest":
                raise WorkspaceError(403, "FOLDER_WRITE_FORBIDDEN", "无权写入该团队文件夹", {"folder_id": folder.id})
        return folder

    async def _team_member_for_user(self, team_id: str | None, user: UserPublic) -> TeamMember | None:
        if not team_id:
            return None
        members = await _safe_list_members(self, team_id)
        return next((m for m in members if m.user_id == user.id and m.status == "active"), None)

    async def _file_folder(self, file: File) -> Folder | None:
        return await self._folders.get_by_id(file.folder_id)

    async def _file_team_id(self, file: File) -> str | None:
        if file.team_id:
            return file.team_id
        folder = await self._file_folder(file)
        return folder.team_id if folder and folder.scope == "team" else None

    async def _can_read_file(self, file: File, user: UserPublic) -> bool:
        if file.owner_id is None or file.owner_id == user.id:
            return True
        team_id = await self._file_team_id(file)
        if team_id:
            return await self._team_member_for_user(team_id, user) is not None
        return False

    async def _ensure_can_read_file(self, file: File, user: UserPublic) -> None:
        if await self._can_read_file(file, user):
            return
        raise WorkspaceError(403, "FILE_READ_FORBIDDEN", "没有读取该文件的权限", {"file_id": file.id})

    async def _ensure_can_write_file(self, file: File, user: UserPublic) -> None:
        team_id = await self._file_team_id(file)
        if team_id:
            member = await self._team_member_for_user(team_id, user)
            if member is None:
                raise WorkspaceError(403, "FILE_WRITE_FORBIDDEN", "没有修改该文件的权限", {"file_id": file.id})
            if member.role == "guest":
                raise WorkspaceError(403, "FILE_WRITE_FORBIDDEN", "访客只能查看团队文件", {"file_id": file.id})
            return
        if file.owner_id == user.id:
            return
        raise WorkspaceError(403, "FILE_WRITE_FORBIDDEN", "没有修改该文件的权限", {"file_id": file.id})

    async def _ensure_personal_kb(self, user: UserPublic) -> Any:
        """Get or create the user's personal knowledge base for auto-indexing."""
        import secrets as _s
        kb_name = "我的知识库"
        existing_kbs = await self._kbs.list_all()
        personal_kb = next((kb for kb in existing_kbs if kb.name == kb_name and kb.owner_id == user.id), None)
        if not personal_kb:
            personal_kb = KnowledgeBase(id=f"kb-{_s.token_hex(4)}", name=kb_name, description="自动创建的个人知识库，上传文件将自动入库", owner_id=user.id)
            await self._kbs.create(personal_kb)
            await self._s.commit()
        return personal_kb

    # ── Files ──
    async def list_files(self, user: UserPublic) -> list[FileItem]:
        all_files = await self._files.list_all()
        files = [f for f in all_files if await self._can_read_file(f, user)]
        return [_file_to_item(f) for f in files]

    async def upload_file(self, filename: str, folder_id: str, content: bytes, tags: list[str], user: UserPublic) -> FileItem:
        folder = await self._resolve_upload_folder(folder_id, user)
        permission_scope = "团队" if folder.scope == "team" else "个人"
        team_id = folder.team_id if folder.scope == "team" else None
        digest = hashlib.sha256(content).hexdigest()
        fid = f"file-{digest[:12]}"
        if await self._files.get_by_id(fid):
            fid = f"file-{digest[:8]}-{secrets.token_hex(4)}"
        f = File(id=fid, name=filename, folder_id=folder.id, type=_file_type(filename), size=len(
            content), sha256=digest, tags=",".join(tags), created_by=user.username, owner_id=user.id,
            permission_scope=permission_scope, team_id=team_id)
        _store_file_content(fid, digest, content)
        await self._files.create(f)
        await self._append_file_version(f, content, user)
        await self._s.commit()
        # Auto-index into personal knowledge base
        try:
            personal_kb = await self._ensure_personal_kb(user)
            await self.add_knowledge_document(personal_kb.id, type('payload', (), {'file_id': fid})(), user)
        except Exception:
            pass  # Non-fatal: file upload succeeds even if auto-index fails
        # Refresh to pick up parse_status updated by add_knowledge_document
        await self._s.refresh(f)
        return _file_to_item(f)

    async def reparse_file(self, file_id: str, user: UserPublic) -> FileItem:
        f = await self._files.get_by_id(file_id)
        if not f:
            from fastapi import HTTPException
            raise HTTPException(404, detail="文件不存在")
        await self._ensure_can_write_file(f, user)
        content = _read_file_content(f)
        if content is None:
            from fastapi import HTTPException
            f.parse_status = "failed"
            await self._files.update(f)
            await self._s.commit()
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "FILE_CONTENT_MISSING",
                    "message": "原始文件内容缺失，请重新上传该文件后再解析",
                    "file_id": file_id,
                },
            )
        try:
            parsed = parse_document(f.name, content, f.type)
            f.parse_status = "indexed"
            kb_ids = [k.strip() for k in (f.knowledge_base_ids or "").split(",") if k.strip()]
            for kb_id in kb_ids:
                docs = [d for d in (await self._docs.list_by_kb(kb_id)) if d.file_id == file_id]
                for doc in docs:
                    from app.services.parser import clean_text, chunk_paragraphs
                    cleaned = clean_text(parsed.text)
                    text_chunks = chunk_paragraphs(cleaned, target_size=600)
                    old_chunks = await self._chunks.list_by_document(doc.id)
                    for oc in old_chunks:
                        await self._s.delete(oc)
                    import secrets as _s
                    for i, tc in enumerate(text_chunks):
                        self._s.add(KnowledgeChunk(id=f"{doc.id}-chunk-{i+1}", document_id=doc.id,
                            content=f"[{f.name}]\n{tc}", page_no=1, paragraph_no=i+1))
                    doc.index_status = "indexed"
                self._faiss.pop(kb_id, None)
        except Exception:
            f.parse_status = "failed"
        await self._files.update(f)
        await self._s.commit()
        return _file_to_item(f)

    async def delete_file(self, file_id: str, user: UserPublic) -> None:
        f = await self._files.get_by_id(file_id)
        if not f:
            raise ValueError("NOT_FOUND")
        await self._ensure_can_write_file(f, user)
        await self._deleted.create(DeletedFile(id=f"del-{secrets.token_hex(4)}", file_id=file_id, deleted_by=user.username))
        await self._files.delete(f)
        await self._s.commit()

    # ── Folders ──
    async def folder_tree(self, user: UserPublic) -> list[FolderItem]:
        await self._ensure_personal_root(user)
        all_folders = await self._folders.list_all()
        # Include personal folders + team folders where user is a member
        team_ids = set()
        for t in await self._teams.list_all():
            try:
                tms = await self._members.list_by_team(t.id)
                if any(m.user_id == user.id and m.status == "active" for m in tms):
                    team_ids.add(t.id)
            except Exception:
                pass
        folders = [f for f in all_folders if f.owner_id ==
                   user.id or (f.team_id and f.team_id in team_ids)]
        return _build_tree(folders)

    # ── Auth (extended) ──
    async def refresh_session(self, refresh_token: str) -> tuple[UserPublic, str, str]:
        user_id = self._read_token(refresh_token, "refresh")
        db_user = await self._users.get_by_id(user_id)
        if not db_user:
            raise ValueError("INVALID_TOKEN")
        pub = UserPublic(id=db_user.id, username=db_user.username, email=db_user.email,
                         display_name=db_user.display_name, roles=db_user.roles.split(",") if db_user.roles else ["user"])
        return pub, self._create_token(db_user.id, "access"), self._create_token(db_user.id, "refresh")

    async def update_user_profile(self, user_id: int, payload: Any) -> UserPublic:
        u = await self._users.get_by_id(user_id)
        if not u:
            return UserPublic(id=user_id, username="unknown", email="", display_name="", roles=["user"])
        if (getattr(payload, "display_name", None)):
            u.display_name = getattr(payload, "display_name", None)
        if (getattr(payload, "email", None)):
            u.email = getattr(payload, "email", None)
        await self._users.update(u)
        await self._s.commit()
        return UserPublic(id=u.id, username=u.username, email=u.email, display_name=u.display_name, roles=u.roles.split(",") if u.roles else ["user"])
        if not u:
            return UserPublic(id=user_id, username="unknown", email="", display_name="", roles=["user"])
        await self._users.update(u)
        await self._s.commit()
        return UserPublic(id=u.id, username=u.username, email=u.email, display_name=u.display_name, roles=u.roles.split(",") if u.roles else ["user"])

    # ── Files (extended) ──
    async def update_file(self, file_id: str, payload: Any, user: UserPublic) -> FileItem:
        f = await self._files.get_by_id(file_id)
        if not f:
            raise WorkspaceError(404, "FILE_NOT_FOUND", "文件不存在或无权访问", {"file_id": file_id})
        await self._ensure_can_write_file(f, user)
        if (getattr(payload, "name", None)):
            f.name = getattr(payload, "name", None)
        if (getattr(payload, "folder_id", None)):
            target_folder = await self._resolve_upload_folder(getattr(payload, "folder_id", None), user)
            f.folder_id = target_folder.id
            f.permission_scope = "团队" if target_folder.scope == "team" else "个人"
            f.team_id = target_folder.team_id if target_folder.scope == "team" else None
        if getattr(payload, "tags", None) is not None:
            f.tags = ",".join(getattr(payload, "tags", []))
        await self._files.update(f)
        await self._s.commit()
        return _file_to_item(f)

    async def copy_file(self, file_id: str, payload: Any, user: UserPublic) -> FileItem:
        src = await self._files.get_by_id(file_id)
        if not src:
            raise WorkspaceError(404, "FILE_NOT_FOUND", "文件不存在或无权访问", {"file_id": file_id})
        await self._ensure_can_read_file(src, user)
        import secrets as _s
        cid = f"file-{_s.token_hex(6)}"
        target = (getattr(payload, "target_folder_id", None) or src.folder_id)
        target_folder = await self._resolve_upload_folder(target, user)
        cp = File(id=cid, name=f"副本_{src.name}", folder_id=target_folder.id, type=src.type, size=src.size, sha256=src.sha256,
                  content_type=src.content_type, permission_scope="团队" if target_folder.scope == "team" else "个人",
                  tags=src.tags, created_by=user.username, owner_id=user.id,
                  team_id=target_folder.team_id if target_folder.scope == "team" else None)
        content = _read_file_content(src)
        if content is not None:
            _FILE_CONTENTS[cid] = content
        await self._files.create(cp)
        await self._s.commit()
        return _file_to_item(cp)

    async def create_share_link(self, file_id: str, payload: Any, user: UserPublic) -> ShareLinkPublic:
        f = await self._files.get_by_id(file_id)
        if not f:
            raise WorkspaceError(404, "FILE_NOT_FOUND", "文件不存在或无权访问", {"file_id": file_id})
        await self._ensure_can_read_file(f, user)
        import secrets as _s
        from datetime import UTC, datetime, timedelta
        tok = _s.token_hex(16)
        now = datetime.now(UTC)
        sl = ShareLink(id=f"share-{_s.token_hex(4)}", file_id=file_id, token=tok,
                       download_limit=10, download_count=0, expires_at=now + timedelta(hours=1))
        await self._shares.create(sl)
        await self._s.commit()
        return ShareLinkPublic(id=sl.id, file_id=file_id, token=tok, url=f"/api/v2/share-links/{tok}/download", expires_at=str(sl.expires_at), download_limit=10, download_count=0, has_password=False)

    async def list_file_annotations(self, file_id: str, user: UserPublic) -> list[FileAnnotationItem]:
        f = await self._files.get_by_id(file_id)
        if not f:
            raise WorkspaceError(404, "FILE_NOT_FOUND", "文件不存在或无权访问", {"file_id": file_id})
        await self._ensure_can_read_file(f, user)
        anns = await self._annotations.list_by_file(file_id)
        return [FileAnnotationItem(id=a.id, file_id=a.file_id, author_id=a.author_id, author_name=a.author_name, content=a.content, created_at=str(a.created_at)) for a in anns]

    async def create_file_annotation(self, file_id: str, payload: Any, user: UserPublic) -> FileAnnotationItem:
        f = await self._files.get_by_id(file_id)
        if not f:
            raise WorkspaceError(404, "FILE_NOT_FOUND", "文件不存在或无权访问", {"file_id": file_id})
        await self._ensure_can_read_file(f, user)
        import secrets as _s
        aid = f"ann-{_s.token_hex(4)}"
        a = FileAnnotation(id=aid, file_id=file_id, author_id=user.id,
                           author_name=user.display_name, content=getattr(payload, "content", ""))
        await self._annotations.create(a)
        await self._s.commit()
        return FileAnnotationItem(id=aid, file_id=file_id, author_id=user.id, author_name=user.display_name, content=a.content, created_at=str(a.created_at))

    async def reply_file_annotation(self, annotation_id: str, payload: Any, user: UserPublic) -> Any:
        import secrets as _s
        parent = await self._annotations.get_by_id(annotation_id)
        if not parent:
            raise WorkspaceError(404, "ANNOTATION_NOT_FOUND", "批注不存在或无权访问", {"annotation_id": annotation_id})
        f = await self._files.get_by_id(parent.file_id)
        if not f:
            raise WorkspaceError(404, "FILE_NOT_FOUND", "文件不存在或无权访问", {"file_id": parent.file_id})
        await self._ensure_can_read_file(f, user)
        rid = f"reply-{_s.token_hex(4)}"
        reply = FileAnnotation(id=rid, file_id=parent.file_id, author_id=user.id,
                               author_name=user.display_name, content=getattr(payload, "content", ""), parent_id=annotation_id)
        await self._annotations.create(reply)
        await self._s.commit()
        return {"id": rid, "content": reply.content, "author_name": reply.author_name, "parent_id": annotation_id}

    async def delete_file_annotation(self, file_id: str, annotation_id: str, user: UserPublic) -> None:
        a = await self._annotations.get_by_id(annotation_id)
        if a:
            f = await self._files.get_by_id(a.file_id)
            if not f:
                raise WorkspaceError(404, "FILE_NOT_FOUND", "文件不存在或无权访问", {"file_id": a.file_id})
            if a.file_id != file_id:
                raise WorkspaceError(404, "ANNOTATION_NOT_FOUND", "批注不存在或无权访问", {"annotation_id": annotation_id})
            if a.author_id != user.id:
                await self._ensure_can_write_file(f, user)
            await self._annotations.delete(a)
            await self._s.commit()

    async def download_file(self, file_id: str, user: UserPublic) -> tuple[FileItem, bytes]:
        f = await self._files.get_by_id(file_id)
        if not f:
            from fastapi import HTTPException
            raise HTTPException(404, detail="文件不存在")
        await self._ensure_can_read_file(f, user)
        content = _read_file_content(f)
        if content is None:
            from fastapi import HTTPException
            raise HTTPException(404, detail="文件内容不存在")
        return _file_to_item(f), content

    async def read_file_content_text(self, file_id: str, user: UserPublic) -> FileContentResponse:
        f = await self._files.get_by_id(file_id)
        if not f:
            from fastapi import HTTPException
            raise HTTPException(404, detail="文件不存在")
        await self._ensure_can_read_file(f, user)
        content = _read_file_content(f)
        if content is None:
            from fastapi import HTTPException
            raise HTTPException(404, detail="文件内容不存在")
        return FileContentResponse(
            file_id=f.id,
            name=f.name,
            type=f.type,
            content=content.decode("utf-8", errors="replace"),
            editable=f.type.lower() in _EDITABLE_FILE_TYPES,
            updated_at=f.updated_at,
        )

    async def update_file_content_text(self, file_id: str, payload: Any, user: UserPublic) -> FileItem:
        f = await self._files.get_by_id(file_id)
        if not f:
            from fastapi import HTTPException
            raise HTTPException(404, detail="文件不存在")
        await self._ensure_can_write_file(f, user)
        if f.type.lower() not in _EDITABLE_FILE_TYPES:
            from fastapi import HTTPException
            raise HTTPException(415, detail="该文件类型暂不支持在线编辑")
        content = getattr(payload, "content", "").encode("utf-8")
        digest = hashlib.sha256(content).hexdigest()
        f.size = len(content)
        f.sha256 = digest
        f.parse_status = "queued"
        _store_file_content(f.id, digest, content)
        await self._append_file_version(f, content, user)
        await self._files.update(f)
        await self._s.commit()
        return _file_to_item(f)

    async def list_file_versions(self, file_id: str, user: UserPublic) -> list[FileVersionItem]:
        vs = await self._versions.list_by_file(file_id)
        f = await self._files.get_by_id(file_id)
        if not f:
            raise WorkspaceError(404, "FILE_NOT_FOUND", "文件不存在或无权访问", {"file_id": file_id})
        await self._ensure_can_read_file(f, user)
        current_version_no = None
        matching = [v.version_no for v in vs if v.sha256 == f.sha256]
        current_version_no = max(matching) if matching else None
        return [
            FileVersionItem(
                id=v.id,
                file_id=v.file_id,
                version_no=v.version_no,
                name=v.name,
                size=v.size,
                sha256=v.sha256,
                created_by=v.created_by,
                created_at=str(v.created_at),
                is_current=v.version_no == current_version_no,
            )
            for v in vs
        ]

    async def restore_file_version(self, file_id: str, version_id: str, user: UserPublic) -> FileItem:
        f = await self._files.get_by_id(file_id)
        version = await self._versions.get_by_id(version_id)
        if not f or not version or version.file_id != file_id:
            from fastapi import HTTPException
            raise HTTPException(404, detail="文件版本不存在")
        await self._ensure_can_write_file(f, user)
        content = _read_content_by_sha(version.content_key or version.sha256)
        if content is None:
            from fastapi import HTTPException
            raise HTTPException(404, detail="版本内容不存在")
        f.name = version.name
        f.type = _file_type(version.name)
        f.size = version.size
        f.sha256 = version.sha256
        f.parse_status = "queued"
        _store_file_content(f.id, version.sha256, content)
        await self._append_file_version(f, content, user)
        await self._files.update(f)
        await self._s.commit()
        return _file_to_item(f)

    async def restore_deleted_file(self, file_id: str, user: UserPublic) -> FileItem:
        deleted_items = await self._deleted.list_all()
        deleted = next((item for item in deleted_items if item.file_id == file_id and item.deleted_by == user.username), None)
        if deleted is None:
            raise WorkspaceError(404, "DELETED_FILE_NOT_FOUND", "回收站文件不存在", {"file_id": file_id})
        return FileItem(id=file_id, name="restored", folder_id="personal-root", type="unknown", size=0, sha256="", content_type="", permission_scope="个人", parse_status="queued", tags=[], knowledge_base_ids=[], updated_at=deleted.deleted_at, created_at=deleted.deleted_at, created_by=user.username)

    async def init_multipart_upload(self, payload: Any, user: UserPublic) -> Any:
        import secrets as _s
        from datetime import UTC, datetime, timedelta
        folder = await self._resolve_upload_folder(getattr(payload, "folder_id", ""), user)
        uid = f"upload-{_s.token_hex(4)}"
        mu = MultipartUpload(id=uid, filename=getattr(payload, "filename", ""), folder_id=folder.id, size=getattr(payload, "size", 0), sha256=getattr(payload, "sha256", ""), chunk_size=getattr(payload, "chunk_size", 0), total_chunks=(
            getattr(payload, "size", 0) + getattr(payload, "chunk_size", 1) - 1) // max(getattr(payload, "chunk_size", 1), 1), created_by=user.id, created_at=datetime.now(UTC), expires_at=datetime.now(UTC) + timedelta(hours=1))
        await self._uploads.create(mu)
        _MULTIPART_CHUNKS[uid] = {}
        _MULTIPART_TAGS[uid] = list(getattr(payload, "tags", []) or [])
        await self._s.commit()
        return self._multipart_session_payload(mu)

    async def get_multipart_upload(self, session_id: str, user: UserPublic) -> Any:
        mu = await self._uploads.get_by_id(session_id)
        if not mu or mu.created_by != user.id:
            raise WorkspaceError(404, "MULTIPART_UPLOAD_NOT_FOUND", "分片上传会话不存在", {"session_id": session_id})
        return self._multipart_session_payload(mu)

    async def upload_multipart_chunk(self, session_id: str, chunk_index: int, chunk_data: bytes, sha256: str, user: UserPublic) -> Any:
        mu = await self._uploads.get_by_id(session_id)
        if not mu or mu.created_by != user.id:
            raise WorkspaceError(404, "MULTIPART_UPLOAD_NOT_FOUND", "分片上传会话不存在", {"session_id": session_id})
        if chunk_index < 0 or chunk_index >= mu.total_chunks:
            raise WorkspaceError(400, "INVALID_CHUNK_INDEX", "分片序号无效", {"chunk_index": chunk_index})
        if hashlib.sha256(chunk_data).hexdigest() != sha256:
            raise WorkspaceError(400, "CHUNK_HASH_MISMATCH", "分片校验失败", {"chunk_index": chunk_index})
        chunks = _MULTIPART_CHUNKS.setdefault(session_id, {})
        chunks[chunk_index] = chunk_data
        return {
            "session_id": session_id,
            "chunk_index": chunk_index,
            "received_chunks": sorted(chunks),
            "total_chunks": mu.total_chunks,
            "status": "uploading",
        }

    async def complete_multipart_upload(self, session_id: str, user: UserPublic) -> FileItem:
        mu = await self._uploads.get_by_id(session_id)
        if not mu or mu.created_by != user.id:
            raise WorkspaceError(404, "MULTIPART_UPLOAD_NOT_FOUND", "分片上传会话不存在", {"session_id": session_id})
        chunks = _MULTIPART_CHUNKS.get(session_id, {})
        missing = [index for index in range(mu.total_chunks) if index not in chunks]
        if missing:
            raise WorkspaceError(400, "MULTIPART_UPLOAD_INCOMPLETE", "分片尚未上传完整", {"missing_chunks": missing})
        content = b"".join(chunks[index] for index in range(mu.total_chunks))
        if len(content) != mu.size:
            raise WorkspaceError(400, "MULTIPART_SIZE_MISMATCH", "文件大小校验失败", {"expected": mu.size, "actual": len(content)})
        if hashlib.sha256(content).hexdigest() != mu.sha256:
            raise WorkspaceError(400, "MULTIPART_HASH_MISMATCH", "文件整体校验失败", {"session_id": session_id})
        item = await self.upload_file(mu.filename, mu.folder_id, content, _MULTIPART_TAGS.get(session_id, []), user)
        await self._uploads.delete(mu)
        _MULTIPART_CHUNKS.pop(session_id, None)
        _MULTIPART_TAGS.pop(session_id, None)
        await self._s.commit()
        return item

    def _multipart_session_payload(self, mu: MultipartUpload) -> dict[str, Any]:
        chunks = _MULTIPART_CHUNKS.get(mu.id, {})
        return {
            "id": mu.id,
            "filename": mu.filename,
            "folder_id": mu.folder_id,
            "size": mu.size,
            "sha256": mu.sha256,
            "chunk_size": mu.chunk_size,
            "total_chunks": mu.total_chunks,
            "received_chunks": sorted(chunks),
            "status": "completed" if len(chunks) >= mu.total_chunks else "uploading",
            "expires_at": mu.expires_at,
        }

    async def list_deleted_files(self, user: UserPublic) -> list[RecycleBinItem]:
        items = await self._deleted.list_all()
        items = [item for item in items if item.deleted_by == user.username]
        return [
            RecycleBinItem(
                file=FileItem(
                    id=d.file_id,
                    name="已删除文件",
                    folder_id="",
                    type="unknown",
                    size=0,
                    sha256="",
                    content_type="",
                    permission_scope="个人",
                    parse_status="queued",
                    tags=[],
                    knowledge_base_ids=[],
                    updated_at=d.deleted_at,
                    created_at=d.deleted_at,
                    created_by=d.deleted_by,
                ),
                deleted_at=d.deleted_at,
                deleted_by=d.deleted_by,
            )
            for d in items
        ]

    # ── Folders (extended) ──
    async def create_folder(self, payload: Any, user: UserPublic) -> FolderItem:
        import secrets as _s
        scope = getattr(payload, "scope", None) or "personal"
        root_id = await self._ensure_personal_root(user)
        parent_id = getattr(payload, "parent_id", None) or root_id
        parent = await self._folders.get_by_id(parent_id)
        if not parent:
            parent_id = root_id
            parent = await self._folders.get_by_id(root_id)
        if parent and parent.scope != scope:
            raise ValueError("FOLDER_SCOPE_MISMATCH")
        fid = f"folder-{_s.token_hex(4)}"
        name = getattr(payload, "name", None) or "新文件夹"
        f = Folder(id=fid, name=name, parent_id=parent_id, scope=scope, owner_id=user.id,
                   team_id=parent.team_id if parent and scope == "team" else None)
        await self._folders.create(f)
        await self._s.commit()
        return FolderItem(id=fid, name=f.name, parent_id=f.parent_id, scope=f.scope, permission="管理", children=[])

    async def update_folder(self, folder_id: str, payload: Any, user: UserPublic) -> FolderItem:
        folder = await self._folders.get_by_id(folder_id)
        if not folder:
            raise WorkspaceError(404, "FOLDER_NOT_FOUND", "文件夹不存在", {"folder_id": folder_id})
        if folder.owner_id is not None and folder.owner_id != user.id:
            raise WorkspaceError(403, "PERMISSION_DENIED", "无权修改该文件夹", {"folder_id": folder_id})
        root_id = await self._ensure_personal_root(user)
        # Prevent modification of personal root folders
        if folder_id.startswith("personal-root-"):
            raise WorkspaceError(400, "CANNOT_MODIFY_ROOT", "不能修改个人根目录", {"folder_id": folder_id})

        name = getattr(payload, "name", None)
        parent_id = getattr(payload, "parent_id", None)

        if name is not None and name.strip():
            folder.name = name.strip()

        if parent_id is not None:
            new_parent = await self._folders.get_by_id(parent_id)
            if not new_parent:
                raise WorkspaceError(404, "PARENT_NOT_FOUND", "父文件夹不存在", {"folder_id": parent_id})
            if new_parent.scope != folder.scope:
                raise WorkspaceError(400, "FOLDER_SCOPE_MISMATCH", "不能跨空间移动文件夹", {"folder_id": folder_id})
            # Prevent moving to self or descendant
            if parent_id == folder_id or await self._is_descendant(parent_id, folder_id):
                raise WorkspaceError(400, "INVALID_FOLDER_MOVE", "不能将文件夹移动到自身或子级目录", {"folder_id": folder_id})
            folder.parent_id = parent_id
            folder.team_id = new_parent.team_id

        await self._folders.update(folder)
        await self._s.commit()
        return FolderItem(id=folder.id, name=folder.name, parent_id=folder.parent_id,
                          scope=folder.scope, permission="管理", children=[])

    async def _is_descendant(self, ancestor_id: str, target_id: str) -> bool:
        """Check if ancestor_id is a descendant of target_id by walking up the parent chain."""
        current = await self._folders.get_by_id(ancestor_id)
        visited: set[str] = set()
        while current and current.parent_id and current.parent_id not in visited:
            if current.parent_id == target_id:
                return True
            visited.add(current.parent_id)
            current = await self._folders.get_by_id(current.parent_id)
        return False

    async def delete_folder_tree(self, folder_id: str, user: UserPublic) -> None:
        if folder_id.startswith("personal-root-"):
            raise WorkspaceError(400, "CANNOT_DELETE_ROOT", "不能删除个人根目录", {"folder_id": folder_id})
        folder = await self._folders.get_by_id(folder_id)
        if not folder:
            return
        if folder.owner_id is not None and folder.owner_id != user.id:
            raise WorkspaceError(403, "PERMISSION_DENIED", "无权删除该文件夹", {"folder_id": folder_id})

        # Collect all descendant folder IDs (breadth-first from the target)
        descendant_ids: list[str] = []
        queue = [folder_id]
        while queue:
            fid = queue.pop(0)
            children = await self._folders.list_children(fid)
            for child in children:
                descendant_ids.append(child.id)
                queue.append(child.id)

        # Reassign files in deleted folders to user's personal root
        root_id = await self._ensure_personal_root(user)
        all_files = await self._files.list_all()
        affected_ids = {folder_id, *descendant_ids}
        for f in all_files:
            if f.folder_id in affected_ids:
                f.folder_id = root_id
                await self._files.update(f)

        # Delete folders from leaves up (children first, then the target)
        for fid in reversed(descendant_ids):
            f = await self._folders.get_by_id(fid)
            if f:
                await self._folders.delete(f)
        await self._folders.delete(folder)
        await self._s.commit()

    # ── Teams ──
    async def create_team(self, payload: Any, user: UserPublic) -> TeamDetail:
        import secrets as _s
        tid = f"team-{_s.token_hex(4)}"
        team = Team(id=tid, name=(getattr(payload, "name", None) or "新团队"),
                    description=(getattr(payload, "description", None) or ""),
                    created_by=user.id)
        await self._teams.create(team)
        # Also create member record for the creator
        member = TeamMember(
            id=f"mem-{_s.token_hex(4)}", team_id=tid, user_id=user.id, role="owner")
        await self._members.create(member)
        await self._s.commit()
        # Create team root folder in DB
        rf_id = f"folder-team-{tid}"
        rf = Folder(id=rf_id, name=team.name, scope="team",
                    team_id=tid, owner_id=user.id)
        await self._folders.create(rf)
        await self._s.commit()
        members = await self._members.list_by_team(tid)
        active_members = [m for m in members if m.status == "active"]
        return TeamDetail(id=tid, name=team.name, description=team.description or "",
                          role="owner", member_count=len(active_members), unread_count=0,
                          root_folder=FolderItem(
                              id=rf_id, name=team.name, parent_id=None, scope="team", permission="管理", children=[]),
                          members=[], invites=[])

    async def list_teams(self, user: UserPublic) -> list[TeamSummary]:
        teams = await self._teams.list_all()
        result = []
        for t in teams:
            try:
                members = [m for m in (await _safe_list_members(self, t.id)) if m.status == "active"]
            except Exception:
                members = []
            my_member = next((m for m in members if m.user_id == user.id), None)
            # Only include teams the user is an active member of
            if my_member is None:
                continue
            result.append(TeamSummary(id=t.id, name=t.name, role=my_member.role,
                          member_count=len(members), unread_count=0))
        return result

    async def get_team_detail(self, team_id: str, user: UserPublic) -> TeamDetail:
        team = await self._teams.get_by_id(team_id)
        if not team:
            raise ValueError("TEAM_NOT_FOUND")
        members = [m for m in (await _safe_list_members(self, team_id)) if m.status == "active"]
        my_member = next((m for m in members if m.user_id == user.id), None)
        if my_member is None:
            raise ValueError("NOT_TEAM_MEMBER")
        from app.domain.schemas import TeamMemberPublic
        member_list = []
        for m in members:
            u = await self._users.get_by_id(m.user_id)
            member_list.append(TeamMemberPublic(
                id=m.id, team_id=m.team_id, user_id=m.user_id,
                username=u.username if u else str(m.user_id),
                email=u.email if u else "",
                display_name=u.display_name if u else str(m.user_id),
                role=m.role, status=m.status, joined_at=m.joined_at))
        return TeamDetail(id=team.id, name=team.name, description=team.description or "",
                          role=my_member.role, member_count=len(members), unread_count=0,
                          root_folder=FolderItem(
                              id="root", name="root", parent_id=None, scope="team", permission="管理", children=[]),
                          members=member_list, invites=[])

    async def _ensure_team_member(self, team_id: str, user: UserPublic) -> TeamMember:
        """Verify user is an active member of the team. Raises ValueError if not."""
        members = [m for m in (await _safe_list_members(self, team_id)) if m.status == "active"]
        my_member = next((m for m in members if m.user_id == user.id), None)
        if my_member is None:
            raise ValueError("NOT_TEAM_MEMBER")
        return my_member

    async def list_team_messages(self, team_id: str, user: UserPublic) -> list[Any]:
        await self._ensure_team_member(team_id, user)
        msgs = await self._messages.list_by_team(team_id)
        return [{"id": m.id, "team_id": m.team_id, "sender_id": m.sender_id, "sender_name": m.sender_name, "content": m.content, "message_type": m.message_type, "created_at": str(m.created_at)} for m in msgs]

    async def create_team_message(self, team_id: str, payload: Any, user: UserPublic) -> Any:
        await self._ensure_team_member(team_id, user)
        import secrets as _s
        mid = f"msg-{_s.token_hex(4)}"
        msg = TeamMessage(id=mid, team_id=team_id, sender_id=user.id, sender_name=user.display_name, content=getattr(
            payload, "content", ""), message_type=getattr(payload, "message_type", "text"))
        await self._messages.create(msg)
        await self._s.commit()
        result = {"id": mid, "team_id": team_id, "content": msg.content, "sender_name": msg.sender_name,
                  "sender_id": msg.sender_id, "message_type": msg.message_type, "created_at": str(msg.created_at)}
        # Broadcast to all team members via WebSocket (fire-and-forget)
        try:
            from app.services.websocket_manager import ws_manager
            import asyncio as _aio
            _aio.ensure_future(ws_manager.broadcast(
                f"team-{team_id}", "team_message", result))
        except Exception:
            pass  # Non-fatal: message is persisted even if broadcast fails
        return result

    async def create_team_invite(self, team_id: str, payload: Any, user: UserPublic) -> Any:
        await self._ensure_team_member(team_id, user)
        import secrets as _s
        from datetime import UTC, datetime, timedelta
        now = datetime.now(UTC)
        inv = TeamInvite(id=f"inv-{_s.token_hex(4)}", team_id=team_id,
                         email=getattr(payload, "email", "invite@whucs.local"),
                         role=getattr(payload, "role", "member"),
                         token=_s.token_hex(16), status="pending",
                         created_at=now, expires_at=now + timedelta(days=7))
        await self._invites.create(inv)
        await self._s.commit()
        return {"id": inv.id, "team_id": team_id, "email": inv.email, "role": inv.role,
                "status": inv.status, "token": inv.token,
                "created_at": inv.created_at, "expires_at": inv.expires_at}

    async def _ensure_team_admin(self, team_id: str, user: UserPublic) -> TeamMember:
        """Verify user is an admin/owner of the team."""
        member = await self._ensure_team_member(team_id, user)
        if member.role not in ("owner", "admin"):
            raise ValueError("TEAM_ADMIN_REQUIRED")
        return member

    async def join_team(self, team_id: str, payload: Any, user: UserPublic) -> Any:
        invite_token = getattr(payload, "invite_token", None)
        invite = await self._invites.get_by_token(invite_token) if invite_token else None
        if not invite or invite.team_id != team_id or invite.status != "pending":
            raise WorkspaceError(404, "TEAM_INVITE_NOT_FOUND", "邀请不存在或已失效", {"team_id": team_id})
        if invite.email != user.email:
            raise WorkspaceError(403, "TEAM_INVITE_EMAIL_MISMATCH", "当前账号与邀请邮箱不一致", {"team_id": team_id})
        now = datetime.now(UTC)
        expires_at = invite.expires_at.replace(tzinfo=UTC) if invite.expires_at and invite.expires_at.tzinfo is None else invite.expires_at
        if expires_at and expires_at < now:
            invite.status = "expired"
            await self._s.commit()
            raise WorkspaceError(410, "TEAM_INVITE_EXPIRED", "邀请已过期", {"team_id": team_id})
        # Check user isn't already a member
        try:
            await self._ensure_team_member(team_id, user)
            raise ValueError("ALREADY_TEAM_MEMBER")
        except ValueError as e:
            if "NOT_TEAM_MEMBER" not in str(e):
                raise
        import secrets as _s
        mid = f"mem-{_s.token_hex(4)}"
        m = TeamMember(id=mid, team_id=team_id, user_id=user.id, role=invite.role)
        invite.status = "accepted"
        await self._members.create(m)
        await self._s.commit()
        return {"id": mid, "team_id": team_id, "user_id": user.id,
                "username": user.username, "email": user.email,
                "display_name": user.display_name, "role": invite.role,
                "status": "active", "joined_at": now.isoformat()}

    async def update_team_member(self, team_id: str, member_id: str, payload: Any, user: UserPublic) -> Any:
        await self._ensure_team_admin(team_id, user)
        m = await self._members.get_by_id(member_id)
        if m and m.team_id == team_id:
            m.role = getattr(payload, "role", m.role)
            await self._members.update(m)
            await self._s.commit()
            return {"id": member_id, "role": m.role}
        return {"id": member_id, "role": "member"}

    async def remove_team_member(self, team_id: str, member_id: str, user: UserPublic) -> None:
        await self._ensure_team_admin(team_id, user)
        m = await self._members.get_by_id(member_id)
        if m and m.team_id == team_id:
            m.status = "removed"
            await self._members.update(m)
            await self._s.commit()

    async def update_team(self, team_id: str, payload: Any, user: UserPublic) -> TeamDetail:
        await self._ensure_team_admin(team_id, user)
        team = await self._teams.get_by_id(team_id)
        if not team:
            raise ValueError("TEAM_NOT_FOUND")
        if name := getattr(payload, "name", None):
            team.name = name
        if description := getattr(payload, "description", None):
            team.description = description
        await self._teams.update(team)
        await self._s.commit()
        members = [m for m in (await _safe_list_members(self, team_id)) if m.status == "active"]
        return TeamDetail(id=team.id, name=team.name, description=team.description or "",
                          role="owner", member_count=len(members), unread_count=0,
                          root_folder=FolderItem(id=f"folder-team-{team.id}", name=team.name,
                                                  parent_id=None, scope="team", permission="管理", children=[]),
                          members=[], invites=[])

    async def delete_team(self, team_id: str, user: UserPublic) -> None:
        await self._ensure_team_admin(team_id, user)
        t = await self._teams.get_by_id(team_id)
        if t:
            await self._teams.delete(t)
            await self._s.commit()
        members = await self._members.list_by_team(team_id)
        for m in members:
            if m.user_id == user.id and m.role != "owner":
                m.status = "left"
                await self._members.update(m)
                await self._s.commit()
                break

    # ── Knowledge bases ──
    def _decode_kb_tags(self, tags_raw: str | None) -> list[str]:
        if not tags_raw:
            return []
        try:
            value = json.loads(tags_raw)
        except json.JSONDecodeError:
            return [tag.strip() for tag in tags_raw.split(",") if tag.strip()]
        return [str(tag) for tag in value if str(tag).strip()] if isinstance(value, list) else []

    def _encode_kb_tags(self, tags: list[str] | None) -> str:
        cleaned = [str(tag).strip() for tag in (tags or []) if str(tag).strip()]
        return json.dumps(cleaned, ensure_ascii=False)

    async def _user_can_access_team(self, team_id: str | None, user: UserPublic) -> bool:
        if not team_id:
            return False
        members = await self._members.list_by_team(team_id)
        return any(member.user_id == user.id and member.status == "active" for member in members)

    async def _team_member_role(self, team_id: str | None, user: UserPublic) -> str | None:
        member = await self._team_member_for_user(team_id, user)
        return member.role if member else None

    async def _ensure_kb_access(self, kb_id: str, user: UserPublic, *, manage: bool = False) -> KnowledgeBase:
        kb = await self._kbs.get_by_id(kb_id)
        if not kb or kb.status == "deleted":
            raise WorkspaceError(404, "KB_NOT_FOUND", "知识库不存在", {"kb_id": kb_id})
        if kb.scope_type == "team":
            role = await self._team_member_role(kb.scope_id, user)
            if role is None:
                raise WorkspaceError(403, "KB_SCOPE_DENIED", "无权访问该团队知识库", {"kb_id": kb_id})
            if manage and role == "guest":
                raise WorkspaceError(403, "KB_MANAGE_FORBIDDEN", "访客只能查看团队知识库", {"kb_id": kb_id})
            return kb
        if kb.owner_id != user.id:
            raise WorkspaceError(403, "KB_SCOPE_DENIED", "无权访问该个人知识库", {"kb_id": kb_id})
        return kb

    async def _ensure_file_matches_kb_scope(self, kb: KnowledgeBase, file: File) -> None:
        folder = await self._folders.get_by_id(file.folder_id)
        if kb.scope_type == "team":
            if not folder or folder.scope != "team" or folder.team_id != kb.scope_id:
                raise WorkspaceError(
                    400,
                    "KB_FILE_SCOPE_MISMATCH",
                    "团队知识库只能添加该团队空间下的文件",
                    {"kb_id": kb.id, "file_id": file.id, "scope_id": kb.scope_id},
                )
            return
        if folder and folder.scope == "team":
            raise WorkspaceError(
                400,
                "KB_FILE_SCOPE_MISMATCH",
                "个人知识库只能添加个人空间下的文件",
                {"kb_id": kb.id, "file_id": file.id, "team_id": folder.team_id},
            )

    async def _knowledge_document_public(self, doc: KnowledgeDocument) -> KnowledgeDocumentPublic:
        chunks = await self._chunks.list_by_document(doc.id)
        return KnowledgeDocumentPublic(
            id=doc.id,
            kb_id=doc.kb_id,
            file_id=doc.file_id,
            file_name=doc.file_name,
            index_status=doc.index_status,
            chunk_count=len(chunks),
            error_message=doc.error_message or None,
            summary=doc.summary or None,
            char_count=doc.char_count or 0,
            token_count=doc.token_count or 0,
            updated_at=doc.updated_at,
        )

    async def _knowledge_base_public(self, kb: KnowledgeBase) -> KnowledgeBasePublic:
        docs = await self._docs.list_by_kb(kb.id)
        chunk_count = 0
        for doc in docs:
            chunk_count += len(await self._chunks.list_by_document(doc.id))
        return KnowledgeBasePublic(
            id=kb.id,
            name=kb.name,
            description=kb.description or "",
            scope_type=kb.scope_type,
            scope_id=kb.scope_id,
            category=kb.category or None,
            tags=self._decode_kb_tags(kb.tags),
            freshness_policy=kb.freshness_policy,
            status=kb.status,
            document_count=len(docs),
            chunk_count=chunk_count,
            last_indexed_at=kb.last_indexed_at,
            updated_at=kb.updated_at,
        )

    async def _knowledge_conversation_public(self, conversation: KnowledgeConversation) -> KnowledgeConversationPublic:
        messages = await self._knowledge_messages.list_by_conversation(conversation.id)
        return KnowledgeConversationPublic(
            id=conversation.id,
            kb_id=conversation.kb_id,
            title=conversation.title,
            message_count=len(messages),
            updated_at=conversation.updated_at,
        )

    async def _knowledge_message_public(self, message: KnowledgeMessage) -> KnowledgeMessagePublic:
        snapshots = await self._knowledge_citations.list_by_message(message.id)
        citations = [
            Citation(
                file_id=snapshot.file_id,
                document_id=snapshot.document_id,
                chunk_id=snapshot.chunk_id,
                title=snapshot.title,
                page_no=snapshot.page_no,
                paragraph_no=snapshot.paragraph_no,
                snippet=snapshot.snippet,
            )
            for snapshot in snapshots
        ]
        return KnowledgeMessagePublic(
            id=message.id,
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            citations=citations,
            created_at=message.created_at,
        )

    async def _ensure_knowledge_conversation(
        self,
        conversation_id: str,
        kb_id: str,
        user: UserPublic,
    ) -> KnowledgeConversation:
        conversation = await self._knowledge_conversations.get_by_id(conversation_id)
        if not conversation or conversation.kb_id != kb_id:
            raise WorkspaceError(
                404,
                "CONVERSATION_NOT_FOUND",
                "对话不存在",
                {"conversation_id": conversation_id, "kb_id": kb_id},
            )
        await self._ensure_kb_access(conversation.kb_id, user)
        return conversation

    async def list_knowledge_bases(self, user: UserPublic) -> list[KnowledgeBasePublic]:
        kbs = await self._kbs.list_all()
        visible: list[KnowledgeBasePublic] = []
        for kb in kbs:
            if kb.scope_type == "team":
                if await self._user_can_access_team(kb.scope_id, user):
                    visible.append(await self._knowledge_base_public(kb))
            elif kb.owner_id == user.id:
                visible.append(await self._knowledge_base_public(kb))
        return visible

    async def create_knowledge_base(self, payload: Any, user: UserPublic) -> KnowledgeBasePublic:
        import secrets as _s
        kid = f"kb-{_s.token_hex(4)}"
        scope_type = getattr(payload, "scope_type", "personal") or "personal"
        scope_id = getattr(payload, "scope_id", None)
        if scope_type == "team" and not await self._user_can_access_team(scope_id, user):
            raise WorkspaceError(403, "KB_SCOPE_DENIED", "无权在该团队空间创建知识库", {"scope_id": scope_id})
        kb = KnowledgeBase(id=kid, name=(getattr(payload, "name", None) or "新知识库"),
                           description=(getattr(payload, "description", None) or ""), owner_id=user.id,
                           scope_type=scope_type, scope_id=scope_id if scope_type == "team" else None,
                           category=(getattr(payload, "category", None) or ""),
                           tags=self._encode_kb_tags(getattr(payload, "tags", None)),
                           freshness_policy=(getattr(payload, "freshness_policy", None) or "manual"))
        await self._kbs.create(kb)
        await self._s.commit()
        return await self._knowledge_base_public(kb)

    async def update_knowledge_base(self, kb_id: str, payload: Any, user: UserPublic) -> KnowledgeBasePublic:
        kb = await self._ensure_kb_access(kb_id, user, manage=True)
        if (getattr(payload, "name", None)):
            kb.name = getattr(payload, "name", None)
        if getattr(payload, "description", None) is not None:
            kb.description = getattr(payload, "description", None)
        if getattr(payload, "status", None) is not None:
            kb.status = getattr(payload, "status", None)
        if getattr(payload, "category", None) is not None:
            kb.category = getattr(payload, "category", None) or ""
        if getattr(payload, "tags", None) is not None:
            kb.tags = self._encode_kb_tags(getattr(payload, "tags", None))
        if getattr(payload, "freshness_policy", None) is not None:
            kb.freshness_policy = getattr(payload, "freshness_policy", None)
        await self._kbs.update(kb)
        await self._s.commit()
        return await self._knowledge_base_public(kb)

    async def delete_knowledge_base(self, kb_id: str, user: UserPublic) -> None:
        kb = await self._ensure_kb_access(kb_id, user, manage=True)
        kb.status = "deleted"
        await self._kbs.update(kb)
        self._faiss.pop(kb_id, None)
        await self._s.commit()

    async def list_knowledge_documents(self, kb_id: str, user: UserPublic) -> list[KnowledgeDocumentPublic]:
        await self._ensure_kb_access(kb_id, user)
        docs = await self._docs.list_by_kb(kb_id)
        return [await self._knowledge_document_public(d) for d in docs]

    async def list_knowledge_document_profiles(self, kb_id: str, user: UserPublic) -> list[dict[str, Any]]:
        await self._ensure_kb_access(kb_id, user)
        docs = await self._docs.list_by_kb(kb_id)
        profiles: list[dict[str, Any]] = []
        for doc in docs:
            profiles.append({
                "id": doc.id,
                "file_id": doc.file_id,
                "file_name": doc.file_name,
                "index_status": doc.index_status,
                "summary": doc.summary or "",
                "keywords": _json_loads_list(doc.keywords),
                "outline": _json_loads_list(doc.outline),
                "content_preview": (doc.content_text or "")[:5000],
                "char_count": doc.char_count or 0,
                "token_count": doc.token_count or 0,
            })
        return profiles

    async def add_knowledge_document(self, kb_id: str, payload: Any, user: UserPublic) -> KnowledgeDocumentPublic:
        import secrets as _s
        kb = await self._ensure_kb_access(kb_id, user, manage=True)
        fid = getattr(payload, "file_id", "")
        f = await self._files.get_by_id(fid)
        if not f:
            raise WorkspaceError(404, "FILE_NOT_FOUND", "文件不存在或无权访问", {"file_id": fid})
        await self._ensure_can_read_file(f, user)
        await self._ensure_file_matches_kb_scope(kb, f)
        content = _read_file_content(f) or b""
        did = f"doc-{_s.token_hex(4)}"
        # Parse, clean, and chunk — paragraph-aware for coherent retrieval
        try:
            parsed = parse_document(f.name, content, f.type)
            from app.services.parser import clean_text, chunk_paragraphs
            cleaned = clean_text(parsed.text)
            text_chunks = chunk_paragraphs(cleaned, target_size=600)
            chunks = [KnowledgeChunk(
                id=f"{did}-chunk-{i+1}", document_id=did,
                content=f"[{f.name}]\n{tc}",
                page_no=1, paragraph_no=i+1,
            ) for i, tc in enumerate(text_chunks)]
            index_status = "indexed"
            error_message = ""
        except Exception as exc:
            cleaned = ""
            chunks = []
            index_status = "failed"
            error_message = str(exc)
        d = KnowledgeDocument(id=did, kb_id=kb_id,
                              file_id=fid, file_name=f.name, version_sha=f.sha256,
                              index_status=index_status,
                              error_message=error_message,
                              content_text=cleaned,
                              summary=_summarize_document_text(cleaned),
                              keywords=json.dumps(_extract_document_keywords(cleaned, f.name), ensure_ascii=False),
                              outline=json.dumps(_extract_document_outline(cleaned), ensure_ascii=False),
                              char_count=len(cleaned),
                              token_count=_estimate_document_tokens(cleaned))
        await self._docs.create(d)
        if chunks:
            await self._chunks.create_bulk(chunks)
        # Update file parse status
        f.parse_status = index_status
        f.knowledge_base_ids = (f.knowledge_base_ids +
                                "," + kb_id) if f.knowledge_base_ids else kb_id
        await self._files.update(f)
        kb.last_indexed_at = datetime.now(UTC)
        await self._kbs.update(kb)
        # Clear FAISS cache for this KB
        self._faiss.pop(kb_id, None)
        await self._s.commit()
        return await self._knowledge_document_public(d)

    async def create_markdown_knowledge_document(
        self,
        kb_id: str,
        filename: str,
        markdown: str,
        tags: list[str],
        user: UserPublic,
    ) -> KnowledgeDocumentPublic:
        kb = await self._ensure_kb_access(kb_id, user, manage=True)
        folder_id = await self._knowledge_document_target_folder(kb, user)
        content = markdown.encode("utf-8")
        digest = hashlib.sha256(content).hexdigest()
        fid = f"file-{digest[:12]}"
        if await self._files.get_by_id(fid):
            fid = f"file-{digest[:8]}-{secrets.token_hex(4)}"
        folder = await self._resolve_upload_folder(folder_id, user)
        file = File(
            id=fid,
            name=filename,
            folder_id=folder.id,
            type=_file_type(filename),
            size=len(content),
            sha256=digest,
            content_type="text/markdown",
            owner_id=user.id,
            team_id=folder.team_id if folder.scope == "team" else None,
            permission_scope="团队" if folder.scope == "team" else "个人",
            tags=",".join(tags),
            created_by=user.username,
        )
        _store_file_content(fid, digest, content)
        await self._files.create(file)
        await self._append_file_version(file, content, user)
        await self._s.commit()
        return await self.add_knowledge_document(kb_id, type("_Payload", (), {"file_id": fid})(), user)

    async def _knowledge_document_target_folder(self, kb: KnowledgeBase, user: UserPublic) -> str:
        if kb.scope_type != "team":
            return await self._ensure_personal_root(user)
        if not kb.scope_id:
            raise WorkspaceError(400, "KB_SCOPE_MISSING", "团队知识库缺少团队范围", {"kb_id": kb.id})
        root_id = f"folder-team-{kb.scope_id}"
        if not await self._folders.get_by_id(root_id):
            await self._folders.create(Folder(
                id=root_id,
                name="团队空间",
                scope="team",
                team_id=kb.scope_id,
            ))
            await self._s.commit()
        return root_id

    async def remove_knowledge_document(self, kb_id: str, doc_id: str, user: UserPublic) -> None:
        """Remove a document from a knowledge base."""
        await self._ensure_kb_access(kb_id, user, manage=True)
        doc = await self._docs.get_by_id(doc_id)
        if doc and doc.kb_id == kb_id:
            await self._chunks.delete_by_document(doc.id)
            await self._docs.delete(doc)
            # Remove KB ID from file
            f = await self._files.get_by_id(doc.file_id)
            if f and f.knowledge_base_ids:
                kb_ids = [k.strip() for k in f.knowledge_base_ids.split(",") if k.strip() and k.strip() != kb_id]
                f.knowledge_base_ids = ",".join(kb_ids)
                await self._files.update(f)
            # Clear FAISS cache
            self._faiss.pop(kb_id, None)
            await self._s.commit()

    async def batch_add_knowledge_files(self, kb_id: str, payload: Any, user: UserPublic) -> dict[str, Any]:
        await self._ensure_kb_access(kb_id, user, manage=True)
        added: list[KnowledgeDocumentPublic] = []
        skipped: list[dict[str, str]] = []
        existing_docs = await self._docs.list_by_kb(kb_id)
        existing_file_ids = {doc.file_id for doc in existing_docs}

        for file_id in getattr(payload, "file_ids", []):
            if file_id in existing_file_ids:
                skipped.append({"file_id": file_id, "code": "FILE_ALREADY_IN_KB"})
                continue
            try:
                document = await self.add_knowledge_document(kb_id, type("_Payload", (), {"file_id": file_id})(), user)
            except WorkspaceError as exc:
                skipped.append({"file_id": file_id, "code": exc.code})
                continue
            added.append(document)
            existing_file_ids.add(file_id)

        return {"added": added, "removed": [], "skipped": skipped}

    async def batch_remove_knowledge_files(self, kb_id: str, payload: Any, user: UserPublic) -> dict[str, Any]:
        await self._ensure_kb_access(kb_id, user, manage=True)
        removed: list[str] = []
        skipped: list[dict[str, str]] = []
        docs = await self._docs.list_by_kb(kb_id)
        docs_by_file_id = {doc.file_id: doc for doc in docs}

        for file_id in getattr(payload, "file_ids", []):
            doc = docs_by_file_id.get(file_id)
            if not doc:
                skipped.append({"file_id": file_id, "code": "FILE_NOT_IN_KB"})
                continue
            await self._chunks.delete_by_document(doc.id)
            await self._docs.delete(doc)
            f = await self._files.get_by_id(doc.file_id)
            if f and f.knowledge_base_ids:
                kb_ids = [k.strip() for k in f.knowledge_base_ids.split(",") if k.strip() and k.strip() != kb_id]
                f.knowledge_base_ids = ",".join(kb_ids)
                await self._files.update(f)
            removed.append(file_id)

        self._faiss.pop(kb_id, None)
        await self._s.commit()
        return {"added": [], "removed": removed, "skipped": skipped}

    async def reindex_knowledge_base(self, kb_id: str, user: UserPublic) -> dict[str, Any]:
        kb = await self._ensure_kb_access(kb_id, user, manage=True)
        kb.last_indexed_at = datetime.now(UTC)
        await self._kbs.update(kb)
        self._faiss.pop(kb_id, None)
        await self._s.commit()
        return {"kb_id": kb_id, "status": "queued"}

    async def list_knowledge_conversations(
        self,
        kb_id: str,
        user: UserPublic,
    ) -> KnowledgeConversationListResponse:
        await self._ensure_kb_access(kb_id, user)
        conversations = await self._knowledge_conversations.list_by_kb(kb_id)
        return KnowledgeConversationListResponse(
            items=[await self._knowledge_conversation_public(conversation) for conversation in conversations]
        )

    async def get_knowledge_conversation(
        self,
        conversation_id: str,
        user: UserPublic,
    ) -> KnowledgeConversationDetailResponse:
        conversation = await self._knowledge_conversations.get_by_id(conversation_id)
        if not conversation:
            raise WorkspaceError(
                404,
                "CONVERSATION_NOT_FOUND",
                "对话不存在",
                {"conversation_id": conversation_id},
            )
        await self._ensure_kb_access(conversation.kb_id, user)
        messages = await self._knowledge_messages.list_by_conversation(conversation.id)
        return KnowledgeConversationDetailResponse(
            conversation=await self._knowledge_conversation_public(conversation),
            messages=[await self._knowledge_message_public(message) for message in messages],
        )

    async def delete_knowledge_conversation(self, conversation_id: str, user: UserPublic) -> None:
        conversation = await self._knowledge_conversations.get_by_id(conversation_id)
        if not conversation:
            raise WorkspaceError(
                404,
                "CONVERSATION_NOT_FOUND",
                "对话不存在",
                {"conversation_id": conversation_id},
            )
        await self._ensure_kb_access(conversation.kb_id, user)
        messages = await self._knowledge_messages.list_by_conversation(conversation.id)
        await self._knowledge_citations.delete_by_message_ids([message.id for message in messages])
        await self._knowledge_messages.delete_by_conversation(conversation.id)
        await self._knowledge_conversations.delete(conversation)
        await self._s.commit()

    async def answer_question(self, payload: QARequest, user: UserPublic) -> QAResponse:
        import secrets as _s
        await self._ensure_kb_access(payload.kb_id, user)
        conv_id = getattr(payload, "conversation_id", None)
        now = datetime.now(UTC)
        if conv_id:
            conversation = await self._ensure_knowledge_conversation(conv_id, payload.kb_id, user)
        else:
            conv_id = f"conv-{_s.token_hex(4)}"
            conversation = KnowledgeConversation(
                id=conv_id,
                kb_id=payload.kb_id,
                owner_id=user.id,
                title=payload.question[:120],
                created_at=now,
                updated_at=now,
            )
            await self._knowledge_conversations.create(conversation)
        report_mode = getattr(payload, "report_mode", False)
        kb = await self._kbs.get_by_id(payload.kb_id)
        kb_name = kb.name if kb else "知识库"
        error_code = await self._knowledge_query_error_code(payload.kb_id)
        rag_context = None if error_code else await self._build_rag_context(payload.kb_id, payload.question, payload.top_k)
        citations = [] if rag_context is None else rag_context.citations
        snippets = [] if rag_context is None else rag_context.snippets
        if not error_code and not snippets:
            error_code = "KB_NO_MATCH"

        history_context = ""
        past_msgs = await self._knowledge_messages.list_by_conversation(conv_id)
        if past_msgs:
            recent = past_msgs[-6:]
            history_parts = []
            for message in recent:
                role_label = "用户" if message.role == "user" else "助手"
                history_parts.append(f"【{role_label}】{message.content}")
            history_context = "\n".join(history_parts)

        if error_code:
            answer = self._knowledge_error_answer(error_code, kb_name)
        else:
            answer = await self._generate_answer(
                payload.question, snippets, kb_name,
                history_context=history_context, report_mode=report_mode,
            )
        previous_user_messages = [message for message in past_msgs if message.role == "user"]
        question_lower = payload.question.lower()
        asks_previous_question = (
            "previous question" in question_lower
            or "上一" in payload.question
            or "之前" in payload.question
            or "刚才" in payload.question
        )
        if asks_previous_question and previous_user_messages:
            previous_question = previous_user_messages[-1].content
            if previous_question not in answer:
                answer = f"上一轮问题是：{previous_question}\n\n{answer}"
        user_msg_id = f"msg-{_s.token_hex(4)}"
        assistant_msg_id = f"msg-{_s.token_hex(4)}"
        await self._knowledge_messages.create(
            KnowledgeMessage(
                id=user_msg_id,
                conversation_id=conv_id,
                role="user",
                content=payload.question,
                created_at=now,
            )
        )
        await self._knowledge_messages.create(
            KnowledgeMessage(
                id=assistant_msg_id,
                conversation_id=conv_id,
                role="assistant",
                content=answer,
                created_at=datetime.now(UTC),
            )
        )
        snapshots = [
            KnowledgeCitationSnapshot(
                id=f"cite-{_s.token_hex(4)}",
                message_id=assistant_msg_id,
                ordinal=index,
                file_id=citation.file_id,
                document_id=citation.document_id,
                chunk_id=citation.chunk_id,
                title=citation.title,
                page_no=citation.page_no,
                paragraph_no=citation.paragraph_no,
                snippet=citation.snippet,
            )
            for index, citation in enumerate(citations)
        ]
        if snapshots:
            await self._knowledge_citations.create_bulk(snapshots)
        conversation.updated_at = datetime.now(UTC)
        await self._knowledge_conversations.update(conversation)
        await self._s.commit()
        return QAResponse(
            conversation_id=conv_id,
            message_id=assistant_msg_id,
            answer=answer,
            citations=citations,
            error_code=error_code,
        )

    async def answer_question_stream(self, payload: QARequest, user: UserPublic):
        """Stream RAG answer via SSE async generator."""
        import secrets as _s
        import json as _json
        await self._ensure_kb_access(payload.kb_id, user)
        conv_id = getattr(payload, "conversation_id", None)
        now = datetime.now(UTC)
        if conv_id:
            conversation = await self._ensure_knowledge_conversation(conv_id, payload.kb_id, user)
        else:
            conv_id = f"conv-{_s.token_hex(4)}"
            conversation = KnowledgeConversation(
                id=conv_id, kb_id=payload.kb_id, owner_id=user.id,
                title=payload.question[:120], created_at=now, updated_at=now,
            )
            await self._knowledge_conversations.create(conversation)
        report_mode = getattr(payload, "report_mode", False)
        kb = await self._kbs.get_by_id(payload.kb_id)
        kb_name = kb.name if kb else "知识库"
        error_code = await self._knowledge_query_error_code(payload.kb_id)
        rag_context = None if error_code else await self._build_rag_context(payload.kb_id, payload.question, payload.top_k)
        citations = [] if rag_context is None else rag_context.citations
        snippets = [] if rag_context is None else rag_context.snippets
        if not error_code and not snippets:
            error_code = "KB_NO_MATCH"

        # Build history context
        history_context = ""
        past_msgs = await self._knowledge_messages.list_by_conversation(conv_id)
        if past_msgs:
            recent = past_msgs[-6:]
            history_parts = []
            for message in recent:
                role_label = "用户" if message.role == "user" else "助手"
                history_parts.append(f"【{role_label}】{message.content}")
            history_context = "\n".join(history_parts)

        # Create user message immediately
        user_msg_id = f"msg-{_s.token_hex(4)}"
        await self._knowledge_messages.create(
            KnowledgeMessage(id=user_msg_id, conversation_id=conv_id,
                             role="user", content=payload.question, created_at=now))

        # Send citations to client
        citation_data = [
            {
                "file_id": c.file_id,
                "document_id": c.document_id,
                "chunk_id": c.chunk_id,
                "title": c.title,
                "page_no": c.page_no,
                "paragraph_no": c.paragraph_no,
                "snippet": c.snippet[:800],
            }
            for c in (citations or [])
        ]
        yield f"data: {_json.dumps({'type': 'citations', 'citations': citation_data}, ensure_ascii=False)}\n\n"

        # Stream answer
        full_answer = ""
        assistant_msg_id = f"msg-{_s.token_hex(4)}"
        try:
            if error_code:
                full_answer = self._knowledge_error_answer(error_code, kb_name)
                yield f"data: {_json.dumps({'type': 'token', 'content': full_answer}, ensure_ascii=False)}\n\n"
            else:
                from app.services.llm import generate_rag_answer_stream
                async for chunk_text in self._stream_llm(
                    payload.question, snippets, kb_name,
                    history_context=history_context, report_mode=report_mode,
                ):
                    full_answer += chunk_text
                    yield f"data: {_json.dumps({'type': 'token', 'content': chunk_text}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.warning("Stream failed: %s", e)
            if not full_answer:
                full_answer = f"回答生成失败: {e}"
            yield f"data: {_json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

        # Persist assistant message + citation snapshots
        await self._knowledge_messages.create(
            KnowledgeMessage(id=assistant_msg_id, conversation_id=conv_id,
                             role="assistant", content=full_answer, created_at=datetime.now(UTC)))
        citation_snapshots = [
            KnowledgeCitationSnapshot(
                id=f"cite-{_s.token_hex(4)}", message_id=assistant_msg_id,
                ordinal=index, file_id=c.file_id, document_id=c.document_id,
                chunk_id=c.chunk_id, title=c.title,
                page_no=c.page_no, paragraph_no=c.paragraph_no, snippet=c.snippet,
            )
            for index, c in enumerate(citations or [])
        ]
        if citation_snapshots:
            await self._knowledge_citations.create_bulk(citation_snapshots)
        conversation.updated_at = datetime.now(UTC)
        await self._knowledge_conversations.update(conversation)
        await self._s.commit()
        yield f"data: {_json.dumps({'type': 'done', 'conversation_id': conv_id, 'message_id': assistant_msg_id}, ensure_ascii=False)}\n\n"

    async def _stream_llm(self, question: str, snippets: list[str], kb_name: str,
                          history_context: str = "", report_mode: bool = False):
        """Bridge sync LLM stream generator into async for SSE via thread + queue."""
        from app.services.llm import generate_rag_answer_stream
        import asyncio

        queue: asyncio.Queue[str | None] = asyncio.Queue()

        def _run() -> None:
            try:
                for chunk in generate_rag_answer_stream(
                    question,
                    snippets,
                    kb_name,
                    history_context=history_context,
                    report_mode=report_mode,
                ):
                    queue.put_nowait(chunk)
            except Exception:
                pass
            finally:
                queue.put_nowait(None)  # sentinel

        loop = asyncio.get_running_loop()
        loop.run_in_executor(None, _run)

        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            yield chunk

    async def _knowledge_query_error_code(self, kb_id: str) -> str | None:
        docs = await self._docs.list_by_kb(kb_id)
        if not docs:
            return "KB_EMPTY"
        for doc in docs:
            chunks = await self._chunks.list_by_document(doc.id)
            if chunks:
                return None
        return "KB_FILE_NOT_INDEXED"

    def _knowledge_error_answer(self, error_code: str, kb_name: str) -> str:
        if error_code == "KB_EMPTY":
            return f"知识库「{kb_name}」中还没有文件。请先选择已解析文件批量加入知识库，再重新提问。"
        if error_code == "KB_FILE_NOT_INDEXED":
            return f"知识库「{kb_name}」中的文件尚未完成索引。请等待解析完成或手动重建索引后再提问。"
        return f"知识库「{kb_name}」中未找到与问题相关的内容。请尝试更具体的关键词，或补充相关文件后重试。"

    async def _retrieve_citations(self, kb_id: str, question: str, top_k: int) -> list:
        return await self._rag_pipeline.retrieve(kb_id, question, top_k)

    async def _build_rag_context(self, kb_id: str, question: str, top_k: int):
        return await self._rag_pipeline.build_context(kb_id, question, top_k)

    async def _generate_answer(self, question: str, snippets: list, kb_name: str, history_context: str = "", report_mode: bool = False) -> str:
        return await self._rag_pipeline.answer(
            question,
            snippets,
            kb_name,
            history_context=history_context,
            report_mode=report_mode,
        )

    async def list_tools(self) -> list[ToolDefinition]:
        return self._tool_registry.definitions()

    async def record_agent_tool_execution(self, user: UserPublic, tool_name: str, execution: Any) -> None:
        status = str(getattr(execution, "status", "unknown"))
        latency_ms = int(getattr(execution, "latency_ms", 0) or 0)
        error = str(getattr(execution, "error_message", "") or "")
        resource_name = json.dumps(
            {
                "tool": tool_name,
                "status": status,
                "latency_ms": latency_ms,
                "error": error[:160],
            },
            ensure_ascii=False,
        )[:256]
        await self._audit.create(AuditLog(
            actor=user.username,
            action=f"agent.tool.{status}",
            resource_type="agent_tool",
            resource_name=resource_name,
        ))

    def read_file_content_for_tool(self, file: File) -> bytes | None:
        return _read_file_content(file)

    def _workflow_tool_params(self, tool_name: str, node: dict[str, Any], payload: Any) -> dict[str, Any]:
        params = dict(node.get("parameters") or {})
        file_id = payload.get("file_id") if isinstance(payload, dict) else getattr(payload, "file_id", None)
        if tool_name == "file_content_search":
            params.setdefault("query", "")
            if file_id and not params.get("file_ids"):
                params["file_ids"] = [file_id]
        elif tool_name == "python_data" and file_id:
            params.setdefault("file_id", file_id)
        elif tool_name == "calculator":
            params.setdefault("expression", "1 + 1")
        elif tool_name == "course_lookup":
            params.setdefault("query", "算法")
        return params

    async def _execute_workflow_node(
        self,
        node: dict[str, Any],
        edges: list[dict[str, Any]],
        node_outputs: dict[str, dict[str, Any]],
        workflow_inputs: dict[str, Any],
        user: UserPublic,
    ) -> dict[str, Any]:
        """Execute one node for both formal runs and step debugging."""
        node_id = str(node.get("id", ""))
        node_type = str(node.get("type", "tool"))
        tool_name = str(node.get("tool_name") or "")
        resolved_parameters = self._workflow_resolve_parameters(node, node_outputs, workflow_inputs)
        status = "success"
        if tool_name:
            resolved_node = dict(node)
            resolved_node["parameters"] = resolved_parameters
            input_value = self._workflow_tool_params(tool_name, resolved_node, workflow_inputs)
            execution = await self._tool_registry.execute(tool_name, input_value, self, user)
            status = "success" if execution.status == "success" else "failed"
            output = execution.output if status == "success" else {
                "error": execution.error_message or execution.clarification or "工具执行失败",
            }
        elif node_type in {"input", "trigger"}:
            input_value = workflow_inputs
            output = {**workflow_inputs, **resolved_parameters}
        elif node_type == "condition":
            input_value = resolved_parameters
            left = resolved_parameters.get("left")
            right = resolved_parameters.get("right")
            operator = str(resolved_parameters.get("operator") or "truthy")
            matched = self._workflow_compare(left, operator, right)
            output = {"matched": matched, "branch": "true" if matched else "false", "value": left}
        elif node_type == "transform":
            input_value = resolved_parameters
            output = self._workflow_transform(resolved_parameters)
        elif node_type == "loop":
            input_value = resolved_parameters
            output = self._workflow_loop(resolved_parameters)
        elif node_type == "aggregate":
            input_value = resolved_parameters
            output = self._workflow_aggregate(resolved_parameters)
        elif node_type == "output":
            input_value = resolved_parameters
            output = resolved_parameters
            if not output:
                incoming = [edge.get("source") for edge in edges if edge.get("target") == node_id]
                if incoming:
                    output = dict(node_outputs.get(str(incoming[-1]), {}).get("output") or {})
        else:
            input_value = resolved_parameters
            output = resolved_parameters
        record = {"input": input_value, "output": output, "status": status}
        node_outputs[node_id] = record
        return {
            "node_id": node_id,
            "name": node.get("name", ""),
            "tool_name": tool_name,
            **record,
        }

    def _workflow_skipped_node(self, node: dict[str, Any]) -> dict[str, Any]:
        return {
            "node_id": str(node.get("id") or ""),
            "name": str(node.get("name") or ""),
            "tool_name": str(node.get("tool_name") or ""),
            "status": "skipped",
            "input": {},
            "output": {},
        }

    def _workflow_compare(self, left: Any, operator: str, right: Any) -> bool:
        if operator == "truthy":
            return bool(left)
        if operator == "falsy":
            return not bool(left)
        if operator == "eq":
            return left == right
        if operator == "ne":
            return left != right
        if operator == "contains":
            try:
                return right in left
            except (TypeError, AttributeError):
                return False
        if operator == "not_contains":
            try:
                return right not in left
            except (TypeError, AttributeError):
                return True
        if operator in {"gt", "gte", "lt", "lte"}:
            try:
                if operator == "gt":
                    return left > right
                if operator == "gte":
                    return left >= right
                if operator == "lt":
                    return left < right
                return left <= right
            except TypeError:
                return False
        return False

    def _workflow_transform(self, parameters: dict[str, Any]) -> dict[str, Any]:
        value = parameters.get("value")
        operation = str(parameters.get("operation") or "identity")
        if operation == "pick":
            paths = parameters.get("paths") or []
            if not isinstance(paths, list):
                paths = []
            result = {str(path): self._workflow_read_path(value, str(path)) for path in paths}
        elif operation == "omit" and isinstance(value, dict):
            keys = {str(key) for key in (parameters.get("keys") or [])}
            result = {key: item for key, item in value.items() if key not in keys}
        elif operation == "to_array":
            result = value if isinstance(value, list) else [value]
        elif operation == "json_stringify":
            result = json.dumps(value, ensure_ascii=False, sort_keys=True)
        elif operation == "flatten":
            result = [item for group in (value if isinstance(value, list) else []) for item in (group if isinstance(group, list) else [group])]
        else:
            result = value
        return {"result": result}

    def _workflow_loop(self, parameters: dict[str, Any]) -> dict[str, Any]:
        items = parameters.get("items")
        if not isinstance(items, list):
            items = []
        limit = min(max(int(parameters.get("max_iterations") or 100), 1), 1000)
        path = str(parameters.get("path") or "")
        selected = items[:limit]
        results = [self._workflow_read_path(item, path) if path else item for item in selected]
        return {"items": results, "count": len(results), "truncated": len(items) > limit}

    def _workflow_aggregate(self, parameters: dict[str, Any]) -> dict[str, Any]:
        values = parameters.get("values")
        if not isinstance(values, list):
            values = [] if values is None else [values]
        operation = str(parameters.get("operation") or parameters.get("strategy") or "collect")
        if operation in {"merge", "collect"}:
            result: Any = values
        elif operation == "count":
            result = len(values)
        elif operation == "join":
            result = str(parameters.get("separator") or ", ").join(str(value) for value in values)
        else:
            numbers = [float(value) for value in values if isinstance(value, (int, float)) and not isinstance(value, bool)]
            if operation == "sum":
                result = sum(numbers)
            elif operation == "avg":
                result = sum(numbers) / len(numbers) if numbers else None
            elif operation == "min":
                result = min(numbers) if numbers else None
            elif operation == "max":
                result = max(numbers) if numbers else None
            else:
                result = values
        return {"result": result, "count": len(values)}

    def _workflow_node_is_active(
        self,
        node_id: str,
        edges: list[dict[str, Any]],
        node_outputs: dict[str, dict[str, Any]],
    ) -> bool:
        incoming = [edge for edge in edges if str(edge.get("target")) == node_id]
        if not incoming:
            return True
        for edge in incoming:
            source = str(edge.get("source") or "")
            source_record = node_outputs.get(source)
            if not source_record or source_record.get("status") != "success":
                continue
            branch = (source_record.get("output") or {}).get("branch")
            handle = edge.get("source_handle")
            if branch in {"true", "false"} and handle in {"true", "false"} and handle != branch:
                continue
            return True
        return False

    def _workflow_payload_inputs(self, payload: Any) -> dict[str, Any]:
        inputs = payload.get("inputs") if isinstance(payload, dict) else getattr(payload, "inputs", None)
        if not isinstance(inputs, dict):
            inputs = {}
        result = dict(inputs)
        file_id = payload.get("file_id") if isinstance(payload, dict) else getattr(payload, "file_id", None)
        target_kb_id = payload.get("target_kb_id") if isinstance(payload, dict) else getattr(payload, "target_kb_id", None)
        if file_id is not None:
            result.setdefault("file_id", file_id)
        if target_kb_id is not None:
            result.setdefault("target_kb_id", target_kb_id)
        return result

    def _workflow_node_maps(self, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, list[str]], dict[str, int]]:
        node_by_id = {str(node.get("id")): node for node in nodes if node.get("id")}
        outgoing = {node_id: [] for node_id in node_by_id}
        indegree = {node_id: 0 for node_id in node_by_id}
        for edge in edges:
            source = edge.get("source")
            target = edge.get("target")
            if source in node_by_id and target in node_by_id:
                outgoing[source].append(target)
                indegree[target] += 1
        return node_by_id, outgoing, indegree

    def _workflow_topological_order(self, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
        node_by_id, outgoing, indegree = self._workflow_node_maps(nodes, edges)
        original_index = {str(node.get("id")): index for index, node in enumerate(nodes) if node.get("id")}
        ready = sorted((node_id for node_id, degree in indegree.items() if degree == 0), key=lambda item: original_index.get(item, 0))
        ordered_ids: list[str] = []
        while ready:
            node_id = ready.pop(0)
            ordered_ids.append(node_id)
            for target in sorted(outgoing.get(node_id, []), key=lambda item: original_index.get(item, 0)):
                indegree[target] -= 1
                if indegree[target] == 0:
                    ready.append(target)
                    ready.sort(key=lambda item: original_index.get(item, 0))
        if len(ordered_ids) != len(node_by_id):
            return None
        return [node_by_id[node_id] for node_id in ordered_ids]

    def _workflow_read_path(self, value: Any, path: str) -> Any:
        current = value
        parts = [part for part in path.strip(".").split(".") if part]
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                index = int(part)
                current = current[index] if 0 <= index < len(current) else None
            else:
                return None
        return current

    def _workflow_resolve_ref(self, ref: str, node_outputs: dict[str, dict[str, Any]], workflow_inputs: dict[str, Any]) -> Any:
        if not ref.startswith("$"):
            return ref
        body = ref[1:]
        node_id, _, path = body.partition(".")
        if node_id in {"input", "inputs"}:
            return self._workflow_read_path(workflow_inputs, path.removeprefix("output."))
        node_record = node_outputs.get(node_id, {})
        if not path:
            return node_record
        return self._workflow_read_path(node_record, path)

    def _workflow_resolve_value(self, value: Any, node_outputs: dict[str, dict[str, Any]], workflow_inputs: dict[str, Any]) -> Any:
        if isinstance(value, str):
            return self._workflow_resolve_ref(value, node_outputs, workflow_inputs)
        if isinstance(value, list):
            return [self._workflow_resolve_value(item, node_outputs, workflow_inputs) for item in value]
        if isinstance(value, dict):
            mode = value.get("mode")
            if mode == "literal":
                return value.get("value")
            if mode == "input":
                input_key = str(value.get("input_key") or value.get("key") or "")
                return self._workflow_read_path(workflow_inputs, input_key)
            if mode == "node":
                node_id = str(value.get("node_id") or "")
                path = str(value.get("path") or "output")
                return self._workflow_read_path(node_outputs.get(node_id, {}), path)
            if mode == "ref":
                return self._workflow_resolve_ref(str(value.get("value") or ""), node_outputs, workflow_inputs)
            return {key: self._workflow_resolve_value(item, node_outputs, workflow_inputs) for key, item in value.items()}
        return value

    def _workflow_resolve_parameters(self, node: dict[str, Any], node_outputs: dict[str, dict[str, Any]], workflow_inputs: dict[str, Any]) -> dict[str, Any]:
        parameters = node.get("parameters") or {}
        if not isinstance(parameters, dict):
            return {}
        resolved = self._workflow_resolve_value(parameters, node_outputs, workflow_inputs)
        return resolved if isinstance(resolved, dict) else {}

    async def create_agent_task(self, payload: Any, user: UserPublic) -> AgentTaskResponse:
        kb_id = getattr(payload, "kb_id", None)
        if kb_id:
            try:
                await self._ensure_kb_access(kb_id, user)
            except WorkspaceError:
                response = AgentTaskResponse(
                    id=f"agent-{secrets.token_hex(4)}",
                    task=getattr(payload, "task", ""),
                    status="failed",
                    steps=[
                        AgentStep(
                            type="answer",
                            phase="answer",
                            title="知识库不存在",
                            content=f"知识库 {kb_id} 不存在，请检查ID。",
                            tool_name=None,
                            status="failed",
                            error_message="KB_NOT_FOUND",
                        )
                    ],
                    final_answer=f"知识库 {kb_id} 不存在。",
                    result_view={"type": "text", "content": f"知识库 {kb_id} 不存在。"},
                )
                await self._persist_agent_response(response, user, self._agent_request_from_payload(payload))
                await self._s.commit()
                loaded = await self._load_agent_response(response.id, user)
                return loaded or response
        response = await self._agent_executor.run(payload, self, user)
        await self._persist_agent_response(response, user, self._agent_request_from_payload(payload))
        audit_log = AuditLog(
            actor=user.username,
            action="agent.create_task",
            resource_type="agent_task",
            resource_name=getattr(payload, "task", "")[:100],
        )
        await self._audit.create(audit_log)
        await self._s.commit()
        loaded = await self._load_agent_response(response.id, user)
        return loaded or response

    async def get_agent_task(self, task_id: str, user: UserPublic) -> AgentTaskResponse:
        persisted = await self._load_agent_response(task_id, user)
        if persisted:
            return persisted
        task = self._agent_executor.get(task_id, user)
        if not task:
            raise WorkspaceError(404, "AGENT_TASK_NOT_FOUND", "智能体任务不存在", {"task_id": task_id})
        return task

    async def list_agent_tasks(self, user: UserPublic) -> AgentTaskListResponse:
        tasks = await self._agent_tasks.list_by_owner(user.id)
        items: list[AgentTaskResponse] = []
        for task in tasks:
            loaded = await self._load_agent_response(task.id, user)
            if loaded is not None:
                items.append(loaded)
        return AgentTaskListResponse(items=items)

    async def delete_agent_task(self, task_id: str, user: UserPublic) -> None:
        task = await self._agent_tasks.get_by_id(task_id)
        if not task or task.owner_id != user.id:
            raise WorkspaceError(404, "AGENT_TASK_NOT_FOUND", "智能体任务不存在", {"task_id": task_id})
        task_name = task.task[:100]
        await self._agent_tasks.delete(task)
        self._agent_executor.delete(task_id, user)
        await self._audit.create(AuditLog(
            actor=user.username,
            action="agent.delete_task",
            resource_type="agent_task",
            resource_name=task_name,
        ))
        await self._s.commit()

    async def preview_agent_plan(self, payload: Any, user: UserPublic) -> AgentPlanPreviewResponse:
        kb_id = getattr(payload, "kb_id", None)
        if kb_id:
            await self._ensure_kb_access(kb_id, user)
        return await self._agent_executor.preview_plan(payload, user)

    async def stream_agent_task(self, payload: Any, user: UserPublic):
        try:
            response = await self.create_agent_task(payload, user)
            for step in response.steps:
                event_type = step.phase if step.phase in {"plan", "call", "observe", "answer"} else "step"
                yield f"data: {json.dumps({'type': event_type, 'step': step.model_dump()}, ensure_ascii=False, default=str)}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'task': response.model_dump()}, ensure_ascii=False, default=str)}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)}, ensure_ascii=False)}\n\n"

    async def continue_agent_task(self, task_id: str, payload: Any, user: UserPublic) -> AgentTaskResponse:
        inputs = getattr(payload, "inputs", {}) if payload is not None else {}
        message = (getattr(payload, "message", None) or "").strip() if payload is not None else ""
        persisted_task = await self._agent_tasks.get_by_id(task_id)
        if persisted_task and persisted_task.owner_id == user.id:
            if persisted_task.status == "cancelled":
                raise WorkspaceError(409, "AGENT_TASK_CANCELLED", "智能体任务已取消，不能继续执行", {"task_id": task_id})
            request = _json_loads_object(persisted_task.request_json)
            db_messages = await self._agent_messages.list_by_task(task_id)
            db_tool_calls = await self._agent_tool_calls.list_by_task(task_id)
            all_history = [
                {
                    "role": item.role,
                    "content": item.content,
                    "metadata": _json_loads_object(item.metadata_json),
                }
                for item in db_messages
            ]
            history = all_history[-12:]
            history_summary = self._summarize_agent_history(all_history[:-12])
            prior_tool_calls = [
                {
                    "tool_name": item.tool_name,
                    "input_json": _json_loads_object(item.input_json),
                    "output_json": _json_loads_object(item.output_json),
                    "status": item.status,
                    "error_message": item.error_message,
                }
                for item in db_tool_calls
            ][-12:]
            merged_inputs = {**_json_loads_object(json.dumps(request.get("inputs", {}))), **inputs}
            if history:
                merged_inputs["_history"] = history
            if history_summary:
                merged_inputs["_history_summary"] = history_summary
            if prior_tool_calls:
                merged_inputs["_prior_tool_calls"] = prior_tool_calls
            next_task = message or request.get("task", persisted_task.task)
            next_payload = type(
                "_AgentPayload",
                (),
                {
                    "task": next_task,
                    "context_file_ids": request.get("context_file_ids", []),
                    "kb_id": request.get("kb_id"),
                },
            )()
            task = await self._agent_executor.run(next_payload, self, user, task_id=task_id, continuation_inputs=merged_inputs)
            request["task"] = next_task
            request["inputs"] = merged_inputs
            request["history"] = history
            request["history_summary"] = history_summary
            request["prior_tool_calls"] = prior_tool_calls
        else:
            task = await self._agent_executor.continue_task(task_id, inputs, self, user)
            request = None
        if not task:
            raise WorkspaceError(404, "AGENT_TASK_NOT_FOUND", "智能体任务不存在", {"task_id": task_id})
        await self._persist_agent_response(task, user, request or self._agent_request_from_response(task, inputs))
        audit_log = AuditLog(
            actor=user.username,
            action="agent.continue_task",
            resource_type="agent_task",
            resource_name=task.task[:100],
        )
        await self._audit.create(audit_log)
        await self._s.commit()
        loaded = await self._load_agent_response(task.id, user)
        return loaded or task

    async def cancel_agent_task(self, task_id: str, user: UserPublic) -> AgentTaskResponse:
        task = await self._agent_tasks.get_by_id(task_id)
        if not task or task.owner_id != user.id:
            raise WorkspaceError(404, "AGENT_TASK_NOT_FOUND", "智能体任务不存在", {"task_id": task_id})
        if task.status in {"completed", "failed", "cancelled"}:
            raise WorkspaceError(
                409,
                "AGENT_TASK_NOT_CANCELABLE",
                "智能体任务已结束，不能取消",
                {"task_id": task_id, "status": task.status},
            )

        existing_steps = await self._agent_steps.list_by_task(task_id)
        cancel_step = AgentTaskStep(
            task_id=task_id,
            sequence=len(existing_steps),
            type="answer",
            phase="answer",
            title="任务已取消",
            content="用户已取消该智能体任务。",
            status="failed",
            error_message="AGENT_TASK_CANCELLED",
            metadata_json=json.dumps({"cancelled_by": user.username}, ensure_ascii=False),
        )
        task.status = "cancelled"
        task.final_answer = "任务已取消。"
        task.result_view_json = json.dumps({"type": "text", "content": "任务已取消。"}, ensure_ascii=False)
        await self._agent_tasks.update(task)
        self._s.add(cancel_step)
        await self._s.flush()
        await self._audit.create(AuditLog(
            actor=user.username,
            action="agent.cancel_task",
            resource_type="agent_task",
            resource_name=task.task[:100],
        ))
        await self._s.commit()
        response = await self._load_agent_response(task_id, user)
        if response is None:
            raise WorkspaceError(404, "AGENT_TASK_NOT_FOUND", "智能体任务不存在", {"task_id": task_id})
        return response

    def _agent_request_from_payload(self, payload: Any, inputs: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "task": getattr(payload, "task", ""),
            "context_file_ids": list(getattr(payload, "context_file_ids", []) or []),
            "kb_id": getattr(payload, "kb_id", None),
            "inputs": inputs or {},
        }

    def _agent_request_from_response(self, response: AgentTaskResponse, inputs: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "task": response.task,
            "context_file_ids": [],
            "kb_id": None,
            "inputs": inputs or {},
        }

    async def _persist_agent_response(self, response: AgentTaskResponse, user: UserPublic, request: dict[str, Any]) -> None:
        existing = await self._agent_tasks.get_by_id(response.id)
        result_view_json = json.dumps(response.result_view, ensure_ascii=False, default=str)
        request_json = json.dumps(request, ensure_ascii=False, default=str)
        context_file_ids_json = json.dumps(request.get("context_file_ids", []), ensure_ascii=False)
        if existing:
            existing.status = response.status
            existing.task = response.task
            existing.kb_id = request.get("kb_id")
            existing.context_file_ids_json = context_file_ids_json
            existing.request_json = request_json
            existing.final_answer = response.final_answer
            existing.result_view_json = result_view_json
            await self._agent_tasks.update(existing)
        else:
            await self._agent_tasks.create(AgentTask(
                id=response.id,
                owner_id=user.id,
                task=response.task,
                status=response.status,
                kb_id=request.get("kb_id"),
                context_file_ids_json=context_file_ids_json,
                request_json=request_json,
                final_answer=response.final_answer,
                result_view_json=result_view_json,
            ))
        db_steps = [
            AgentTaskStep(
                task_id=response.id,
                sequence=index,
                type=step.type,
                phase=step.phase,
                title=step.title,
                content=step.content,
                tool_name=step.tool_name,
                input_json=json.dumps(step.input_json, ensure_ascii=False, default=str),
                output_json=json.dumps(step.output_json, ensure_ascii=False, default=str),
                status=step.status,
                error_message=step.error_message,
                metadata_json=json.dumps(step.metadata, ensure_ascii=False, default=str),
            )
            for index, step in enumerate(response.steps)
        ]
        await self._agent_steps.replace_for_task(response.id, db_steps)
        await self._agent_messages.replace_for_task(
            response.id,
            self._agent_messages_from_response(response, request),
        )
        await self._agent_tool_calls.replace_for_task(
            response.id,
            self._agent_tool_calls_from_response(response),
        )
        await self._agent_plan_revisions.replace_for_task(
            response.id,
            self._agent_plan_revisions_from_response(response),
        )

    async def _load_agent_response(self, task_id: str, user: UserPublic) -> AgentTaskResponse | None:
        task = await self._agent_tasks.get_by_id(task_id)
        if not task or task.owner_id != user.id:
            return None
        db_steps = await self._agent_steps.list_by_task(task_id)
        db_messages = await self._agent_messages.list_by_task(task_id)
        db_tool_calls = await self._agent_tool_calls.list_by_task(task_id)
        db_plan_revisions = await self._agent_plan_revisions.list_by_task(task_id)
        return AgentTaskResponse(
            id=task.id,
            task=task.task,
            status=task.status,
            steps=[
                AgentStep(
                    type=step.type,
                    phase=step.phase,
                    title=step.title,
                    content=step.content,
                    tool_name=step.tool_name,
                    input_json=_json_loads_object(step.input_json),
                    output_json=_json_loads_object(step.output_json),
                    status=step.status,
                    error_message=step.error_message,
                    metadata=_json_loads_object(step.metadata_json),
                )
                for step in db_steps
            ],
            final_answer=task.final_answer,
            result_view=_json_loads_object(task.result_view_json),
            messages=[
                AgentMessageSchema(
                    id=message.id,
                    role=message.role,
                    content=message.content,
                    metadata=_json_loads_object(message.metadata_json),
                )
                for message in db_messages
            ],
            tool_calls=[
                AgentToolCallSchema(
                    id=call.id,
                    tool_name=call.tool_name,
                    input_json=_json_loads_object(call.input_json),
                    output_json=_json_loads_object(call.output_json),
                    status=call.status,
                    error_message=call.error_message,
                    latency_ms=call.latency_ms,
                )
                for call in db_tool_calls
            ],
            plan_revisions=[
                AgentPlanRevisionSchema(
                    id=revision.id,
                    revision_no=revision.revision_no,
                    reason=revision.reason,
                    plan_json=_json_loads_object(revision.plan_json),
                )
                for revision in db_plan_revisions
            ],
        )

    def _agent_messages_from_response(self, response: AgentTaskResponse, request: dict[str, Any]) -> list[AgentMessage]:
        messages: list[AgentMessage] = []
        history = request.get("history", [])
        if isinstance(history, list):
            for item in self._compact_agent_history(history):
                if not isinstance(item, dict):
                    continue
                role = item.get("role") if item.get("role") in {"user", "assistant", "system"} else "system"
                content = str(item.get("content") or "").strip()
                if not content:
                    continue
                messages.append(AgentMessage(
                    id=f"{response.id}-msg-{len(messages)}",
                    task_id=response.id,
                    sequence=len(messages),
                    role=role,
                    content=content,
                    metadata_json=json.dumps(item.get("metadata") or {}, ensure_ascii=False, default=str),
                ))

        raw_inputs = request.get("inputs", {})
        metadata_inputs = dict(raw_inputs) if isinstance(raw_inputs, dict) else {}
        metadata_inputs.pop("_history", None)
        metadata_inputs.pop("_history_summary", None)
        metadata_inputs.pop("_prior_tool_calls", None)
        messages.append(AgentMessage(
            id=f"{response.id}-msg-{len(messages)}",
            task_id=response.id,
            sequence=len(messages),
            role="user",
            content=str(request.get("task") or response.task),
            metadata_json=json.dumps({
                "context_file_ids": request.get("context_file_ids", []),
                "kb_id": request.get("kb_id"),
                "inputs": metadata_inputs,
            }, ensure_ascii=False, default=str),
        ))
        messages.append(AgentMessage(
            id=f"{response.id}-msg-{len(messages)}",
            task_id=response.id,
            sequence=len(messages),
            role="assistant",
            content=response.final_answer,
            metadata_json=json.dumps({
                "status": response.status,
                "result_view": response.result_view,
            }, ensure_ascii=False, default=str),
        ))
        return messages

    def _summarize_agent_history(self, history: list[dict[str, Any]]) -> str:
        if not history:
            return ""
        fragments: list[str] = []
        for item in history[-20:]:
            role = str(item.get("role") or "system")
            content = str(item.get("content") or "").strip().replace("\n", " ")
            if not content:
                continue
            fragments.append(f"{role}: {content[:160]}")
        return "；".join(fragments)

    def _compact_agent_history(self, history: list[Any]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for item in history:
            if not isinstance(item, dict):
                continue
            role = item.get("role") if item.get("role") in {"user", "assistant", "system"} else "system"
            content = str(item.get("content") or "").strip()
            if not content:
                continue
            metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
            normalized.append({"role": role, "content": content, "metadata": metadata})

        if len(normalized) <= 10:
            return normalized

        older = normalized[:-8]
        recent = normalized[-8:]
        existing_summary = next(
            (
                item for item in older
                if item["role"] == "system" and item.get("metadata", {}).get("kind") == "history_summary"
            ),
            None,
        )
        summary_lines: list[str] = []
        if existing_summary:
            summary_lines.append(existing_summary["content"])
        for item in older:
            if item is existing_summary:
                continue
            role_label = {"user": "用户", "assistant": "助手", "system": "系统"}.get(item["role"], "系统")
            summary_lines.append(f"{role_label}: {item['content']}")
        summary = "历史摘要：" + "；".join(summary_lines)
        if len(summary) > 1200:
            summary = f"{summary[:1200].rstrip()}..."
        return [
            {
                "role": "system",
                "content": summary,
                "metadata": {"kind": "history_summary", "source_message_count": len(normalized)},
            },
            *recent,
        ]

    def _agent_tool_calls_from_response(self, response: AgentTaskResponse) -> list[AgentToolCall]:
        calls: list[AgentToolCall] = []
        for index, step in enumerate(response.steps):
            if step.phase != "call" or not step.tool_name:
                continue
            calls.append(AgentToolCall(
                id=f"{response.id}-call-{len(calls)}",
                task_id=response.id,
                step_sequence=index,
                tool_name=step.tool_name,
                input_json=json.dumps(step.input_json, ensure_ascii=False, default=str),
                output_json=json.dumps(step.output_json, ensure_ascii=False, default=str),
                status="needs_clarification" if step.status == "needs_clarification" else ("failed" if step.status == "failed" else "success"),
                error_message=step.error_message,
                latency_ms=int(step.metadata.get("latency_ms", 0) or 0),
            ))
        return calls

    def _agent_plan_revisions_from_response(self, response: AgentTaskResponse) -> list[AgentPlanRevision]:
        revisions: list[AgentPlanRevision] = []
        for index, step in enumerate(response.steps):
            if step.phase != "plan":
                continue
            revisions.append(AgentPlanRevision(
                id=f"{response.id}-plan-{len(revisions)}",
                task_id=response.id,
                revision_no=len(revisions),
                reason=str(step.metadata.get("revision_reason") or step.title),
                plan_json=json.dumps(step.input_json, ensure_ascii=False, default=str),
            ))
        return revisions

    def _can_read_workflow(self, workflow: Workflow, user: UserPublic) -> bool:
        return workflow.status == "template" or str(workflow.created_by) == str(user.id)

    async def _ensure_workflow_access(self, workflow_id: str, user: UserPublic, *, manage: bool = False) -> Workflow:
        workflow = await self._workflows.get_by_id(workflow_id)
        if not workflow or not self._can_read_workflow(workflow, user):
            raise WorkspaceError(404, "WORKFLOW_NOT_FOUND", "流程不存在", {"workflow_id": workflow_id})
        if manage and str(workflow.created_by) != str(user.id):
            raise WorkspaceError(403, "WORKFLOW_MANAGE_FORBIDDEN", "没有管理该流程的权限", {"workflow_id": workflow_id})
        return workflow

    async def list_workflows(self, user: UserPublic) -> list[WorkflowDefinition]:
        import json as _json
        wfs = await self._workflows.list_all()
        wfs = [wf for wf in wfs if self._can_read_workflow(wf, user)]
        result = []
        for wf in wfs:
            try:
                node_count = len(_json.loads(wf.nodes or "[]"))
            except (TypeError, ValueError):
                node_count = 0
            result.append(WorkflowDefinition(
                id=wf.id, name=wf.name, description=wf.description or "",
                trigger=wf.trigger, version=wf.version, status=wf.status,
                revision=wf.revision, node_count=node_count, nodes=[], edges=[],
            ))
        return result

    async def get_workflow(self, workflow_id: str, user: UserPublic) -> WorkflowDefinition:
        import json as _json
        wf = await self._ensure_workflow_access(workflow_id, user)
        nodes = _json.loads(wf.nodes) if wf.nodes else []
        edges = _json.loads(wf.edges) if wf.edges else []
        return WorkflowDefinition(
            id=wf.id,
            name=wf.name,
            description=wf.description or "",
            trigger=wf.trigger,
            version=wf.version,
            status=wf.status,
            revision=wf.revision,
            node_count=len(nodes),
            nodes=nodes,
            edges=edges,
        )

    async def create_workflow(self, payload: Any, user: UserPublic) -> WorkflowDefinition:
        import secrets as _s
        import json as _json
        wid = f"wf-{_s.token_hex(4)}"
        nodes_raw = _jsonable_list(getattr(payload, "nodes", None) or [])
        edges_raw = _jsonable_list(getattr(payload, "edges", None) or [])
        nodes_json = _json.dumps(nodes_raw, ensure_ascii=False)
        edges_json = _json.dumps(edges_raw, ensure_ascii=False)
        wf = Workflow(id=wid, name=(getattr(payload, "name", None) or "新流程"),
                      description=(getattr(payload, "description", None) or ""),
                      trigger=getattr(payload, "trigger", None) or "manual",
                      version="0.1.0", status="draft",
                      nodes=nodes_json, edges=edges_json, created_by=user.id)
        await self._workflows.create(wf)
        await self._s.commit()
        return WorkflowDefinition(id=wid, name=wf.name, description=wf.description or "",
                                   trigger=wf.trigger, version=wf.version, status=wf.status,
                                   revision=wf.revision,
                                   node_count=len(nodes_raw), nodes=nodes_raw, edges=edges_raw)

    async def update_workflow(self, workflow_id: str, payload: Any, user: UserPublic) -> WorkflowDefinition:
        import json as _json
        wf = await self._ensure_workflow_access(workflow_id, user, manage=True)
        expected_revision = getattr(payload, "expected_revision", None)
        if expected_revision is not None and expected_revision != wf.revision:
            raise WorkspaceError(409, "WORKFLOW_REVISION_CONFLICT", "流程已被其他会话修改，请重新加载", {
                "workflow_id": workflow_id, "expected_revision": expected_revision, "actual_revision": wf.revision,
            })
        if getattr(payload, "name", None):
            wf.name = getattr(payload, "name")
        if getattr(payload, "description", None) is not None:
            wf.description = getattr(payload, "description")
        if getattr(payload, "trigger", None):
            wf.trigger = getattr(payload, "trigger")
        nodes_raw = getattr(payload, "nodes", None)
        if nodes_raw is not None:
            nodes_raw = _jsonable_list(nodes_raw)
            wf.nodes = _json.dumps(nodes_raw, ensure_ascii=False)
        edges_raw = getattr(payload, "edges", None)
        if edges_raw is not None:
            edges_raw = _jsonable_list(edges_raw)
            wf.edges = _json.dumps(edges_raw, ensure_ascii=False)
        if wf.status == "published":
            wf.status = "draft"
        wf.revision += 1
        await self._workflows.update(wf)
        await self._s.commit()
        nodes_out = _json.loads(wf.nodes) if wf.nodes else []
        edges_out = _json.loads(wf.edges) if wf.edges else []
        return WorkflowDefinition(id=workflow_id, name=wf.name, description=wf.description or "",
                                   trigger=wf.trigger, version=wf.version, status=wf.status,
                                   revision=wf.revision,
                                   node_count=len(nodes_out), nodes=nodes_out, edges=edges_out)

    async def validate_workflow(self, workflow_id: str, user: UserPublic) -> Any:
        import json as _json
        wf = await self._ensure_workflow_access(workflow_id, user)
        nodes = _json.loads(wf.nodes) if wf.nodes else []
        edges = _json.loads(wf.edges) if wf.edges else []
        issues = []
        tools = {t.name: t for t in await self.list_tools()}
        tool_names = set(tools)
        node_ids = set()
        if not nodes:
            issues.append({"code": "WORKFLOW_EMPTY", "message": "流程至少需要 1 个节点"})
        for n in nodes:
            node_id = n.get("id")
            if not node_id:
                issues.append({"code": "WORKFLOW_NODE_ID_REQUIRED", "message": "流程节点缺少 ID"})
                continue
            if node_id in node_ids:
                issues.append({"code": "WORKFLOW_NODE_DUPLICATE", "message": f"流程节点 ID 重复: {node_id}", "node_id": node_id})
            node_ids.add(node_id)
        for n in nodes:
            tn = n.get("tool_name")
            if n.get("type") == "tool" and not tn:
                issues.append({"code": "WORKFLOW_TOOL_REQUIRED", "message": "工具节点缺少 tool_name", "node_id": n.get("id")})
            elif tn and tn not in tool_names:
                issues.append({"code": "WORKFLOW_TOOL_UNKNOWN", "message": f"工具节点引用了未注册工具: {tn}", "node_id": n.get("id")})
        for e in edges:
            if e.get("source") not in node_ids or e.get("target") not in node_ids:
                issues.append({"code": "WORKFLOW_EDGE_INVALID", "message": f"连线 {e.get('id')} 引用了不存在的节点", "edge_id": e.get("id")})
        incoming: dict[str, list[str]] = {str(node_id): [] for node_id in node_ids}
        for edge in edges:
            source, target = edge.get("source"), edge.get("target")
            if source in node_ids and target in node_ids:
                incoming[str(target)].append(str(source))
        input_keys = {
            str(key)
            for node in nodes if node.get("type") == "input"
            for key in (node.get("parameters") or {}).keys()
        }

        def upstream_ids(node_id: str) -> set[str]:
            result: set[str] = set()
            stack = list(incoming.get(node_id, []))
            while stack:
                source = stack.pop()
                if source in result:
                    continue
                result.add(source)
                stack.extend(incoming.get(source, []))
            return result

        def validate_binding(value: Any, node_id: str, parameter: str) -> None:
            if isinstance(value, list):
                for item in value:
                    validate_binding(item, node_id, parameter)
                return
            if not isinstance(value, dict):
                return
            mode = value.get("mode")
            if mode == "input":
                key = str(value.get("input_key") or value.get("key") or "")
                if key not in input_keys:
                    issues.append({"code": "WORKFLOW_INPUT_REF_INVALID", "message": f"参数 {parameter} 引用了不存在的流程输入: {key}", "node_id": node_id})
                return
            if mode == "node":
                source_id = str(value.get("node_id") or "")
                if source_id not in node_ids:
                    issues.append({"code": "WORKFLOW_NODE_REF_INVALID", "message": f"参数 {parameter} 引用了不存在的节点: {source_id}", "node_id": node_id})
                elif source_id not in upstream_ids(node_id):
                    issues.append({"code": "WORKFLOW_NODE_REF_NOT_UPSTREAM", "message": f"参数 {parameter} 只能引用上游节点: {source_id}", "node_id": node_id})
                return
            for nested in value.values():
                validate_binding(nested, node_id, parameter)

        for node in nodes:
            node_id = str(node.get("id") or "")
            parameters = node.get("parameters") or {}
            for key, value in parameters.items():
                validate_binding(value, node_id, str(key))
            node_type = node.get("type")
            if node_type == "condition":
                operator = parameters.get("operator")
                if operator not in {"truthy", "falsy", "eq", "ne", "contains", "not_contains", "gt", "gte", "lt", "lte"}:
                    issues.append({"code": "WORKFLOW_CONDITION_OPERATOR_INVALID", "message": "条件节点缺少有效 operator", "node_id": node_id})
                branch_handles = {edge.get("source_handle") for edge in edges if edge.get("source") == node_id}
                if not branch_handles or not branch_handles.issubset({"true", "false"}):
                    issues.append({"code": "WORKFLOW_CONDITION_BRANCH_INVALID", "message": "条件节点出边必须使用 true 或 false 分支", "node_id": node_id})
            elif node_type == "transform" and parameters.get("operation") not in {"identity", "pick", "omit", "to_array", "json_stringify", "flatten"}:
                issues.append({"code": "WORKFLOW_TRANSFORM_OPERATION_INVALID", "message": "转换节点缺少有效 operation", "node_id": node_id})
            elif node_type == "loop":
                limit = parameters.get("max_iterations", 100)
                if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 1000:
                    issues.append({"code": "WORKFLOW_LOOP_LIMIT_INVALID", "message": "循环节点 max_iterations 必须在 1 到 1000 之间", "node_id": node_id})
            elif node_type == "aggregate" and (parameters.get("operation") or parameters.get("strategy", "collect")) not in {"collect", "merge", "count", "sum", "avg", "min", "max", "join"}:
                issues.append({"code": "WORKFLOW_AGGREGATE_OPERATION_INVALID", "message": "聚合节点缺少有效 operation", "node_id": node_id})
            tool = tools.get(node.get("tool_name"))
            if not tool:
                continue
            required = tool.input_schema.get("required", []) if isinstance(tool.input_schema, dict) else []
            for key in required:
                value = parameters.get(key)
                missing = value is None or value == "" or (
                    isinstance(value, dict) and value.get("mode") == "literal" and value.get("value") in (None, "")
                )
                if missing:
                    issues.append({"code": "WORKFLOW_TOOL_PARAMETER_REQUIRED", "message": f"工具 {tool.name} 缺少必填参数: {key}", "node_id": node_id})
        if self._workflow_topological_order(nodes, edges) is None:
            issues.append({"code": "WORKFLOW_CYCLE", "message": "流程连线存在环，不能形成 DAG"})
        return {"valid": len(issues) == 0, "issues": issues, "node_count": len(nodes), "edge_count": len(edges)}

    async def publish_workflow(self, workflow_id: str, user: UserPublic) -> WorkflowDefinition:
        wf = await self._ensure_workflow_access(workflow_id, user, manage=True)
        validation = await self.validate_workflow(workflow_id, user)
        if not validation["valid"]:
            raise WorkspaceError(
                409,
                "WORKFLOW_INVALID",
                "流程校验未通过，不能发布",
                {"workflow_id": workflow_id, "issues": validation["issues"]},
            )
        wf.status = "published"
        wf.revision += 1
        parts = wf.version.split(".")
        try:
            major = int(parts[0]) if parts else 0
            minor = int(parts[1]) if len(parts) > 1 else 0
            wf.version = f"{major}.{minor + 1}.0"
        except ValueError:
            wf.version = "1.0.0"
        await self._workflow_versions.create(WorkflowVersion(
            id=f"wfver-{secrets.token_hex(6)}",
            workflow_id=workflow_id,
            version=wf.version,
            name=wf.name,
            description=wf.description or "",
            trigger=wf.trigger,
            nodes_json=wf.nodes or "[]",
            edges_json=wf.edges or "[]",
            published_by=user.id,
        ))
        await self._workflows.update(wf)
        await self._s.commit()
        import json as _json
        nodes = _json.loads(wf.nodes) if wf.nodes else []
        edges = _json.loads(wf.edges) if wf.edges else []
        return WorkflowDefinition(id=workflow_id, name=wf.name, description=wf.description or "",
                                   trigger=wf.trigger, version=wf.version, status=wf.status,
                                   revision=wf.revision,
                                   node_count=len(nodes), nodes=nodes, edges=edges)

    async def list_workflow_versions(self, workflow_id: str, user: UserPublic) -> list[WorkflowVersionPublic]:
        import json as _json
        await self._ensure_workflow_access(workflow_id, user)
        versions = await self._workflow_versions.list_by_workflow(workflow_id)
        return [WorkflowVersionPublic(
            id=item.id,
            workflow_id=item.workflow_id,
            version=item.version,
            name=item.name,
            description=item.description or "",
            trigger=item.trigger,
            nodes=_json.loads(item.nodes_json or "[]"),
            edges=_json.loads(item.edges_json or "[]"),
            published_at=item.published_at,
        ) for item in versions]

    async def restore_workflow_version(self, workflow_id: str, version_id: str, user: UserPublic) -> WorkflowDefinition:
        wf = await self._ensure_workflow_access(workflow_id, user, manage=True)
        version = await self._workflow_versions.get_by_id(version_id)
        if not version or version.workflow_id != workflow_id:
            raise WorkspaceError(404, "WORKFLOW_VERSION_NOT_FOUND", "流程版本不存在", {"version_id": version_id})
        wf.name = version.name
        wf.description = version.description or ""
        wf.trigger = version.trigger
        wf.nodes = version.nodes_json
        wf.edges = version.edges_json
        wf.status = "draft"
        wf.revision += 1
        await self._workflows.update(wf)
        await self._s.commit()
        return await self.get_workflow(workflow_id, user)

    async def list_workflow_executions(self, workflow_id: str, user: UserPublic) -> list[WorkflowExecutionRecord]:
        import json as _json
        await self._ensure_workflow_access(workflow_id, user)
        executions = await self._workflow_executions.list_by_workflow(workflow_id)
        return [WorkflowExecutionRecord(
            id=item.id,
            workflow_id=item.workflow_id,
            workflow_version=item.workflow_version,
            status=item.status,
            node_executions=_json.loads(item.node_executions_json or "[]"),
            output=_json.loads(item.output_json or "{}"),
            created_at=item.created_at,
        ) for item in executions]

    async def execute_workflow(self, workflow_id: str, payload: Any, user: UserPublic) -> WorkflowExecutionResponse:
        import secrets as _s
        import json as _json
        wf = await self._ensure_workflow_access(workflow_id, user)
        if wf.status != "published":
            raise WorkspaceError(
                409,
                "WORKFLOW_NOT_PUBLISHED",
                "流程尚未发布，不能执行",
                {"workflow_id": workflow_id},
            )
        nodes = _json.loads(wf.nodes) if wf.nodes else []
        edges = _json.loads(wf.edges) if wf.edges else []
        if not nodes:
            return WorkflowExecutionResponse(id=f"exec-{_s.token_hex(4)}", workflow_id=workflow_id, status="completed", node_executions=[], output={"summary": f"流程「{wf.name}」无节点，执行完成"})
        ordered_nodes = self._workflow_topological_order(nodes, edges)
        if ordered_nodes is None:
            return WorkflowExecutionResponse(id=f"exec-{_s.token_hex(4)}", workflow_id=workflow_id, status="failed", node_executions=[], output={"summary": f"流程「{wf.name}」包含环路，无法执行 DAG"})

        node_executions = []
        node_outputs: dict[str, dict[str, Any]] = {}
        workflow_inputs = self._workflow_payload_inputs(payload)
        workflow_failed = False
        final_output: dict[str, Any] = {}
        for node in ordered_nodes:
            if not self._workflow_node_is_active(str(node.get("id") or ""), edges, node_outputs):
                node_executions.append(self._workflow_skipped_node(node))
                continue
            record = await self._execute_workflow_node(node, edges, node_outputs, workflow_inputs, user)
            node_executions.append(record)
            final_output = record["output"]
            if record["status"] == "failed":
                workflow_failed = True
                break
        summary = f"流程「{wf.name}」执行{'失败' if workflow_failed else '完成'}，共执行 {len(node_executions)} 个节点"
        output = {"summary": summary, "result": final_output, "nodes": node_outputs}
        response = WorkflowExecutionResponse(id=f"exec-{_s.token_hex(4)}", workflow_id=workflow_id, status="failed" if workflow_failed else "completed", node_executions=node_executions, output=output)
        await self._workflow_executions.create(WorkflowExecution(
            id=response.id,
            workflow_id=workflow_id,
            workflow_version=wf.version,
            status=response.status,
            node_executions_json=_json.dumps([item.model_dump() for item in response.node_executions], ensure_ascii=False),
            output_json=_json.dumps(response.output, ensure_ascii=False),
            created_by=user.id,
        ))
        await self._s.commit()
        return response

    async def _seed_workflow_templates(self) -> None:
        """Seed built-in workflow templates if none exist."""
        import secrets as _s
        import json as _json
        file_compare_template = {
            "name": "文件比对报告",
            "trigger": "manual",
            "description": "选择两个可访问文本文件，逐行比对并生成结构化 Markdown 差异报告",
            "nodes": [
                {
                    "id": "input-compare",
                    "name": "选择待比对文件",
                    "type": "input",
                    "tool_name": None,
                    "parameters": {"file_a": "", "file_b": "", "context_lines": 3},
                    "position": {"x": 80, "y": 170},
                },
                {
                    "id": "tool-compare",
                    "name": "逐行比对文件",
                    "type": "tool",
                    "tool_name": "file_compare",
                    "parameters": {
                        "file_a": {"mode": "input", "input_key": "file_a"},
                        "file_b": {"mode": "input", "input_key": "file_b"},
                        "context_lines": {"mode": "input", "input_key": "context_lines"},
                    },
                    "position": {"x": 420, "y": 170},
                },
                {
                    "id": "output-compare",
                    "name": "输出比对报告",
                    "type": "output",
                    "tool_name": None,
                    "parameters": {
                        "format": "markdown",
                        "report": {"mode": "node", "node_id": "tool-compare", "path": "output.report"},
                        "summary": {"mode": "node", "node_id": "tool-compare", "path": "output.summary"},
                        "diff": {"mode": "node", "node_id": "tool-compare", "path": "output.diff"},
                        "file_a": {"mode": "node", "node_id": "tool-compare", "path": "output.file_a"},
                        "file_b": {"mode": "node", "node_id": "tool-compare", "path": "output.file_b"},
                    },
                    "position": {"x": 760, "y": 170},
                },
            ],
            "edges": [
                {"id": "compare-e1", "source": "input-compare", "target": "tool-compare", "type": "smoothstep"},
                {"id": "compare-e2", "source": "tool-compare", "target": "output-compare", "type": "smoothstep"},
            ],
        }
        existing = await self._workflows.list_all()
        if any(w.status == "template" for w in existing):
            for workflow in existing:
                if workflow.status == "template":
                    if workflow.name == file_compare_template["name"]:
                        canonical_nodes = _json.dumps(file_compare_template["nodes"], ensure_ascii=False)
                        canonical_edges = _json.dumps(file_compare_template["edges"], ensure_ascii=False)
                        if workflow.nodes != canonical_nodes or workflow.edges != canonical_edges:
                            workflow.description = file_compare_template["description"]
                            workflow.trigger = file_compare_template["trigger"]
                            workflow.nodes = canonical_nodes
                            workflow.edges = canonical_edges
                            workflow.version = "1.1.0"
                            await self._workflows.update(workflow)
                        continue
                    nodes = _json.loads(workflow.nodes) if workflow.nodes else []
                    migrated = False
                    for node in nodes:
                        old_name = node.get("tool_name")
                        new_name = {
                            "file_search": "file_content_search",
                            "knowledge_qa": "file_content_search",
                            "report_generate": "calculator",
                            "file_compare": "file_content_search",
                            "image_ocr": "file_content_search",
                            "team_activity": "course_lookup",
                        }.get(old_name, old_name)
                        if new_name != old_name:
                            node["tool_name"] = new_name
                            migrated = True
                    if migrated:
                        workflow.nodes = _json.dumps(nodes, ensure_ascii=False)
                        await self._workflows.update(workflow)
            await self._s.commit()
            return
        templates = [
            {"name": "新文件自动摘要", "trigger": "file_upload", "description": "上传文件后自动解析内容并生成摘要报告", "nodes": [
                {"id": "trigger-1", "name": "文件上传触发", "type": "trigger", "tool_name": None, "parameters": {}, "position": {"x": 80, "y": 170}},
                {"id": "tool-search", "name": "搜索相关文件", "type": "tool", "tool_name": "file_content_search", "parameters": {"query": ""}, "position": {"x": 360, "y": 110}},
                {"id": "tool-data", "name": "CSV 数据分析", "type": "tool", "tool_name": "python_data", "parameters": {}, "position": {"x": 650, "y": 110}},
                {"id": "output-report", "name": "生成摘要报告", "type": "output", "tool_name": None, "parameters": {"format": "markdown"}, "position": {"x": 940, "y": 170}},
            ], "edges": [
                {"id": "e1", "source": "trigger-1", "target": "tool-search", "type": "smoothstep"},
                {"id": "e2", "source": "tool-search", "target": "tool-data", "type": "smoothstep"},
                {"id": "e3", "source": "tool-data", "target": "output-report", "type": "smoothstep"},
            ]},
            {"name": "团队周报生成", "trigger": "schedule", "description": "定时收集团队活动与文件变更，生成 Markdown 周报", "nodes": [
                {"id": "trigger-w", "name": "每周触发", "type": "trigger", "tool_name": None, "parameters": {"cron": "0 9 * * 1"}, "position": {"x": 80, "y": 170}},
                {"id": "tool-files", "name": "搜索本周文件", "type": "tool", "tool_name": "file_content_search", "parameters": {"query": "周报"}, "position": {"x": 360, "y": 250}},
                {"id": "tool-course", "name": "查询课程安排", "type": "tool", "tool_name": "course_lookup", "parameters": {"query": "算法"}, "position": {"x": 650, "y": 180}},
                {"id": "output-weekly", "name": "发布周报", "type": "output", "tool_name": None, "parameters": {"format": "markdown", "destination": "team-channel"}, "position": {"x": 940, "y": 180}},
            ], "edges": [
                {"id": "e1", "source": "trigger-w", "target": "tool-files", "type": "smoothstep"},
                {"id": "e2", "source": "tool-files", "target": "tool-course", "type": "smoothstep"},
                {"id": "e3", "source": "tool-course", "target": "output-weekly", "type": "smoothstep"},
            ]},
            {"name": "批量知识问答", "trigger": "manual", "description": "对知识库中的文件逐一提问并汇总结果", "nodes": [
                {"id": "trigger-b", "name": "手动触发", "type": "trigger", "tool_name": None, "parameters": {}, "position": {"x": 80, "y": 170}},
                {"id": "tool-search", "name": "文件内容查询", "type": "tool", "tool_name": "file_content_search", "parameters": {"query": ""}, "position": {"x": 360, "y": 110}},
                {"id": "aggregate", "name": "汇总答案", "type": "aggregate", "tool_name": None, "parameters": {"strategy": "merge"}, "position": {"x": 650, "y": 170}},
                {"id": "output-batch", "name": "输出问答结果", "type": "output", "tool_name": None, "parameters": {"format": "markdown"}, "position": {"x": 940, "y": 170}},
            ], "edges": [
                {"id": "e1", "source": "trigger-b", "target": "tool-search", "type": "smoothstep"},
                {"id": "e2", "source": "tool-search", "target": "aggregate", "type": "smoothstep"},
                {"id": "e3", "source": "aggregate", "target": "output-batch", "type": "smoothstep"},
            ]},
            file_compare_template,
            {"name": "知识入库处理", "trigger": "file_upload", "description": "上传文件后自动解析、OCR识别、分块索引到知识库", "nodes": [
                {"id": "trigger-k", "name": "文件上传触发", "type": "trigger", "tool_name": None, "parameters": {"event": "file.created"}, "position": {"x": 80, "y": 170}},
                {"id": "tool-search", "name": "搜索重复文件", "type": "tool", "tool_name": "file_content_search", "parameters": {"query": ""}, "position": {"x": 360, "y": 240}},
                {"id": "tool-data", "name": "CSV 数据分析", "type": "tool", "tool_name": "python_data", "parameters": {}, "position": {"x": 650, "y": 170}},
                {"id": "output-kb", "name": "更新知识库", "type": "output", "tool_name": None, "parameters": {"format": "markdown", "destination": "knowledge-base"}, "position": {"x": 940, "y": 170}},
            ], "edges": [
                {"id": "e1", "source": "trigger-k", "target": "tool-search", "type": "smoothstep"},
                {"id": "e2", "source": "tool-search", "target": "tool-data", "type": "smoothstep"},
                {"id": "e3", "source": "tool-data", "target": "output-kb", "type": "smoothstep"},
            ]},
        ]
        for tmpl in templates:
            wid = f"wf-{_s.token_hex(4)}"
            wf = Workflow(id=wid, name=tmpl["name"], description=tmpl["description"],
                          trigger=tmpl["trigger"], version="1.0.0", status="template",
                          nodes=_json.dumps(tmpl["nodes"], ensure_ascii=False),
                          edges=_json.dumps(tmpl["edges"], ensure_ascii=False),
                          created_by="system")
            await self._workflows.create(wf)
        await self._s.commit()

    # ── File Compression ──
    async def compress_files(self, file_ids: list[str], algorithm: str, user: UserPublic) -> CompressionResult:
        """Compress multiple files into a single archive."""
        import io as _io
        import zipfile as _zipfile
        import tarfile as _tarfile

        files_data: list[tuple[str, bytes]] = []
        total_original = 0
        for fid in file_ids:
            db_file = await self._files.get_by_id(fid)
            if db_file is None:
                raise ValueError(f"FILE_NOT_FOUND: {fid}")
            await self._ensure_can_read_file(db_file, user)
            content = _read_file_content(db_file)
            if content is None:
                raise ValueError(f"CONTENT_MISSING: {fid}")
            files_data.append((db_file.name, content))
            total_original += len(content)

        buf = _io.BytesIO()
        if algorithm == "zip":
            with _zipfile.ZipFile(buf, "w", _zipfile.ZIP_DEFLATED) as zf:
                for name, data in files_data:
                    zf.writestr(name, data)
            ext = ".zip"
        elif algorithm == "tar.gz":
            import gzip as _gzip
            with _tarfile.open(fileobj=buf, mode="w:gz") as tf:
                for name, data in files_data:
                    info = _tarfile.TarInfo(name=name)
                    info.size = len(data)
                    tf.addfile(info, _io.BytesIO(data))
            ext = ".tar.gz"
        else:
            raise ValueError(f"UNSUPPORTED_ALGORITHM: {algorithm}")

        compressed = buf.getvalue()
        archive_name = f"archive-{secrets.token_hex(4)}{ext}"
        content_sha = hashlib.sha256(compressed).hexdigest()
        _store_file_content("", content_sha, compressed)

        archive_file = File(
            id=f"file-{secrets.token_hex(6)}",
            name=archive_name,
            folder_id="",
            type=ext.lstrip("."),
            size=len(compressed),
            sha256=content_sha,
            content_type="application/" + ("zip" if algorithm == "zip" else "gzip"),
            owner_id=user.id,
            parse_status="queued",
            tags=",压缩文件,",
        )
        await self._files.create(archive_file)
        await self._s.commit()

        ratio = round((1 - len(compressed) / max(total_original, 1)) * 100, 1)
        return CompressionResult(
            file_id=archive_file.id, file_name=archive_name,
            original_size=total_original, compressed_size=len(compressed),
            algorithm=algorithm, ratio=ratio,
        )

    async def decompress_file(self, file_id: str, user: UserPublic) -> list[CompressionResult]:
        """Decompress an archive file into individual files."""
        import io as _io
        import zipfile as _zipfile
        import tarfile as _tarfile

        db_file = await self._files.get_by_id(file_id)
        if db_file is None:
            raise ValueError(f"FILE_NOT_FOUND: {file_id}")
        await self._ensure_can_read_file(db_file, user)
        content = _read_file_content(db_file)
        if content is None:
            raise ValueError(f"CONTENT_MISSING: {file_id}")

        results: list[CompressionResult] = []
        buf = _io.BytesIO(content)

        if db_file.name.endswith(".zip"):
            with _zipfile.ZipFile(buf, "r") as zf:
                for name in zf.namelist():
                    data = zf.read(name)
                    sha = hashlib.sha256(data).hexdigest()
                    _store_file_content("", sha, data)
                    new_file = File(
                        id=f"file-{secrets.token_hex(6)}", name=name, folder_id="",
                        type=name.rsplit(".", 1)[-1] if "." in name else "",
                        size=len(data), sha256=sha,
                        content_type="application/octet-stream",
                        owner_id=user.id, parse_status="queued", tags="",
                    )
                    await self._files.create(new_file)
                    results.append(CompressionResult(
                        file_id=new_file.id, file_name=name,
                        original_size=0, compressed_size=len(data),
                        algorithm="extracted", ratio=0,
                    ))
        elif db_file.name.endswith((".tar.gz", ".tgz")):
            with _tarfile.open(fileobj=buf, mode="r:gz") as tf:
                for member in tf.getmembers():
                    if not member.isfile():
                        continue
                    data = tf.extractfile(member)
                    if data is None:
                        continue
                    raw = data.read()
                    sha = hashlib.sha256(raw).hexdigest()
                    _store_file_content("", sha, raw)
                    new_file = File(
                        id=f"file-{secrets.token_hex(6)}", name=member.name, folder_id="",
                        type=member.name.rsplit(".", 1)[-1] if "." in member.name else "",
                        size=len(raw), sha256=sha,
                        content_type="application/octet-stream",
                        owner_id=user.id, parse_status="queued", tags="",
                    )
                    await self._files.create(new_file)
                    results.append(CompressionResult(
                        file_id=new_file.id, file_name=member.name,
                        original_size=0, compressed_size=len(raw),
                        algorithm="extracted", ratio=0,
                    ))
        else:
            raise ValueError(f"UNSUPPORTED_ARCHIVE_TYPE: {db_file.name}")

        await self._s.commit()
        return results

    # ── Permissions / Notifications / Audit ──
    async def _ensure_can_manage_permission_resource(self, resource_type: str, resource_id: str, user: UserPublic) -> None:
        if resource_type == "file":
            file = await self._files.get_by_id(resource_id)
            if not file:
                raise WorkspaceError(404, "PERMISSION_RESOURCE_NOT_FOUND", "权限资源不存在", {"resource_type": resource_type, "resource_id": resource_id})
            team_id = await self._file_team_id(file)
            if team_id:
                member = await self._team_member_for_user(team_id, user)
                if not member or member.role not in {"owner", "admin"}:
                    raise WorkspaceError(403, "PERMISSION_RESOURCE_FORBIDDEN", "没有管理该资源权限规则的权限", {"resource_type": resource_type, "resource_id": resource_id})
                return
            if file.owner_id != user.id:
                raise WorkspaceError(403, "PERMISSION_RESOURCE_FORBIDDEN", "没有管理该资源权限规则的权限", {"resource_type": resource_type, "resource_id": resource_id})
            return
        if resource_type == "folder":
            folder = await self._folders.get_by_id(resource_id)
            if not folder:
                raise WorkspaceError(404, "PERMISSION_RESOURCE_NOT_FOUND", "权限资源不存在", {"resource_type": resource_type, "resource_id": resource_id})
            if folder.scope == "team":
                member = await self._team_member_for_user(folder.team_id, user)
                if not member or member.role not in {"owner", "admin"}:
                    raise WorkspaceError(403, "PERMISSION_RESOURCE_FORBIDDEN", "没有管理该资源权限规则的权限", {"resource_type": resource_type, "resource_id": resource_id})
                return
            if folder.owner_id not in {None, user.id}:
                raise WorkspaceError(403, "PERMISSION_RESOURCE_FORBIDDEN", "没有管理该资源权限规则的权限", {"resource_type": resource_type, "resource_id": resource_id})
            return
        if resource_type == "team":
            await self._ensure_team_admin(resource_id, user)
            return
        if resource_type == "knowledge_base":
            await self._ensure_kb_access(resource_id, user, manage=True)
            return
        if resource_type == "workflow":
            await self._ensure_workflow_access(resource_id, user, manage=True)
            return
        if resource_type == "tool":
            tools = await self.list_tools()
            if resource_id not in {tool.id for tool in tools} and resource_id not in {tool.name for tool in tools}:
                raise WorkspaceError(404, "PERMISSION_RESOURCE_NOT_FOUND", "权限资源不存在", {"resource_type": resource_type, "resource_id": resource_id})
            return
        raise WorkspaceError(422, "PERMISSION_RESOURCE_INVALID", "资源类型不支持", {"resource_type": resource_type})

    async def _can_manage_permission_resource(self, resource_type: str, resource_id: str, user: UserPublic) -> bool:
        try:
            await self._ensure_can_manage_permission_resource(resource_type, resource_id, user)
        except (ValueError, WorkspaceError):
            return False
        return True

    async def list_permission_rules(self, user: UserPublic) -> list[PermissionRulePublic]:
        rules = await self._perms.list_all()
        visible_rules = []
        for rule in rules:
            if await self._can_manage_permission_resource(rule.resource_type, rule.resource_id, user):
                visible_rules.append(rule)
        return [
            PermissionRulePublic(
                id=r.id,
                subject_type=r.subject_type,
                subject_id=r.subject_id,
                subject_label=r.subject_id,
                resource_type=r.resource_type,
                resource_id=r.resource_id,
                resource_label=r.resource_id,
                action=r.action,
                effect=r.effect,
                inherit=r.inherit,
                created_at=r.created_at,
                created_by=user.username,
            )
            for r in visible_rules
        ]

    async def create_permission_rule(self, payload: Any, user: UserPublic) -> PermissionRulePublic:
        import secrets as _s
        await self._ensure_can_manage_permission_resource(
            getattr(payload, "resource_type", "file"),
            getattr(payload, "resource_id", ""),
            user,
        )
        rid = f"rule-{_s.token_hex(4)}"
        r = PermissionRule(id=rid, subject_type=getattr(payload, "subject_type", "user"),
                           subject_id=getattr(
                               payload, "subject_id", str(user.id)),
                           resource_type=getattr(
                               payload, "resource_type", "file"),
                           resource_id=getattr(payload, "resource_id", ""),
                           action=getattr(payload, "action", "read"),
                           effect=getattr(payload, "effect", "allow"),
                           inherit=getattr(payload, "inherit", False), priority=0)
        await self._perms.create(r)
        await self._s.commit()
        return PermissionRulePublic(
            id=rid,
            subject_type=r.subject_type,
            subject_id=r.subject_id,
            subject_label=getattr(payload, "subject_id", str(user.id)),
            resource_type=r.resource_type,
            resource_id=r.resource_id,
            resource_label=r.resource_id,
            action=r.action,
            effect=r.effect,
            inherit=r.inherit,
            created_at=r.created_at,
            created_by=user.username,
        )

    async def delete_permission_rule(self, rule_id: str, user: UserPublic) -> None:
        r = await self._perms.get_by_id(rule_id)
        if r:
            await self._ensure_can_manage_permission_resource(r.resource_type, r.resource_id, user)
            await self._perms.delete(r)
            await self._s.commit()

    async def _append_file_version(self, f: File, content: bytes, user: UserPublic) -> FileVersion:
        existing = await self._versions.list_by_file(f.id)
        next_version_no = max((version.version_no for version in existing), default=0) + 1
        digest = hashlib.sha256(content).hexdigest()
        _store_file_content(f.id, digest, content)
        version = FileVersion(
            id=f"version-{secrets.token_hex(8)}",
            file_id=f.id,
            version_no=next_version_no,
            name=f.name,
            size=len(content),
            sha256=digest,
            content_key=digest,
            created_by=user.username,
        )
        return await self._versions.create(version)

    async def list_notifications(self, user: UserPublic) -> list[NotificationItem]:
        notifs = await self._notifs.list_by_user(user.id)
        return [NotificationItem(id=n.id, user_id=n.user_id, type=n.type, title=n.title, content=n.content, target_type=n.target_type, target_id=n.target_id, is_read=n.is_read, created_at=str(n.created_at)) for n in notifs]

    async def mark_notification_read(self, notification_id: str, user: UserPublic) -> NotificationItem:
        n = await self._notifs.get_by_id(notification_id)
        if n:
            n.is_read = True
            await self._s.commit()
        return NotificationItem(id=notification_id, user_id=user.id, type=n.type if n else "system", title=n.title if n else "", content=n.content if n else "", target_type=n.target_type if n else "", target_id=n.target_id if n else "", is_read=True, created_at=str(n.created_at) if n else "")

    async def list_audit_logs(self) -> list[AuditLogEntry]:
        logs = await self._audit.list_recent(50)
        return [AuditLogEntry(id=str(log.id), actor=log.actor, action=log.action, resource_type=log.resource_type, resource_name=log.resource_name, created_at=str(log.created_at)) for log in logs]

    # ── Workspace snapshot ──
    async def snapshot(self, user: UserPublic) -> WorkspaceSnapshot:
        import json as _json
        all_folders = await self._folders.list_all()
        team_ids_snap = set()
        for t in await self._teams.list_all():
            try:
                tms = await self._members.list_by_team(t.id)
                if any(m.user_id == user.id and m.status == "active" for m in tms):
                    team_ids_snap.add(t.id)
            except Exception:
                pass
        files = [
            f for f in await self._files.list_all()
            if f.owner_id is None or f.owner_id == user.id or (f.team_id and f.team_id in team_ids_snap)
        ]
        folders = [f for f in all_folders if f.owner_id is None or f.owner_id ==
                   user.id or (f.team_id and f.team_id in team_ids_snap)]
        teams_db = await self._teams.list_all()
        team_summaries = []
        for t in teams_db:
            members = [m for m in (await _safe_list_members(self, t.id)) if m.status == "active"]
            my_member = next((m for m in members if m.user_id == user.id), None)
            # Only include teams the user is an active member of
            if my_member is None:
                continue
            team_summaries.append({"id": t.id, "name": t.name, "role": my_member.role, "member_count": len(
                members), "unread_count": 0})
        workflows_db = [
            workflow for workflow in await self._workflows.list_all()
            if self._can_read_workflow(workflow, user)
        ]
        workflow_defs = []
        for w in workflows_db:
            try:
                nodes = _json.loads(w.nodes) if w.nodes else []
            except Exception:
                nodes = []
            try:
                edges = _json.loads(w.edges) if w.edges else []
            except Exception:
                edges = []
            workflow_defs.append({"id": w.id, "name": w.name, "description": w.description or "",
                                  "trigger": w.trigger, "version": w.version, "status": w.status,
                                  "node_count": len(nodes), "nodes": nodes, "edges": edges})
        tools_real = await self.list_tools()
        indexed_count = sum(1 for f in files if f.parse_status == "indexed")
        kbs = await self._kbs.list_all()
        audit_entries = await self._audit.list_recent(50)
        recent_audit = [{"id": str(a.id), "actor": a.actor, "action": a.action,
                          "resource_type": a.resource_type, "resource_name": a.resource_name or "",
                          "resource_id": "",
                          "detail": {}, "created_at": a.created_at.isoformat() if a.created_at else ""}
                        for a in (audit_entries or [])]
        notifs = await self._notifs.list_by_user(user.id)
        unread_count = len([n for n in notifs if not getattr(n, 'read', False)])
        return WorkspaceSnapshot(
            files=[_file_to_item(f) for f in files],
            folders=[_folder_to_item(f) for f in folders],
            tools=tools_real, workflows=workflow_defs, teams=team_summaries,
            audit_logs=recent_audit,
            summary={"file_count": len(files), "indexed_count": indexed_count,
                     "knowledge_base_count": len(kbs), "running_workflows": sum(1 for w in workflows_db if w.status == "published"),
                     "unread_notifications": unread_count, "tools_enabled": sum(1 for t in tools_real if t.enabled),
                     "total_files": len(files), "total_folders": len(folders)},
        )

    # ── Debug (FR-W07) ──
    async def start_debug(self, workflow_id: str, payload: dict, user: UserPublic) -> dict:
        """Start a debug session over the workflow's real topological order."""
        import json as _json
        wf = await self._ensure_workflow_access(workflow_id, user)
        if wf.status != "published":
            raise WorkspaceError(409, "WORKFLOW_NOT_PUBLISHED", "流程尚未发布，不能调试", {"workflow_id": workflow_id})
        nodes = _json.loads(wf.nodes) if wf.nodes else []
        edges = _json.loads(wf.edges) if wf.edges else []
        ordered_nodes = self._workflow_topological_order(nodes, edges)
        if ordered_nodes is None:
            raise WorkspaceError(409, "WORKFLOW_INVALID", "流程包含环路，不能调试", {"workflow_id": workflow_id})
        if not ordered_nodes:
            raise WorkspaceError(409, "WORKFLOW_EMPTY", "流程没有可调试节点", {"workflow_id": workflow_id})
        import secrets as _s
        sid = f"debug-{_s.token_hex(4)}"
        await self._workflow_debug_sessions.create(WorkflowDebugSession(
            id=sid,
            workflow_id=workflow_id,
            owner_id=user.id,
            cursor=0,
            nodes_json=_json.dumps(ordered_nodes, ensure_ascii=False),
            edges_json=_json.dumps(edges, ensure_ascii=False),
            inputs_json=_json.dumps(self._workflow_payload_inputs(payload), ensure_ascii=False),
            node_outputs_json="{}",
            results_json="[]",
            expires_at=datetime.now(UTC) + timedelta(minutes=30),
        ))
        await self._s.commit()
        return {"session_id": sid, "status": "ready", "node_count": len(ordered_nodes)}

    async def step_debug(self, session_id: str, workflow_id: str, user: UserPublic) -> dict:
        """Execute the next real node using the same parameter/tool semantics as a normal run."""
        session = await self._workflow_debug_sessions.get_by_id(session_id)
        if not session or session.workflow_id != workflow_id or session.owner_id != user.id:
            raise WorkspaceError(404, "DEBUG_SESSION_NOT_FOUND", "调试会话不存在或已结束", {"session_id": session_id})
        expires_at = session.expires_at if session.expires_at.tzinfo else session.expires_at.replace(tzinfo=UTC)
        if datetime.now(UTC) >= expires_at:
            await self._workflow_debug_sessions.delete(session)
            await self._s.commit()
            raise WorkspaceError(410, "DEBUG_SESSION_EXPIRED", "调试会话已过期", {"session_id": session_id})
        lease_token = f"lease-{secrets.token_hex(12)}"
        now = datetime.now(UTC)
        claimed = await self._workflow_debug_sessions.claim(
            session_id, user.id, lease_token, now, now + timedelta(minutes=2)
        )
        if not claimed:
            raise WorkspaceError(409, "DEBUG_STEP_IN_PROGRESS", "已有调试步骤正在执行，请稍后重试", {"session_id": session_id})
        self._s.expire_all()
        session = await self._workflow_debug_sessions.get_by_id(session_id)
        if not session or session.workflow_id != workflow_id:
            raise WorkspaceError(404, "DEBUG_SESSION_NOT_FOUND", "调试会话不存在或已结束", {"session_id": session_id})
        cursor = session.cursor
        nodes = _json_loads_list(session.nodes_json)
        edges = _json_loads_list(session.edges_json)
        node_outputs = _json_loads_object(session.node_outputs_json)
        results = _json_loads_list(session.results_json)
        if cursor >= len(nodes):
            await self._workflow_debug_sessions.delete(session)
            await self._s.commit()
            return {
                "done": True, "step": len(results), "node_id": "", "node_name": "",
                "status": "success", "input": {}, "output": {}, "remaining": 0,
            }
        node = nodes[cursor]
        workflow_inputs = _json_loads_object(session.inputs_json)
        if self._workflow_node_is_active(str(node.get("id") or ""), edges, node_outputs):
            try:
                execution = await self._execute_workflow_node(node, edges, node_outputs, workflow_inputs, user)
            except Exception:
                await self._s.rollback()
                await self._workflow_debug_sessions.release(session_id, lease_token)
                raise
        else:
            execution = self._workflow_skipped_node(node)
        node_id = execution["node_id"]
        status = execution["status"]
        results.append(execution)
        session.cursor = cursor + 1
        session.node_outputs_json = json.dumps(node_outputs, ensure_ascii=False)
        session.results_json = json.dumps(results, ensure_ascii=False)
        next_cursor = session.cursor
        done = status == "failed" or next_cursor >= len(nodes)
        if done:
            await self._workflow_debug_sessions.delete(session)
        else:
            session.lease_token = None
            session.lease_expires_at = None
            await self._workflow_debug_sessions.update(session)
        await self._s.commit()
        return {
            "done": done,
            "step": session.cursor,
            "node_id": node_id,
            "node_name": execution["name"],
            "status": status,
            "input": execution["input"],
            "output": execution["output"],
            "remaining": 0 if done else len(nodes) - next_cursor,
        }

    async def cancel_debug(self, session_id: str, workflow_id: str, user: UserPublic) -> None:
        await self._ensure_workflow_access(workflow_id, user)
        session = await self._workflow_debug_sessions.get_by_id(session_id)
        if not session or session.workflow_id != workflow_id or session.owner_id != user.id:
            raise WorkspaceError(404, "DEBUG_SESSION_NOT_FOUND", "调试会话不存在或已结束", {"session_id": session_id})
        lease_expires_at = session.lease_expires_at
        if lease_expires_at and lease_expires_at.tzinfo is None:
            lease_expires_at = lease_expires_at.replace(tzinfo=UTC)
        if session.lease_token and lease_expires_at and lease_expires_at > datetime.now(UTC):
            raise WorkspaceError(409, "DEBUG_STEP_IN_PROGRESS", "调试步骤正在执行，暂不能取消", {"session_id": session_id})
        await self._workflow_debug_sessions.delete(session)
        await self._s.commit()


def _file_type(name: str) -> str:
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return ext


def _file_to_item(f: File) -> FileItem:
    return FileItem(id=f.id, name=f.name, folder_id=f.folder_id, type=f.type, size=f.size, sha256=f.sha256, content_type=f.content_type, permission_scope=f.permission_scope, parse_status=f.parse_status, tags=f.tags.split(",") if f.tags else [], knowledge_base_ids=f.knowledge_base_ids.split(",") if f.knowledge_base_ids else [], updated_at=f.updated_at.isoformat(), created_at=f.created_at.isoformat(), created_by=f.created_by)


def _folder_to_item(f: Folder) -> FolderItem:
    return FolderItem(id=f.id, name=f.name, parent_id=f.parent_id, scope=f.scope, permission=f.scope, children=[])


def _build_tree(folders: list[Folder]) -> list[FolderItem]:
    items = {f.id: _folder_to_item(f) for f in folders}
    roots = []
    for f in folders:
        item = items[f.id]
        if f.parent_id and f.parent_id in items:
            items[f.parent_id].children.append(item)
        else:
            roots.append(item)
    return roots
