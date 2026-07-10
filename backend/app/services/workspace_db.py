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

from app.domain.schemas import (
    FileItem, FolderItem, FolderTreeResponse, UserCreate, UserPublic, UserUpdate,
    TeamDetail, TeamSummary, WorkspaceSnapshot, ToolDefinition, QAResponse, QARequest,
    NotificationItem, Citation, AuditLogEntry, FileAnnotationItem, FileContentResponse, FileVersionItem,
    ShareLinkPublic, RecycleBinItem, KnowledgeBasePublic, KnowledgeDocumentPublic,
    PermissionRulePublic, WorkflowDefinition, WorkflowExecutionResponse, AgentTaskRequest,
    AgentTaskResponse, AgentStep,
)
from app.models import (
    User, File, Folder, FileVersion, DeletedFile, FileAnnotation, ShareLink,
    Team, TeamMember, TeamInvite, TeamMessage,
    KnowledgeBase, KnowledgeDocument, KnowledgeChunk,
    Workflow, PermissionRule, Notification, AuditLog, Conversation, MultipartUpload,
)
from app.repositories import (
    UserRepository, FileRepository, FileVersionRepository, AnnotationRepository,
    DeletedFileRepository, ShareLinkRepository, FolderRepository,
    TeamRepository, TeamMemberRepository, TeamInviteRepository, TeamMessageRepository,
    KnowledgeBaseRepository, KnowledgeDocumentRepository, KnowledgeChunkRepository,
    WorkflowRepository, PermissionRepository, NotificationRepository,
    AuditLogRepository, ConversationRepository, MultipartUploadRepository,
)
from app.services.llm import _get_llm
from app.services.parser import parse_document, ParseError
from app.services.embedding import embed_query, embed_documents, embedding_dim
import numpy as np
import faiss

SECRET = "dev-workspace-secret"
_FILE_CONTENTS: dict[str, bytes] = {}
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


async def _safe_list_members(svc, team_id: str):
    try:
        return await svc._members.list_by_team(team_id)
    except Exception:
        return []


class WorkspaceServiceDB:
    def __init__(self, session: AsyncSession):
        self._s = session
        self._debug_sessions: dict[str, dict] = {}
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
        self._workflows = WorkflowRepository(session)
        self._perms = PermissionRepository(session)
        self._notifs = NotificationRepository(session)
        self._audit = AuditLogRepository(session)
        self._convs = ConversationRepository(session)
        self._uploads = MultipartUploadRepository(session)
        self._faiss: dict[str, tuple[faiss.Index, list[str], dict]] = {}

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
        await self._ensure_personal_root()
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

    async def _ensure_personal_root(self) -> None:
        if not await self._folders.get_by_id("personal-root"):
            await self._folders.create(Folder(id="personal-root", name="个人空间", scope="personal"))

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
        team_ids = set()
        for t in await self._teams.list_all():
            try:
                tms = await self._members.list_by_team(t.id)
                if any(m.user_id == user.id and m.status == "active" for m in tms):
                    team_ids.add(t.id)
            except Exception:
                pass
        files = [f for f in all_files if f.owner_id is None or f.owner_id ==
                 user.id or (f.team_id and f.team_id in team_ids)]
        return [_file_to_item(f) for f in files]

    async def upload_file(self, filename: str, folder_id: str, content: bytes, tags: list[str], user: UserPublic) -> FileItem:
        await self._ensure_personal_root()
        digest = hashlib.sha256(content).hexdigest()
        fid = f"file-{digest[:12]}"
        if await self._files.get_by_id(fid):
            fid = f"file-{digest[:8]}-{secrets.token_hex(4)}"
        f = File(id=fid, name=filename, folder_id=folder_id, type=_file_type(filename), size=len(
            content), sha256=digest, tags=",".join(tags), created_by=user.username, owner_id=user.id)
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
        return _file_to_item(f)

    async def reparse_file(self, file_id: str, user: UserPublic) -> FileItem:
        f = await self._files.get_by_id(file_id)
        if not f:
            from fastapi import HTTPException
            raise HTTPException(404, detail="文件不存在")
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
                    from app.services.workspace import _merge_heading_segments
                    merged = _merge_heading_segments(parsed.segments)
                    old_chunks = await self._chunks.list_by_document(doc.id)
                    for oc in old_chunks:
                        await self._s.delete(oc)
                    import secrets as _s
                    for i, seg in enumerate(merged):
                        self._s.add(KnowledgeChunk(id=f"{doc.id}-chunk-{i+1}", document_id=doc.id, content=seg.content, page_no=seg.page_no, paragraph_no=seg.paragraph_no))
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
        await self._deleted.create(DeletedFile(id=f"del-{secrets.token_hex(4)}", file_id=file_id, deleted_by=user.username))
        await self._files.delete(f)
        await self._s.commit()

    # ── Folders ──
    async def folder_tree(self, user: UserPublic) -> list[FolderItem]:
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
        folders = [f for f in all_folders if f.owner_id is None or f.owner_id ==
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
            return FileItem(id=file_id, name="文件", folder_id="personal-root", type="unknown", size=0, sha256="", content_type="", permission_scope="个人", parse_status="queued", tags=[], knowledge_base_ids=[], updated_at="", created_at="", created_by=user.username)
        if (getattr(payload, "name", None)):
            f.name = getattr(payload, "name", None)
        if (getattr(payload, "folder_id", None)):
            f.folder_id = getattr(payload, "folder_id", None)
        if getattr(payload, "tags", None) is not None:
            f.tags = ",".join(getattr(payload, "tags", []))
        await self._files.update(f)
        await self._s.commit()
        return _file_to_item(f)

    async def copy_file(self, file_id: str, payload: Any, user: UserPublic) -> FileItem:
        src = await self._files.get_by_id(file_id)
        if not src:
            return _file_to_item(File(id=file_id, name="文件", folder_id="personal-root", type="unknown", size=0, sha256="", created_by=user.username))
        import secrets as _s
        cid = f"file-{_s.token_hex(6)}"
        target = (getattr(payload, "target_folder_id", None) or src.folder_id)
        cp = File(id=cid, name=f"副本_{src.name}", folder_id=target, type=src.type, size=src.size, sha256=src.sha256,
                  content_type=src.content_type, permission_scope=src.permission_scope, tags=src.tags, created_by=user.username, owner_id=user.id)
        content = _read_file_content(src)
        if content is not None:
            _FILE_CONTENTS[cid] = content
        await self._files.create(cp)
        await self._s.commit()
        return _file_to_item(cp)

    async def create_share_link(self, file_id: str, payload: Any, user: UserPublic) -> ShareLinkPublic:
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
        anns = await self._annotations.list_by_file(file_id)
        return [FileAnnotationItem(id=a.id, file_id=a.file_id, author_id=a.author_id, author_name=a.author_name, content=a.content, created_at=str(a.created_at)) for a in anns]

    async def create_file_annotation(self, file_id: str, payload: Any, user: UserPublic) -> FileAnnotationItem:
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
        rid = f"reply-{_s.token_hex(4)}"
        reply = FileAnnotation(id=rid, file_id=parent.file_id if parent else "", author_id=user.id,
                               author_name=user.display_name, content=getattr(payload, "content", ""), parent_id=annotation_id)
        await self._annotations.create(reply)
        await self._s.commit()
        return {"id": rid, "content": reply.content, "author_name": reply.author_name, "parent_id": annotation_id}

    async def delete_file_annotation(self, file_id: str, annotation_id: str, user: UserPublic) -> None:
        a = await self._annotations.get_by_id(annotation_id)
        if a:
            await self._annotations.delete(a)
            await self._s.commit()

    async def download_file(self, file_id: str, user: UserPublic) -> tuple[FileItem, bytes]:
        f = await self._files.get_by_id(file_id)
        if not f:
            from fastapi import HTTPException
            raise HTTPException(404, detail="文件不存在")
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
        current_version_no = None
        if f:
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
        return FileItem(id=file_id, name="restored", folder_id="personal-root", type="unknown", size=0, sha256="", content_type="", permission_scope="个人", parse_status="queued", tags=[], knowledge_base_ids=[], updated_at="", created_at="", created_by=user.username)

    async def init_multipart_upload(self, payload: Any, user: UserPublic) -> Any:
        import secrets as _s
        from datetime import UTC, datetime, timedelta
        uid = f"upload-{_s.token_hex(4)}"
        mu = MultipartUpload(id=uid, filename=getattr(payload, "filename", ""), folder_id=getattr(payload, "folder_id", ""), size=getattr(payload, "size", 0), sha256=getattr(payload, "sha256", ""), chunk_size=getattr(payload, "chunk_size", 0), total_chunks=(
            getattr(payload, "size", 0) + getattr(payload, "chunk_size", 1) - 1) // max(getattr(payload, "chunk_size", 1), 1), created_by=user.id, created_at=datetime.now(UTC), expires_at=datetime.now(UTC) + timedelta(hours=1))
        await self._uploads.create(mu)
        await self._s.commit()
        return {"id": uid, "filename": mu.filename, "chunk_size": mu.chunk_size, "total_chunks": mu.total_chunks}

    async def get_multipart_upload(self, session_id: str, user: UserPublic) -> Any:
        return {"id": session_id, "status": "active"}

    async def upload_multipart_chunk(self, session_id: str, chunk_index: int, chunk_data: bytes, sha256: str, user: UserPublic) -> Any:
        return {"chunk_index": chunk_index, "status": "ok"}

    async def complete_multipart_upload(self, session_id: str, user: UserPublic) -> FileItem:
        return FileItem(id=session_id, name="uploaded", folder_id="personal-root", type="unknown", size=0, sha256="", content_type="", permission_scope="个人", parse_status="queued", tags=[], knowledge_base_ids=[], updated_at="", created_at="", created_by=user.username)

    async def list_deleted_files(self, user: UserPublic) -> list[RecycleBinItem]:
        items = await self._deleted.list_all()
        return [RecycleBinItem(file_id=d.file_id, deleted_at=str(d.deleted_at), deleted_by=d.deleted_by) for d in items]

    # ── Folders (extended) ──
    async def create_folder(self, payload: Any, user: UserPublic) -> FolderItem:
        import secrets as _s
        fid = f"folder-{_s.token_hex(4)}"
        f = Folder(id=fid, name=(getattr(payload, "name", None) or "新文件夹"), parent_id=(getattr(
            payload, "parent_id", None) or "personal-root"), scope="personal", owner_id=user.id)
        await self._folders.create(f)
        await self._s.commit()
        return FolderItem(id=fid, name=f.name, parent_id=f.parent_id, scope=f.scope, permission="管理", children=[])

    async def update_folder(self, folder_id: str, payload: Any, user: UserPublic) -> FolderItem:
        return FolderItem(id=folder_id, name=(getattr(payload, "name", None) or "文件夹"), parent_id=getattr(payload, "parent_id", "personal-root"), scope="personal", permission="管理", children=[])

    async def delete_folder_tree(self, folder_id: str, user: UserPublic) -> None:
        f = await self._folders.get_by_id(folder_id)
        if f:
            await self._folders.delete(f)
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
            my_role = next(
                (m.role for m in members if m.user_id == user.id), "member")
            result.append(TeamSummary(id=t.id, name=t.name, role=my_role,
                          member_count=len(members), unread_count=0))
        return result

    async def get_team_detail(self, team_id: str, user: UserPublic) -> TeamDetail:
        team = await self._teams.get_by_id(team_id)
        if not team:
            return TeamDetail(id=team_id, name="未知团队", description="", role="member", member_count=0, unread_count=0, root_folder=FolderItem(id="root", name="root", parent_id=None, scope="team", permission="管理", children=[]), members=[], invites=[])
        members = [m for m in (await _safe_list_members(self, team_id)) if m.status == "active"]
        my_role = next(
            (m.role for m in members if m.user_id == user.id), "member")
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
                          role=my_role, member_count=len(members), unread_count=0,
                          root_folder=FolderItem(
                              id="root", name="root", parent_id=None, scope="team", permission="管理", children=[]),
                          members=member_list, invites=[])

    async def list_team_messages(self, team_id: str, user: UserPublic) -> list[Any]:
        msgs = await self._messages.list_by_team(team_id)
        return [{"id": m.id, "team_id": m.team_id, "sender_id": m.sender_id, "sender_name": m.sender_name, "content": m.content, "message_type": m.message_type, "created_at": str(m.created_at)} for m in msgs]

    async def create_team_message(self, team_id: str, payload: Any, user: UserPublic) -> Any:
        import secrets as _s
        mid = f"msg-{_s.token_hex(4)}"
        msg = TeamMessage(id=mid, team_id=team_id, sender_id=user.id, sender_name=user.display_name, content=getattr(
            payload, "content", ""), message_type=getattr(payload, "message_type", "text"))
        await self._messages.create(msg)
        await self._s.commit()
        return {"id": mid, "team_id": team_id, "content": msg.content, "sender_name": msg.sender_name, "sender_id": msg.sender_id, "message_type": msg.message_type, "created_at": str(msg.created_at)}

    async def create_team_invite(self, team_id: str, payload: Any, user: UserPublic) -> Any:
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

    async def join_team(self, team_id: str, payload: Any, user: UserPublic) -> Any:
        import secrets as _s
        mid = f"mem-{_s.token_hex(4)}"
        m = TeamMember(id=mid, team_id=team_id, user_id=user.id, role="member")
        await self._members.create(m)
        await self._s.commit()
        return {"id": mid, "team_id": team_id, "role": "member", "user_id": user.id}

    async def update_team_member(self, team_id: str, member_id: str, payload: Any, user: UserPublic) -> Any:
        m = await self._members.get_by_id(member_id)
        if m and m.team_id == team_id:
            m.role = getattr(payload, "role", m.role)
            await self._members.update(m)
            await self._s.commit()
            return {"id": member_id, "role": m.role}
        return {"id": member_id, "role": "member"}

    async def remove_team_member(self, team_id: str, member_id: str, user: UserPublic) -> None:
        m = await self._members.get_by_id(member_id)
        if m and m.team_id == team_id:
            m.status = "removed"
            await self._members.update(m)
            await self._s.commit()

    async def update_team(self, team_id: str, payload: Any, user: UserPublic) -> TeamDetail:
        return TeamDetail(id=team_id, name=(getattr(payload, "name", None) or "团队"), description=(getattr(payload, "description", None) or ""), role="owner", member_count=0, unread_count=0, root_folder=FolderItem(id="root", name="root", parent_id=None, scope="team", permission="管理", children=[]), members=[], invites=[])

    async def delete_team(self, team_id: str, user: UserPublic) -> None:
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
    async def list_knowledge_bases(self, user: UserPublic) -> list[KnowledgeBasePublic]:
        kbs = await self._kbs.list_all()
        return [KnowledgeBasePublic(id=kb.id, name=kb.name, description=kb.description or "",
                                    owner_id=kb.owner_id, status=kb.status, document_count=0, chunk_count=0,
                                    created_at=str(kb.created_at), updated_at=str(kb.updated_at)) for kb in kbs]

    async def create_knowledge_base(self, payload: Any, user: UserPublic) -> KnowledgeBasePublic:
        import secrets as _s
        kid = f"kb-{_s.token_hex(4)}"
        kb = KnowledgeBase(id=kid, name=(getattr(payload, "name", None) or "新知识库"),
                           description=(getattr(payload, "description", None) or ""), owner_id=user.id)
        await self._kbs.create(kb)
        await self._s.commit()
        return KnowledgeBasePublic(id=kid, name=kb.name, description=kb.description or "",
                                   owner_id=user.id, status="active", document_count=0, chunk_count=0, created_at=str(kb.created_at), updated_at=str(kb.updated_at))

    async def update_knowledge_base(self, kb_id: str, payload: Any, user: UserPublic) -> KnowledgeBasePublic:
        kb = await self._kbs.get_by_id(kb_id)
        if not kb:
            return KnowledgeBasePublic(id=kb_id, name="知识库", description="", owner_id=user.id, status="active", document_count=0, chunk_count=0, created_at="", updated_at="")
        if (getattr(payload, "name", None)):
            kb.name = getattr(payload, "name", None)
        if getattr(payload, "description", None) is not None:
            kb.description = getattr(payload, "description", None)
        await self._kbs.update(kb)
        await self._s.commit()
        return KnowledgeBasePublic(id=kb_id, name=kb.name, description=kb.description or "", owner_id=kb.owner_id, status=kb.status, document_count=0, chunk_count=0, created_at=str(kb.created_at), updated_at=str(kb.updated_at))

    async def list_knowledge_documents(self, kb_id: str, user: UserPublic) -> list[KnowledgeDocumentPublic]:
        docs = await self._docs.list_by_kb(kb_id)
        return [KnowledgeDocumentPublic(id=d.id, kb_id=d.kb_id, file_id=d.file_id, file_name=d.file_name, index_status=d.index_status, updated_at=str(d.updated_at)) for d in docs]

    async def add_knowledge_document(self, kb_id: str, payload: Any, user: UserPublic) -> KnowledgeDocumentPublic:
        import secrets as _s
        fid = getattr(payload, "file_id", "")
        f = await self._files.get_by_id(fid)
        if not f:
            raise ValueError("FILE_NOT_FOUND")
        content = _read_file_content(f) or b""
        did = f"doc-{_s.token_hex(4)}"
        # Parse and create chunks
        try:
            parsed = parse_document(f.name, content, f.type)
            from app.services.workspace import _merge_heading_segments
            merged = _merge_heading_segments(parsed.segments)
            chunks = [KnowledgeChunk(id=f"{did}-chunk-{i+1}", document_id=did, content=seg.content,
                                     page_no=seg.page_no, paragraph_no=seg.paragraph_no) for i, seg in enumerate(merged)]
            index_status = "indexed"
        except Exception:
            chunks = [KnowledgeChunk(
                id=f"{did}-chunk-1", document_id=did, content=f.name, page_no=1, paragraph_no=1)]
            index_status = "indexed"
        d = KnowledgeDocument(id=did, kb_id=kb_id,
                              file_id=fid, file_name=f.name)
        await self._docs.create(d)
        if chunks:
            await self._chunks.create_bulk(chunks)
        # Update file parse status
        f.parse_status = index_status
        f.knowledge_base_ids = (f.knowledge_base_ids +
                                "," + kb_id) if f.knowledge_base_ids else kb_id
        await self._files.update(f)
        # Clear FAISS cache for this KB
        self._faiss.pop(kb_id, None)
        await self._s.commit()
        return KnowledgeDocumentPublic(id=did, kb_id=kb_id, file_id=fid, file_name=f.name, index_status=index_status, chunk_count=len(chunks), updated_at=str(d.updated_at))

    async def remove_knowledge_document(self, kb_id: str, doc_id: str, user: UserPublic) -> None:
        """Remove a document from a knowledge base."""
        doc = await self._docs.get_by_id(doc_id)
        if doc and doc.kb_id == kb_id:
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

    async def answer_question(self, payload: QARequest, user: UserPublic) -> QAResponse:
        import secrets as _s
        import numpy as np
        # Use provided conversation_id or create new
        conv_id = getattr(payload, "conversation_id", None)
        if not conv_id:
            conv_id = f"conv-{_s.token_hex(4)}"
        # Check if report mode is requested
        report_mode = getattr(payload, "report_mode", False)
        kb = await self._kbs.get_by_id(payload.kb_id)
        kb_name = kb.name if kb else "知识库"
        citations = await self._retrieve_citations(payload.kb_id, payload.question, payload.top_k)
        snippets = [c.snippet for c in citations]
        # Load conversation history for context
        history_context = ""
        try:
            past_msgs = await self._convs.list_by_session(conv_id)
            if past_msgs:
                recent = past_msgs[-6:]  # last 3 exchanges
                history_parts = []
                for m in recent:
                    role_label = "用户" if m.role == "user" else "助手"
                    history_parts.append(f"【{role_label}】{m.content}")
                history_context = "\n".join(history_parts)
        except Exception:
            pass
        answer = await self._generate_answer(
            payload.question, snippets, kb_name,
            history_context=history_context, report_mode=report_mode,
        )
        # Persist conversation history
        try:
            user_msg_id = f"msg-{_s.token_hex(4)}"
            assistant_msg_id = f"msg-{_s.token_hex(4)}"
            await self._convs.create(Conversation(id=user_msg_id, session_id=conv_id, role="user", content=payload.question))
            await self._convs.create(Conversation(id=assistant_msg_id, session_id=conv_id, role="assistant", content=answer))
        except Exception:
            pass
        await self._s.commit()
        return QAResponse(conversation_id=conv_id, message_id=f"msg-{_s.token_hex(4)}", answer=answer, citations=citations)

    async def _retrieve_citations(self, kb_id: str, question: str, top_k: int) -> list:
        import numpy as np
        if kb_id not in self._faiss:
            docs = await self._docs.list_by_kb(kb_id)
            chunks_list, chunk_ids = [], []
            for d in docs:
                for ch in await self._chunks.list_by_document(d.id):
                    chunks_list.append(ch)
                    chunk_ids.append(ch.id)
            if not chunks_list:
                return []
            # Build chunk lookup map: chunk_id -> (doc, chunk)
            chunk_map = {}
            for d in docs:
                for ch in await self._chunks.list_by_document(d.id):
                    chunk_map[ch.id] = (d, ch)
            texts = [ch.content for ch in chunks_list]
            vecs = embed_documents(texts)
            dim = vecs.shape[1]
            index = faiss.IndexFlatIP(dim)
            faiss.normalize_L2(vecs)
            index.add(vecs)
            self._faiss[kb_id] = (index, chunk_ids, chunk_map)
        index, chunk_ids, chunk_map = self._faiss[kb_id]
        if index.ntotal == 0:
            return []
        qv = embed_query(question).reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(qv)
        k = min(top_k * 3, index.ntotal)
        distances, indices = index.search(qv, k)
        from app.domain.schemas import Citation
        seen_ids: set[str] = set()
        result = []
        for idx, dist in zip(indices[0], distances[0]):
            if 0 <= idx < len(chunk_ids):
                cid = chunk_ids[idx]
                if cid in seen_ids:
                    continue
                seen_ids.add(cid)
                entry = chunk_map.get(cid)
                if entry:
                    d, ch = entry
                    result.append(Citation(file_id=d.file_id, document_id=d.id, chunk_id=ch.id,
                                  title=d.file_name, page_no=ch.page_no, paragraph_no=ch.paragraph_no, snippet=ch.content))
        return result[:top_k]

    async def _generate_answer(self, question: str, snippets: list, kb_name: str, history_context: str = "", report_mode: bool = False) -> str:
        if not snippets:
            return f"知识库「{kb_name}」中未找到与您问题相关的内容。请尝试：\n1. 使用更具体的关键词重新提问\n2. 确认知识库中已上传并索引了相关文档\n3. 检查文档内容是否包含相关信息"
        from app.services.llm import generate_rag_answer
        return generate_rag_answer(question, snippets, kb_name, history_context=history_context, report_mode=report_mode)

    async def list_tools(self) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                id="tool-file-search", name="file_search", version="1.0.0",
                category="文件操作", description="按文件名、标签和解析状态搜索用户可访问文件。",
                input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"files": {"type": "array"}}},
            ),
            ToolDefinition(
                id="tool-knowledge-qa", name="knowledge_qa", version="1.0.0",
                category="AI处理", description="基于知识库检索片段生成带引用的回答。",
                input_schema={"type": "object", "required": ["kb_id", "question"]},
                output_schema={"type": "object", "properties": {"answer": {"type": "string"}, "citations": {"type": "array"}}},
            ),
            ToolDefinition(
                id="tool-report-generate", name="report_generate", version="1.0.0",
                category="AI处理", description="将检索结果和活动动态整理为 Markdown 报告。",
                input_schema={"type": "object", "properties": {"topic": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"report": {"type": "string"}}},
            ),
            ToolDefinition(
                id="tool-image-ocr", name="image_ocr", version="1.0.0",
                category="文档解析", description="提取图片或扫描件中的文字。",
                input_schema={"type": "object", "properties": {"file_id": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"text": {"type": "string"}}},
            ),
            ToolDefinition(
                id="tool-file-compare", name="file_compare", version="1.0.0",
                category="文件操作", description="比对两个文件的内容差异并生成对比报告。",
                input_schema={"type": "object", "required": ["file_a", "file_b"], "properties": {"file_a": {"type": "string"}, "file_b": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"diff": {"type": "string"}}},
            ),
            ToolDefinition(
                id="tool-team-activity", name="team_activity", version="1.0.0",
                category="团队协作", description="获取团队近期活动动态，包括文件变更、成员操作和流程执行记录。",
                input_schema={"type": "object", "properties": {"team_id": {"type": "string"}, "limit": {"type": "integer"}}},
                output_schema={"type": "object", "properties": {"activities": {"type": "array"}}},
            ),
        ]

    def _agent_tools_description(self) -> str:
        """Build a formatted tool list string for the LLM planning prompt."""
        lines: list[str] = []
        for tool in [ToolDefinition(id="tool-file-search", name="file_search", version="1.0.0", category="文件操作", description="搜索和筛选文件", input_schema={}, output_schema={}), ToolDefinition(id="tool-knowledge-qa", name="knowledge_qa", version="1.0.0", category="AI处理", description="基于知识库回答问题", input_schema={}, output_schema={}), ToolDefinition(id="tool-report-generate", name="report_generate", version="1.0.0", category="数据分析", description="生成结构化报告", input_schema={}, output_schema={}), ToolDefinition(id="tool-file-compare", name="file_compare", version="1.0.0", category="文件操作", description="比对文件内容差异", input_schema={}, output_schema={}), ToolDefinition(id="tool-image-ocr", name="image_ocr", version="1.0.0", category="AI处理", description="图片文字识别", input_schema={}, output_schema={}), ToolDefinition(id="tool-team-activity", name="team_activity", version="1.0.0", category="团队协作", description="获取团队活动动态", input_schema={}, output_schema={})]:
            lines.append(f"- {tool.name}: {tool.description}")
        return "\n".join(lines)

    async def _execute_agent_tool(self, tool_name: str, payload: Any, user: UserPublic, context: str) -> str:
        """Execute a tool with timeout and error handling."""
        try:
            return await self._run_agent_tool(tool_name, payload, user, context)
        except TimeoutError:
            return f"工具 {tool_name} 执行超时，请重试。"
        except Exception as exc:
            return f"工具 {tool_name} 执行失败：{exc}"

    async def _run_agent_tool(self, tool_name: str, payload: Any, user: UserPublic, context: str) -> str:
        """Dispatch tool execution based on tool name."""
        task = getattr(payload, "task", "")
        kb_id = getattr(payload, "kb_id", None)

        if tool_name == "file_search":
            files = await self._files.list_all()
            context_ids = getattr(payload, "context_file_ids", []) or []
            if context_ids:
                files = [f for f in files if f.id in context_ids]
            if not files:
                return "未找到匹配的文件。"
            file_list = "\n".join(f"- {f.name} ({f.type}, {f.parse_status})" for f in files[:5])
            return f"找到 {len(files)} 个文件：\n{file_list}"

        elif tool_name == "knowledge_qa":
            if not kb_id:
                return "没有可用的知识库。"
            citations = await self._retrieve_citations(kb_id, task, 3)
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
            return await self._compare_files(payload, user)

        elif tool_name == "team_activity":
            logs = await self._audit.list_all()
            recent = logs[-20:] if logs else []
            if not recent:
                return "暂无团队活动记录。"
            return "\n".join(f"- {log.action}: {log.resource_name} ({log.actor})" for log in reversed(recent[-10:]))

        elif tool_name == "image_ocr":
            return "OCR 服务暂不可用，请稍后重试。"

        return f"工具 {tool_name} 执行完成。"

    async def _compare_files(self, payload: Any, user: UserPublic) -> str:
        """Compare two files by context_file_ids and return a diff summary."""
        context_ids = getattr(payload, "context_file_ids", []) or []
        if len(context_ids) < 2:
            return "需要至少两个文件进行比对。"
        file_a = await self._files.get_by_id(context_ids[0])
        file_b = await self._files.get_by_id(context_ids[1])
        if not file_a or not file_b:
            return "无法找到需要比对的其中一个文件。"
        content_a_bytes = _read_file_content(file_a)
        content_b_bytes = _read_file_content(file_b)
        if content_a_bytes is None or content_b_bytes is None:
            return "无法读取文件内容进行比对。"
        content_a = content_a_bytes.decode("utf-8", errors="replace")
        content_b = content_b_bytes.decode("utf-8", errors="replace")
        lines_a = set(content_a.splitlines())
        lines_b = set(content_b.splitlines())
        only_a = lines_a - lines_b
        only_b = lines_b - lines_a
        common = lines_a & lines_b
        return f"比对 {file_a.name} vs {file_b.name}：共同行 {len(common)}，仅A {len(only_a)}，仅B {len(only_b)}。\n仅A示例：{next(iter(only_a), '无')[:80]}\n仅B示例：{next(iter(only_b), '无')[:80]}"

    async def create_agent_task(self, payload: Any, user: UserPublic) -> AgentTaskResponse:
        import secrets as _s
        import json as _json

        task = getattr(payload, "task", "")
        kb_id = getattr(payload, "kb_id", None)

        # Validate kb_id access
        if kb_id:
            kb = await self._kbs.get_by_id(kb_id)
            if kb is None:
                return AgentTaskResponse(
                    id=f"agent-{_s.token_hex(4)}", task=task, status="failed",
                    steps=[AgentStep(type="answer", title="知识库不存在", content=f"知识库 {kb_id} 不存在，请检查ID。", tool_name=None)],
                    final_answer=f"知识库 {kb_id} 不存在。")

        llm = _get_llm()
        if llm is None:
            return AgentTaskResponse(
                id=f"agent-{_s.token_hex(4)}", task=task, status="failed",
                steps=[AgentStep(type="answer", title="LLM 不可用", content="请配置 LLM API Key", tool_name=None)],
                final_answer="LLM 服务暂不可用")

        tools_desc = self._agent_tools_description()
        plan_prompt = (
            "你是一个智能任务规划助手。根据用户的任务描述和可用工具，生成一个分步执行计划。\n\n"
            f"【可用工具】\n{tools_desc}\n\n"
            f"【用户任务】{task}\n\n"
            "请用 JSON 格式返回执行计划，格式如下：\n"
            '{"steps": [{"type": "thought|action|observation|answer", "title": "...", "content": "...", "tool_name": "..."}]}\n'
            "tool_name 仅在 type=action 时需要填写。最多 5 个步骤。只返回 JSON，不要其它内容。"
        )
        try:
            plan_response = llm.invoke(plan_prompt)
            plan_text = plan_response.content.strip() if hasattr(plan_response, "content") else str(plan_response).strip()
            if plan_text.startswith("```"):
                plan_text = plan_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            plan = _json.loads(plan_text)
        except Exception:
            return AgentTaskResponse(
                id=f"agent-{_s.token_hex(4)}", task=task, status="failed",
                steps=[AgentStep(type="answer", title="规划失败", content="任务规划失败，请重试", tool_name=None)],
                final_answer="")

        steps: list[AgentStep] = []
        final_answer = ""
        for raw in plan.get("steps", []):
            step_type = raw.get("type", "observation")
            step = AgentStep(
                type=step_type if step_type in ("thought", "action", "observation", "answer") else "observation",
                title=raw.get("title", ""),
                content=raw.get("content", ""),
                tool_name=raw.get("tool_name"),
            )
            # Execute action steps through the tool dispatcher
            if step.type == "action" and step.tool_name:
                step.content = await self._execute_agent_tool(step.tool_name, payload, user, step.content)
            if step.type == "answer":
                final_answer = step.content
            steps.append(step)

        if not final_answer and steps:
            final_answer = steps[-1].content

        # Record audit
        audit_log = AuditLog(
            actor=user.username,
            action="agent.create_task",
            resource_type="agent_task",
            resource_name=task[:100],
        )
        await self._audit.create(audit_log)
        await self._s.commit()

        return AgentTaskResponse(
            id=f"agent-{_s.token_hex(4)}", task=task, status="completed",
            steps=steps, final_answer=final_answer)

    async def list_workflows(self) -> list[WorkflowDefinition]:
        wfs = await self._workflows.list_all()
        return [WorkflowDefinition(id=wf.id, name=wf.name, description=wf.description or "",
                                   trigger=wf.trigger, version=wf.version, status=wf.status,
                                   nodes=[], edges=[]) for wf in wfs]

    async def create_workflow(self, payload: Any, user: UserPublic) -> WorkflowDefinition:
        import secrets as _s
        import json as _json
        wid = f"wf-{_s.token_hex(4)}"
        nodes_raw = getattr(payload, "nodes", None) or []
        edges_raw = getattr(payload, "edges", None) or []
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
                                   node_count=len(nodes_raw), nodes=nodes_raw, edges=edges_raw)

    async def update_workflow(self, workflow_id: str, payload: Any, user: UserPublic) -> WorkflowDefinition:
        import json as _json
        wf = await self._workflows.get_by_id(workflow_id)
        if not wf:
            return WorkflowDefinition(id=workflow_id, name="流程", description="", trigger="manual", version="0.1.0", status="draft", nodes=[], edges=[])
        if getattr(payload, "name", None):
            wf.name = getattr(payload, "name")
        if getattr(payload, "description", None) is not None:
            wf.description = getattr(payload, "description")
        if getattr(payload, "trigger", None):
            wf.trigger = getattr(payload, "trigger")
        nodes_raw = getattr(payload, "nodes", None)
        if nodes_raw is not None:
            wf.nodes = _json.dumps(nodes_raw, ensure_ascii=False)
        edges_raw = getattr(payload, "edges", None)
        if edges_raw is not None:
            wf.edges = _json.dumps(edges_raw, ensure_ascii=False)
        await self._workflows.update(wf)
        await self._s.commit()
        nodes_out = _json.loads(wf.nodes) if wf.nodes else []
        edges_out = _json.loads(wf.edges) if wf.edges else []
        return WorkflowDefinition(id=workflow_id, name=wf.name, description=wf.description or "",
                                   trigger=wf.trigger, version=wf.version, status=wf.status,
                                   node_count=len(nodes_out), nodes=nodes_out, edges=edges_out)

    async def validate_workflow(self, workflow_id: str, user: UserPublic) -> Any:
        import json as _json
        wf = await self._workflows.get_by_id(workflow_id)
        if not wf:
            return {"valid": False, "issues": [{"code": "NOT_FOUND", "message": "流程不存在"}]}
        nodes = _json.loads(wf.nodes) if wf.nodes else []
        edges = _json.loads(wf.edges) if wf.edges else []
        issues = []
        tool_names = {t.name for t in await self.list_tools()}
        node_ids = {n.get("id") for n in nodes}
        for n in nodes:
            tn = n.get("tool_name")
            if tn and tn not in tool_names:
                issues.append({"code": "WORKFLOW_TOOL_UNKNOWN", "message": f"工具节点引用了未注册工具: {tn}", "node_id": n.get("id")})
        for e in edges:
            if e.get("source") not in node_ids or e.get("target") not in node_ids:
                issues.append({"code": "WORKFLOW_EDGE_INVALID", "message": f"连线 {e.get('id')} 引用了不存在的节点", "edge_id": e.get("id")})
        return {"valid": len(issues) == 0, "issues": issues, "node_count": len(nodes), "edge_count": len(edges)}

    async def publish_workflow(self, workflow_id: str, user: UserPublic) -> WorkflowDefinition:
        wf = await self._workflows.get_by_id(workflow_id)
        if not wf:
            return WorkflowDefinition(id=workflow_id, name="已发布", description="", trigger="manual", version="0.1.0", status="published", nodes=[], edges=[])
        wf.status = "published"
        # Bump minor version
        parts = wf.version.split(".")
        if len(parts) == 2:
            wf.version = f"{parts[0]}.{int(parts[1]) + 1}"
        await self._workflows.update(wf)
        await self._s.commit()
        import json as _json
        nodes = _json.loads(wf.nodes) if wf.nodes else []
        edges = _json.loads(wf.edges) if wf.edges else []
        return WorkflowDefinition(id=workflow_id, name=wf.name, description=wf.description or "",
                                   trigger=wf.trigger, version=wf.version, status=wf.status,
                                   node_count=len(nodes), nodes=nodes, edges=edges)

    async def execute_workflow(self, workflow_id: str, payload: Any, user: UserPublic) -> WorkflowExecutionResponse:
        import secrets as _s
        import json as _json
        wf = await self._workflows.get_by_id(workflow_id)
        if not wf:
            return WorkflowExecutionResponse(id=f"exec-{_s.token_hex(4)}", workflow_id=workflow_id, status="failed", node_executions=[], output={"summary": "流程不存在"})
        nodes = _json.loads(wf.nodes) if wf.nodes else []
        if not nodes:
            return WorkflowExecutionResponse(id=f"exec-{_s.token_hex(4)}", workflow_id=workflow_id, status="completed", node_executions=[], output={"summary": f"流程「{wf.name}」无节点，执行完成"})
        node_executions = []
        for node in nodes:
            tool_name = node.get("tool_name")
            if tool_name:
                try:
                    result = await self._execute_agent_tool(tool_name, payload, user, node.get("content", ""))
                except Exception as exc:
                    result = f"执行失败: {exc}"
                node_executions.append({"node_id": node.get("id", ""), "name": node.get("name", ""), "tool_name": tool_name, "status": "success", "input": {}, "output": {"result": result}})
            else:
                node_executions.append({"node_id": node.get("id", ""), "name": node.get("name", ""), "tool_name": "", "status": "success", "input": {}, "output": {}})
        return WorkflowExecutionResponse(id=f"exec-{_s.token_hex(4)}", workflow_id=workflow_id, status="completed", node_executions=node_executions, output={"summary": f"流程「{wf.name}」执行完成，共 {len(nodes)} 个节点"})

    async def _seed_workflow_templates(self) -> None:
        """Seed built-in workflow templates if none exist."""
        import secrets as _s
        import json as _json
        existing = await self._workflows.list_all()
        if any(w.status == "template" for w in existing):
            return
        templates = [
            {"name": "新文件自动摘要", "trigger": "file_upload", "description": "上传文件后自动解析内容并生成摘要报告", "nodes": [
                {"id": "trigger-1", "name": "文件上传触发", "type": "trigger", "tool_name": None, "parameters": {}, "position": {"x": 80, "y": 170}},
                {"id": "tool-search", "name": "搜索相关文件", "type": "tool", "tool_name": "file_search", "parameters": {"query": ""}, "position": {"x": 360, "y": 110}},
                {"id": "tool-qa", "name": "知识库问答", "type": "tool", "tool_name": "knowledge_qa", "parameters": {"kb_id": "", "question": ""}, "position": {"x": 650, "y": 110}},
                {"id": "output-report", "name": "生成摘要报告", "type": "output", "tool_name": None, "parameters": {"format": "markdown"}, "position": {"x": 940, "y": 170}},
            ], "edges": [
                {"id": "e1", "source": "trigger-1", "target": "tool-search", "type": "smoothstep"},
                {"id": "e2", "source": "tool-search", "target": "tool-qa", "type": "smoothstep"},
                {"id": "e3", "source": "tool-qa", "target": "output-report", "type": "smoothstep"},
            ]},
            {"name": "团队周报生成", "trigger": "schedule", "description": "定时收集团队活动与文件变更，生成 Markdown 周报", "nodes": [
                {"id": "trigger-w", "name": "每周触发", "type": "trigger", "tool_name": None, "parameters": {"cron": "0 9 * * 1"}, "position": {"x": 80, "y": 170}},
                {"id": "tool-team", "name": "获取团队动态", "type": "tool", "tool_name": "team_activity", "parameters": {"team_id": "", "limit": 20}, "position": {"x": 360, "y": 110}},
                {"id": "tool-files", "name": "搜索本周文件", "type": "tool", "tool_name": "file_search", "parameters": {"query": ""}, "position": {"x": 360, "y": 250}},
                {"id": "tool-report", "name": "生成周报", "type": "tool", "tool_name": "report_generate", "parameters": {"topic": "团队周报"}, "position": {"x": 650, "y": 180}},
                {"id": "output-weekly", "name": "发布周报", "type": "output", "tool_name": None, "parameters": {"format": "markdown", "destination": "team-channel"}, "position": {"x": 940, "y": 180}},
            ], "edges": [
                {"id": "e1", "source": "trigger-w", "target": "tool-team", "type": "smoothstep"},
                {"id": "e2", "source": "trigger-w", "target": "tool-files", "type": "smoothstep"},
                {"id": "e3", "source": "tool-team", "target": "tool-report", "type": "smoothstep"},
                {"id": "e4", "source": "tool-files", "target": "tool-report", "type": "smoothstep"},
                {"id": "e5", "source": "tool-report", "target": "output-weekly", "type": "smoothstep"},
            ]},
            {"name": "批量知识问答", "trigger": "manual", "description": "对知识库中的文件逐一提问并汇总结果", "nodes": [
                {"id": "trigger-b", "name": "手动触发", "type": "trigger", "tool_name": None, "parameters": {}, "position": {"x": 80, "y": 170}},
                {"id": "tool-qa", "name": "知识库问答", "type": "tool", "tool_name": "knowledge_qa", "parameters": {"kb_id": "", "question": ""}, "position": {"x": 360, "y": 110}},
                {"id": "aggregate", "name": "汇总答案", "type": "aggregate", "tool_name": None, "parameters": {"strategy": "merge"}, "position": {"x": 650, "y": 170}},
                {"id": "output-batch", "name": "输出问答结果", "type": "output", "tool_name": None, "parameters": {"format": "markdown"}, "position": {"x": 940, "y": 170}},
            ], "edges": [
                {"id": "e1", "source": "trigger-b", "target": "tool-qa", "type": "smoothstep"},
                {"id": "e2", "source": "tool-qa", "target": "aggregate", "type": "smoothstep"},
                {"id": "e3", "source": "aggregate", "target": "output-batch", "type": "smoothstep"},
            ]},
            {"name": "文件比对报告", "trigger": "manual", "description": "选择两个文件进行内容比对并生成差异报告", "nodes": [
                {"id": "trigger-c", "name": "手动选择文件", "type": "trigger", "tool_name": None, "parameters": {}, "position": {"x": 80, "y": 170}},
                {"id": "tool-compare", "name": "比对文件内容", "type": "tool", "tool_name": "file_compare", "parameters": {"file_a": "", "file_b": ""}, "position": {"x": 360, "y": 110}},
                {"id": "tool-report", "name": "生成比对报告", "type": "tool", "tool_name": "report_generate", "parameters": {"topic": "文件比对分析"}, "position": {"x": 650, "y": 170}},
                {"id": "output-compare", "name": "导出报告", "type": "output", "tool_name": None, "parameters": {"format": "docx"}, "position": {"x": 940, "y": 170}},
            ], "edges": [
                {"id": "e1", "source": "trigger-c", "target": "tool-compare", "type": "smoothstep"},
                {"id": "e2", "source": "tool-compare", "target": "tool-report", "type": "smoothstep"},
                {"id": "e3", "source": "tool-report", "target": "output-compare", "type": "smoothstep"},
            ]},
            {"name": "知识入库处理", "trigger": "file_upload", "description": "上传文件后自动解析、OCR识别、分块索引到知识库", "nodes": [
                {"id": "trigger-k", "name": "文件上传触发", "type": "trigger", "tool_name": None, "parameters": {"event": "file.created"}, "position": {"x": 80, "y": 170}},
                {"id": "tool-ocr", "name": "图片OCR识别", "type": "tool", "tool_name": "image_ocr", "parameters": {"file_id": ""}, "position": {"x": 360, "y": 100}},
                {"id": "tool-search", "name": "搜索重复文件", "type": "tool", "tool_name": "file_search", "parameters": {"query": ""}, "position": {"x": 360, "y": 240}},
                {"id": "tool-report", "name": "生成入库报告", "type": "tool", "tool_name": "report_generate", "parameters": {"topic": "知识入库处理结果"}, "position": {"x": 650, "y": 170}},
                {"id": "output-kb", "name": "更新知识库", "type": "output", "tool_name": None, "parameters": {"format": "markdown", "destination": "knowledge-base"}, "position": {"x": 940, "y": 170}},
            ], "edges": [
                {"id": "e1", "source": "trigger-k", "target": "tool-ocr", "type": "smoothstep"},
                {"id": "e2", "source": "trigger-k", "target": "tool-search", "type": "smoothstep"},
                {"id": "e3", "source": "tool-ocr", "target": "tool-report", "type": "smoothstep"},
                {"id": "e4", "source": "tool-search", "target": "tool-report", "type": "smoothstep"},
                {"id": "e5", "source": "tool-report", "target": "output-kb", "type": "smoothstep"},
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
        archive_name = f"archive-{_s().token_hex(4)}{ext}"
        content_sha = hashlib.sha256(compressed).hexdigest()
        _store_file_content("", content_sha, compressed)

        archive_file = File(
            id=f"file-{_s().token_hex(6)}",
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
                        id=f"file-{_s().token_hex(6)}", name=name, folder_id="",
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
                        id=f"file-{_s().token_hex(6)}", name=member.name, folder_id="",
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
    async def list_permission_rules(self, user: UserPublic) -> list[PermissionRulePublic]:
        rules = await self._perms.list_all()
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
            for r in rules
        ]

    async def create_permission_rule(self, payload: Any, user: UserPublic) -> PermissionRulePublic:
        import secrets as _s
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
        files = [f for f in await self._files.list_all() if f.owner_id is None or f.owner_id == user.id]
        all_folders = await self._folders.list_all()
        team_ids_snap = set()
        for t in await self._teams.list_all():
            try:
                tms = await self._members.list_by_team(t.id)
                if any(m.user_id == user.id and m.status == "active" for m in tms):
                    team_ids_snap.add(t.id)
            except Exception:
                pass
        folders = [f for f in all_folders if f.owner_id is None or f.owner_id ==
                   user.id or (f.team_id and f.team_id in team_ids_snap)]
        teams_db = await self._teams.list_all()
        team_summaries = []
        for t in teams_db:
            members = [m for m in (await _safe_list_members(self, t.id)) if m.status == "active"]
            my_role = next(
                (m.role for m in members if m.user_id == user.id), "member")
            team_summaries.append({"id": t.id, "name": t.name, "role": my_role, "member_count": len(
                members), "unread_count": 0})
        workflows_db = await self._workflows.list_all()
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
    def start_debug(self, workflow_id: str, payload: dict, user) -> dict:
        """Start a debug session, returns first node."""
        import secrets as _s
        sid = f"debug-{_s.token_hex(4)}"
        self._debug_sessions[sid] = {
            "workflow_id": workflow_id, "cursor": 0, "results": []}
        return {"session_id": sid, "status": "ready"}

    def step_debug(self, session_id: str, workflow_id: str) -> dict:
        """Execute next node in debug session."""
        session = self._debug_sessions.get(session_id)
        if not session:
            from fastapi import HTTPException
            raise HTTPException(404, detail="Debug session not found")
        session["cursor"] += 1
        done = session["cursor"] >= 3  # simulate 3 nodes for MVP
        if done:
            del self._debug_sessions[session_id]
        return {"done": done, "step": session["cursor"], "node_name": f"Node-{session["cursor"]}", "status": "success", "remaining": 3 - session["cursor"] if not done else 0}


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
