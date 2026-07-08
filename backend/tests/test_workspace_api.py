from __future__ import annotations

from itertools import count

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
user_counter = count(1)


def auth_session(username: str | None = None) -> dict[str, object]:
    username = username or f"xiaoming{next(user_counter)}"
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "Str0ngPass!",
        },
    )
    assert register_response.status_code == 201
    return register_response.json()


def auth_headers(username: str | None = None) -> dict[str, str]:
    token = auth_session(username)["access_token"]
    assert isinstance(token, str)
    return {"Authorization": f"Bearer {token}"}


def test_register_login_and_current_user_require_bearer_token() -> None:
    headers = auth_headers("xiaoming")

    me_response = client.get("/api/v1/users/me", headers=headers)

    assert me_response.status_code == 200
    assert me_response.json()["user"]["username"] == "xiaoming"

    denied_response = client.get("/api/v1/users/me")
    assert denied_response.status_code == 401
    assert denied_response.json()["code"] == "AUTH_REQUIRED"

    login_response = client.post(
        "/api/v1/auth/login",
        json={"account": "xiaoming", "password": "Str0ngPass!"},
    )
    assert login_response.status_code == 200
    login_body = login_response.json()
    assert login_body["token_type"] == "bearer"
    assert login_body["user"]["email"] == "xiaoming@example.com"


def test_refresh_token_issues_new_access_token_and_enforces_token_kind() -> None:
    session = auth_session()
    refresh_token = session["refresh_token"]
    access_token = session["access_token"]
    assert isinstance(refresh_token, str)
    assert isinstance(access_token, str)

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert refresh_response.status_code == 200
    refreshed = refresh_response.json()
    assert refreshed["token_type"] == "bearer"
    assert refreshed["access_token"] != access_token
    assert refreshed["refresh_token"] != refresh_token
    assert refreshed["user"]["id"] == session["user"]["id"]

    me_response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {refreshed['access_token']}"},
    )
    assert me_response.status_code == 200

    refresh_cannot_access_response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert refresh_cannot_access_response.status_code == 401
    assert refresh_cannot_access_response.json()["code"] == "INVALID_TOKEN"

    access_cannot_refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token},
    )
    assert access_cannot_refresh_response.status_code == 401
    assert access_cannot_refresh_response.json()["code"] == "INVALID_TOKEN"


def test_current_user_can_update_profile_details() -> None:
    session = auth_session()
    access_token = session["access_token"]
    assert isinstance(access_token, str)
    headers = {"Authorization": f"Bearer {access_token}"}

    update_response = client.patch(
        "/api/v1/users/me",
        headers=headers,
        json={
            "display_name": "小明同学",
            "email": "xiaoming-profile@example.com",
        },
    )

    assert update_response.status_code == 200
    updated = update_response.json()["user"]
    assert updated["display_name"] == "小明同学"
    assert updated["email"] == "xiaoming-profile@example.com"

    me_response = client.get("/api/v1/users/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["user"]["display_name"] == "小明同学"


def test_profile_update_rejects_duplicate_email() -> None:
    first_session = auth_session()
    second_session = auth_session()
    access_token = first_session["access_token"]
    assert isinstance(access_token, str)

    response = client.patch(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"email": second_session["user"]["email"]},
    )

    assert response.status_code == 409
    assert response.json()["code"] == "EMAIL_EXISTS"


def test_file_listing_filtering_and_upload_expose_parse_state() -> None:
    headers = auth_headers()

    list_response = client.get("/api/v1/files", params={"tag": "实验"}, headers=headers)
    assert list_response.status_code == 200
    files = list_response.json()["items"]
    assert [file["name"] for file in files] == ["显微镜实验报告.pdf"]
    assert files[0]["parse_status"] == "indexed"

    upload_response = client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={
            "file": (
                "观察记录.md",
                "# 显微镜观察\n细胞壁清晰可见。".encode(),
                "text/markdown",
            )
        },
        data={"folder_id": "personal-root", "tags": "实验,观察"},
    )
    assert upload_response.status_code == 201
    uploaded = upload_response.json()
    assert uploaded["name"] == "观察记录.md"
    assert uploaded["sha256"]
    assert uploaded["parse_status"] == "queued"
    assert uploaded["tags"] == ["实验", "观察"]


def test_qa_query_returns_answer_with_citations() -> None:
    headers = auth_headers()

    response = client.post(
        "/api/v1/qa/query",
        headers=headers,
        json={
            "kb_id": "kb-biology",
            "question": "总结所有用到显微镜的实验步骤",
            "top_k": 3,
            "stream": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"].startswith("显微镜相关实验步骤包括")
    assert body["citations"][0]["title"] == "显微镜实验报告.pdf"
    assert body["citations"][0]["page_no"] == 3


def test_agent_task_uses_required_builtin_tools() -> None:
    headers = auth_headers()

    tools_response = client.get("/api/v1/tools", headers=headers)
    assert tools_response.status_code == 200
    tool_names = {tool["name"] for tool in tools_response.json()["items"]}
    assert {"file_search", "knowledge_qa", "report_generate"}.issubset(tool_names)

    task_response = client.post(
        "/api/v1/agents/tasks",
        headers=headers,
        json={
            "task": "汇总本周生物实验资料并生成报告",
            "kb_id": "kb-biology",
            "context_file_ids": ["file-microscope"],
        },
    )
    assert task_response.status_code == 201
    task = task_response.json()
    assert task["status"] == "completed"
    assert [step["type"] for step in task["steps"]] == [
        "thought",
        "action",
        "observation",
        "action",
        "observation",
        "answer",
    ]
    assert task["steps"][1]["tool_name"] == "file_search"
    assert task["steps"][3]["tool_name"] == "report_generate"


def test_new_file_auto_summary_workflow_template_executes() -> None:
    headers = auth_headers()

    templates_response = client.get("/api/v1/workflows", headers=headers)
    assert templates_response.status_code == 200
    template_ids = [workflow["id"] for workflow in templates_response.json()["items"]]
    assert "new-file-auto-summary" in template_ids

    execution_response = client.post(
        "/api/v1/workflows/new-file-auto-summary/executions",
        headers=headers,
        json={"file_id": "file-microscope", "target_kb_id": "kb-biology"},
    )
    assert execution_response.status_code == 201
    execution = execution_response.json()
    assert execution["status"] == "completed"
    assert [node["status"] for node in execution["node_executions"]] == [
        "success",
        "success",
        "success",
    ]
    assert "显微镜实验报告.pdf" in execution["output"]["summary"]
