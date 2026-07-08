from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
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
    FileItem,
    FolderItem,
    QARequest,
    QAResponse,
    TeamSummary,
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


@dataclass
class StoredUser:
    public: UserPublic
    password_hash: str


class WorkspaceService:
    def __init__(self) -> None:
        self._secret = "dev-workspace-secret"
        self._users_by_id: dict[int, StoredUser] = {}
        self._users_by_username: dict[str, StoredUser] = {}
        self._users_by_email: dict[str, StoredUser] = {}
        self._next_user_id = 1
        self._files = self._seed_files()
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
        if not stored or not hmac.compare_digest(stored.password_hash, self._hash_password(password)):
            raise WorkspaceError(401, "INVALID_CREDENTIALS", "用户名、邮箱或密码不正确")
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

    def folder_tree(self) -> list[FolderItem]:
        return [
            FolderItem(
                id="personal-root",
                name="个人文件",
                scope="personal",
                permission="管理",
                children=[
                    FolderItem(id="folder-biology", name="生物学实验", parent_id="personal-root", scope="personal", permission="管理"),
                    FolderItem(id="folder-course", name="软件工程课程", parent_id="personal-root", scope="personal", permission="管理"),
                ],
            ),
            FolderItem(id="team-root", name="团队文件", scope="team", permission="读写"),
        ]

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
        content = await upload.read()
        digest = hashlib.sha256(content).hexdigest()
        clean_tags = [tag.strip() for tag in (tags or "").split(",") if tag.strip()]
        file_type = self._file_type(upload.filename or "")
        item = FileItem(
            id=f"file-{digest[:12]}",
            name=upload.filename or "未命名文件",
            folder_id=folder_id,
            type=file_type,
            size=len(content),
            sha256=digest,
            parse_status="queued",
            tags=clean_tags,
            updated_at=datetime.now(UTC),
            permission_scope="个人",
            knowledge_base_ids=[],
        )
        self._files.insert(0, item)
        self._record_audit(actor.username, "file.upload", "file", item.name)
        return item

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

    def list_teams(self) -> list[TeamSummary]:
        return [
            TeamSummary(id="team-biology", name="生物学实验", role="团队管理员", member_count=6, unread_count=3),
            TeamSummary(id="team-course", name="软件工程课程组", role="成员", member_count=5, unread_count=1),
        ]

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

    def snapshot(self) -> WorkspaceSnapshot:
        files = self.list_files()
        return WorkspaceSnapshot(
            summary=DashboardSummary(
                file_count=len(files),
                indexed_count=sum(1 for file in files if file.parse_status == "indexed"),
                knowledge_base_count=2,
                running_workflows=0,
                unread_notifications=sum(team.unread_count for team in self.list_teams()),
                tools_enabled=sum(1 for tool in self.list_tools() if tool.enabled),
            ),
            files=files[:5],
            tools=self.list_tools(),
            workflows=self.list_workflows(),
            teams=self.list_teams(),
            audit_logs=self.list_audit_logs(),
        )

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

    def _find_file(self, file_id: str) -> FileItem:
        for file_item in self._files:
            if file_item.id == file_id:
                return file_item
        raise WorkspaceError(404, "FILE_NOT_FOUND", "文件不存在或无权访问", {"file_id": file_id})

    def _file_type(self, filename: str) -> str:
        suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else "unknown"
        return {"md": "markdown", "txt": "text", "pdf": "pdf", "docx": "docx", "pptx": "pptx", "csv": "csv"}.get(
            suffix, suffix
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


workspace_service = WorkspaceService()
