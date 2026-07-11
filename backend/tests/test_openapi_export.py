from __future__ import annotations
import json
from app.openapi_export import export_openapi

def test_export_openapi_writes_v2_contract(tmp_path) -> None:
    output_path = tmp_path / "workspace.openapi.json"
    export_openapi(output_path)
    schema = json.loads(output_path.read_text(encoding="utf-8"))
    paths = schema["paths"]
    assert schema["info"]["title"] == "WHU API v2"
    assert schema["servers"] == [{"url": "/"}]
    assert "/api/v2/workspace/snapshot" in paths
    assert "/api/v2/auth/register" in paths
    assert "/api/v2/auth/login" in paths
    assert "/api/v2/files" in paths
    assert "/api/v2/files/upload" in paths
    assert "/api/v2/files/{file_id}" in paths
    assert "/api/v2/files/{file_id}/download" in paths
    assert "/api/v2/files/{file_id}/restore" in paths
    assert "/api/v2/files/recycle-bin" in paths
    assert "/api/v2/folders/tree" in paths
    assert "/api/v2/teams" in paths
    assert "/api/v2/knowledge-bases" in paths
    assert "/api/v2/knowledge-bases/{kb_id}" in paths
    assert "/api/v2/knowledge-bases/{kb_id}/files" in paths
    assert "/api/v2/knowledge-bases/{kb_id}/files:batch-add" in paths
    assert "/api/v2/knowledge-bases/{kb_id}/files:batch-remove" in paths
    assert "/api/v2/knowledge-bases/{kb_id}/reindex" in paths
    assert "/api/v2/knowledge-bases/{kb_id}/conversations" in paths
    assert "/api/v2/conversations/{conversation_id}" in paths
    assert "delete" in paths["/api/v2/conversations/{conversation_id}"]
    assert "/api/v2/tools" in paths
    assert "/api/v2/agents/tasks" in paths
    assert "get" in paths["/api/v2/agents/tasks"]
    assert "post" in paths["/api/v2/agents/tasks"]
    assert "/api/v2/agents/tasks/plan" in paths
    assert "/api/v2/agents/tasks/stream" in paths
    assert "/api/v2/agents/tasks/{task_id}" in paths
    assert "delete" in paths["/api/v2/agents/tasks/{task_id}"]
    assert "/api/v2/agents/tasks/{task_id}/continue" in paths
    assert "/api/v2/agents/tasks/{task_id}/cancel" in paths
    assert "/api/v2/workflows" in paths
    assert "/api/v2/notifications" in paths
    assert "/api/v2/permissions/rules" in paths
    assert "/api/v2/health" in paths
