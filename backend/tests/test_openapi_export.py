from __future__ import annotations

import json

from app.openapi_export import export_openapi


def test_export_openapi_writes_workspace_contract(tmp_path) -> None:
    output_path = tmp_path / "workspace.openapi.json"

    export_openapi(output_path)

    schema = json.loads(output_path.read_text(encoding="utf-8"))
    assert schema["info"]["title"] == "WHU Intelligent File Workspace API"
    assert schema["info"]["version"] == "0.1.0"
    assert schema["openapi"].startswith("3.")
    assert schema["servers"] == [{"url": "/"}]
    assert "/api/v1/workspace/snapshot" in schema["paths"]
    assert schema["paths"]["/api/v1/workspace/snapshot"]["get"]["operationId"]
    assert "/api/v1/files/{file_id}" in schema["paths"]
    assert schema["paths"]["/api/v1/files/{file_id}"]["patch"]["operationId"]
    assert schema["paths"]["/api/v1/files/{file_id}"]["delete"]["operationId"]
    assert "/api/v1/files/{file_id}/copy" in schema["paths"]
    assert schema["paths"]["/api/v1/files/{file_id}/copy"]["post"]["operationId"]
    assert "/api/v1/files/{file_id}/download" in schema["paths"]
    assert schema["paths"]["/api/v1/files/{file_id}/download"]["get"]["operationId"]
    assert "/api/v1/files/{file_id}/versions" in schema["paths"]
    assert schema["paths"]["/api/v1/files/{file_id}/versions"]["get"]["operationId"]
    assert "/api/v1/files/{file_id}/versions/{version_id}/restore" in schema["paths"]
    assert schema["paths"]["/api/v1/files/{file_id}/versions/{version_id}/restore"]["post"]["operationId"]
    assert "/api/v1/folders/tree" in schema["paths"]
    assert "/api/v1/folders" in schema["paths"]
    assert schema["paths"]["/api/v1/folders"]["post"]["operationId"]
    assert "/api/v1/folders/{folder_id}" in schema["paths"]
    assert schema["paths"]["/api/v1/folders/{folder_id}"]["patch"]["operationId"]
    assert schema["paths"]["/api/v1/folders/{folder_id}"]["delete"]["operationId"]
    assert "/api/v1/teams" in schema["paths"]
    assert schema["paths"]["/api/v1/teams"]["get"]["operationId"]
    assert schema["paths"]["/api/v1/teams"]["post"]["operationId"]
    assert "/api/v1/teams/{team_id}" in schema["paths"]
    assert schema["paths"]["/api/v1/teams/{team_id}"]["get"]["operationId"]
    assert "/api/v1/teams/{team_id}/invites" in schema["paths"]
    assert schema["paths"]["/api/v1/teams/{team_id}/invites"]["post"]["operationId"]
    assert "/api/v1/teams/{team_id}/members" in schema["paths"]
    assert schema["paths"]["/api/v1/teams/{team_id}/members"]["post"]["operationId"]
    assert "/api/v1/teams/{team_id}/members/{member_id}" in schema["paths"]
    assert schema["paths"]["/api/v1/teams/{team_id}/members/{member_id}"]["patch"]["operationId"]
    assert schema["paths"]["/api/v1/teams/{team_id}/members/{member_id}"]["delete"]["operationId"]
    assert "/api/v1/knowledge-bases" in schema["paths"]
    assert schema["paths"]["/api/v1/knowledge-bases"]["get"]["operationId"]
    assert schema["paths"]["/api/v1/knowledge-bases"]["post"]["operationId"]
    assert "/api/v1/knowledge-bases/{kb_id}" in schema["paths"]
    assert schema["paths"]["/api/v1/knowledge-bases/{kb_id}"]["patch"]["operationId"]
    assert "/api/v1/knowledge-bases/{kb_id}/documents" in schema["paths"]
    assert schema["paths"]["/api/v1/knowledge-bases/{kb_id}/documents"]["get"]["operationId"]
    assert schema["paths"]["/api/v1/knowledge-bases/{kb_id}/documents"]["post"]["operationId"]
    assert "/api/v1/workflows" in schema["paths"]
    assert schema["paths"]["/api/v1/workflows"]["get"]["operationId"]
    assert schema["paths"]["/api/v1/workflows"]["post"]["operationId"]
    assert "/api/v1/workflows/{workflow_id}" in schema["paths"]
    assert schema["paths"]["/api/v1/workflows/{workflow_id}"]["patch"]["operationId"]
    assert "/api/v1/workflows/{workflow_id}/validate" in schema["paths"]
    assert schema["paths"]["/api/v1/workflows/{workflow_id}/validate"]["post"]["operationId"]
    assert "/api/v1/workflows/{workflow_id}/publish" in schema["paths"]
    assert schema["paths"]["/api/v1/workflows/{workflow_id}/publish"]["post"]["operationId"]
    assert "/api/v1/workflows/{workflow_id}/executions" in schema["paths"]
    assert schema["paths"]["/api/v1/workflows/{workflow_id}/executions"]["post"]["operationId"]
    assert "/api/v1/permissions/rules" in schema["paths"]
    assert schema["paths"]["/api/v1/permissions/rules"]["get"]["operationId"]
    assert schema["paths"]["/api/v1/permissions/rules"]["post"]["operationId"]
    assert "/api/v1/permissions/rules/{rule_id}" in schema["paths"]
    assert schema["paths"]["/api/v1/permissions/rules/{rule_id}"]["delete"]["operationId"]
    login_responses = schema["paths"]["/api/v1/auth/login"]["post"]["responses"]
    assert login_responses["401"]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/ErrorResponse"
    assert login_responses["423"]["content"]["application/json"]["schema"]["$ref"] == "#/components/schemas/ErrorResponse"
