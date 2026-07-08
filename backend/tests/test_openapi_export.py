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
