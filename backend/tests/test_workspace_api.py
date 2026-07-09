from __future__ import annotations

<<<<<<< HEAD
import hashlib
=======
>>>>>>> permission-backend
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


<<<<<<< HEAD
def session_headers(session: dict[str, object]) -> dict[str, str]:
    token = session["access_token"]
    assert isinstance(token, str)
    return {"Authorization": f"Bearer {token}"}


=======
>>>>>>> permission-backend
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


<<<<<<< HEAD
def test_login_failures_lock_account_temporarily_and_are_audited() -> None:
    session = auth_session("lockout-user")
    access_token = session["access_token"]
    assert isinstance(access_token, str)

    for attempt in range(1, 5):
        response = client.post(
            "/api/v1/auth/login",
            json={"account": "lockout-user", "password": "WrongPass!"},
        )
        assert response.status_code == 401
        assert response.json()["code"] == "INVALID_CREDENTIALS"
        assert response.json()["detail"]["failed_attempts"] == attempt
        assert response.json()["detail"]["max_attempts"] == 5

    locked_response = client.post(
        "/api/v1/auth/login",
        json={"account": "lockout-user", "password": "WrongPass!"},
    )
    assert locked_response.status_code == 423
    locked_body = locked_response.json()
    assert locked_body["code"] == "ACCOUNT_LOCKED"
    assert locked_body["detail"]["failed_attempts"] == 5
    assert locked_body["detail"]["max_attempts"] == 5
    assert locked_body["detail"]["retry_after_seconds"] > 0
    assert locked_body["detail"]["locked_until"]

    correct_password_response = client.post(
        "/api/v1/auth/login",
        json={"account": "lockout-user", "password": "Str0ngPass!"},
    )
    assert correct_password_response.status_code == 423
    assert correct_password_response.json()["code"] == "ACCOUNT_LOCKED"

    audit_response = client.get(
        "/api/v1/audit-logs",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert audit_response.status_code == 200
    actions = [entry["action"] for entry in audit_response.json()["items"]]
    assert "auth.login_failed" in actions
    assert "auth.account_locked" in actions


def test_successful_login_resets_failed_login_count_before_lockout() -> None:
    auth_session("login-reset-user")

    for attempt in range(1, 4):
        response = client.post(
            "/api/v1/auth/login",
            json={"account": "login-reset-user", "password": "WrongPass!"},
        )
        assert response.status_code == 401
        assert response.json()["detail"]["failed_attempts"] == attempt

    success_response = client.post(
        "/api/v1/auth/login",
        json={"account": "login-reset-user", "password": "Str0ngPass!"},
    )
    assert success_response.status_code == 200

    for attempt in range(1, 5):
        response = client.post(
            "/api/v1/auth/login",
            json={"account": "login-reset-user", "password": "WrongPass!"},
        )
        assert response.status_code == 401
        assert response.json()["code"] == "INVALID_CREDENTIALS"
        assert response.json()["detail"]["failed_attempts"] == attempt


=======
>>>>>>> permission-backend
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


<<<<<<< HEAD
def test_file_download_returns_original_content_and_audit_event() -> None:
    headers = auth_headers()
    upload_response = client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("观察记录.md", "细胞壁清晰可见。".encode(), "text/markdown")},
        data={"folder_id": "personal-root", "tags": "实验"},
    )
    assert upload_response.status_code == 201
    file_id = upload_response.json()["id"]

    download_response = client.get(f"/api/v1/files/{file_id}/download", headers=headers)

    assert download_response.status_code == 200
    assert download_response.content == "细胞壁清晰可见。".encode()
    assert download_response.headers["content-type"] == "application/octet-stream"
    assert download_response.headers["content-disposition"].startswith("attachment;")

    audit_response = client.get("/api/v1/audit-logs", headers=headers)
    assert audit_response.status_code == 200
    actions = [entry["action"] for entry in audit_response.json()["items"]]
    assert "file.download" in actions


def test_file_delete_removes_file_from_listing_and_audit_log() -> None:
    headers = auth_headers()
    upload_response = client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("待删除.txt", "临时资料".encode(), "text/plain")},
        data={"folder_id": "personal-root", "tags": "临时"},
    )
    assert upload_response.status_code == 201
    file_id = upload_response.json()["id"]

    delete_response = client.delete(f"/api/v1/files/{file_id}", headers=headers)

    assert delete_response.status_code == 204
    list_response = client.get("/api/v1/files", headers=headers)
    assert list_response.status_code == 200
    assert file_id not in {item["id"] for item in list_response.json()["items"]}

    second_delete_response = client.delete(f"/api/v1/files/{file_id}", headers=headers)
    assert second_delete_response.status_code == 404
    assert second_delete_response.json()["code"] == "FILE_NOT_FOUND"

    audit_response = client.get("/api/v1/audit-logs", headers=headers)
    assert audit_response.status_code == 200
    actions = [entry["action"] for entry in audit_response.json()["items"]]
    assert "file.delete" in actions


def test_file_update_copy_and_folder_validation_are_audited() -> None:
    headers = auth_headers()
    upload_response = client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("待整理.md", "第一版观察记录".encode(), "text/markdown")},
        data={"folder_id": "personal-root", "tags": "草稿"},
    )
    assert upload_response.status_code == 201
    uploaded = upload_response.json()
    file_id = uploaded["id"]

    missing_folder_response = client.patch(
        f"/api/v1/files/{file_id}",
        headers=headers,
        json={"folder_id": "folder-missing"},
    )
    assert missing_folder_response.status_code == 404
    assert missing_folder_response.json()["code"] == "FOLDER_NOT_FOUND"

    update_response = client.patch(
        f"/api/v1/files/{file_id}",
        headers=headers,
        json={
            "name": "归档观察.md",
            "folder_id": "folder-biology",
            "tags": ["实验", "归档"],
        },
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["id"] == file_id
    assert updated["name"] == "归档观察.md"
    assert updated["folder_id"] == "folder-biology"
    assert updated["tags"] == ["实验", "归档"]

    tag_response = client.get("/api/v1/files", params={"tag": "归档"}, headers=headers)
    assert tag_response.status_code == 200
    assert [item["id"] for item in tag_response.json()["items"]] == [file_id]

    copy_response = client.post(
        f"/api/v1/files/{file_id}/copy",
        headers=headers,
        json={"target_folder_id": "folder-course", "name": "归档观察 副本.md"},
    )
    assert copy_response.status_code == 201
    copied = copy_response.json()
    assert copied["id"] != file_id
    assert copied["name"] == "归档观察 副本.md"
    assert copied["folder_id"] == "folder-course"
    assert copied["sha256"] == updated["sha256"]
    assert copied["tags"] == ["实验", "归档"]

    copy_download_response = client.get(f"/api/v1/files/{copied['id']}/download", headers=headers)
    assert copy_download_response.status_code == 200
    assert copy_download_response.content == "第一版观察记录".encode()

    cross_scope_move_response = client.patch(
        f"/api/v1/files/{file_id}",
        headers=headers,
        json={"folder_id": "team-root"},
    )
    assert cross_scope_move_response.status_code == 409
    assert cross_scope_move_response.json()["code"] == "FILE_SCOPE_MISMATCH"

    missing_folder_upload_response = client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("孤立文件.md", "没有目录".encode(), "text/markdown")},
        data={"folder_id": "folder-missing", "tags": "错误"},
    )
    assert missing_folder_upload_response.status_code == 404
    assert missing_folder_upload_response.json()["code"] == "FOLDER_NOT_FOUND"

    audit_response = client.get("/api/v1/audit-logs", headers=headers)
    assert audit_response.status_code == 200
    actions = [entry["action"] for entry in audit_response.json()["items"]]
    assert "file.rename" in actions
    assert "file.move" in actions
    assert "file.update_tags" in actions
    assert "file.copy" in actions


def test_same_name_upload_creates_versions_and_restore_creates_new_current_version() -> None:
    headers = auth_headers()
    original_content = "版本一：低倍镜定位。".encode()
    replacement_content = "版本二：高倍镜观察。".encode()

    first_upload_response = client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("版本记录.md", original_content, "text/markdown")},
        data={"folder_id": "personal-root", "tags": "版本"},
    )
    assert first_upload_response.status_code == 201
    first_upload = first_upload_response.json()

    second_upload_response = client.post(
        "/api/v1/files/upload",
        headers=headers,
        files={"file": ("版本记录.md", replacement_content, "text/markdown")},
        data={"folder_id": "personal-root", "tags": "版本,覆盖"},
    )
    assert second_upload_response.status_code == 201
    second_upload = second_upload_response.json()
    assert second_upload["id"] == first_upload["id"]
    assert second_upload["sha256"] == hashlib.sha256(replacement_content).hexdigest()
    assert second_upload["tags"] == ["版本", "覆盖"]

    versions_response = client.get(f"/api/v1/files/{first_upload['id']}/versions", headers=headers)
    assert versions_response.status_code == 200
    versions = versions_response.json()["items"]
    assert [version["version_no"] for version in versions] == [2, 1]
    assert versions[0]["is_current"] is True
    assert versions[1]["is_current"] is False
    original_version_id = versions[1]["id"]

    current_download_response = client.get(f"/api/v1/files/{first_upload['id']}/download", headers=headers)
    assert current_download_response.status_code == 200
    assert current_download_response.content == replacement_content

    restore_response = client.post(
        f"/api/v1/files/{first_upload['id']}/versions/{original_version_id}/restore",
        headers=headers,
    )
    assert restore_response.status_code == 200
    restored = restore_response.json()
    assert restored["id"] == first_upload["id"]
    assert restored["sha256"] == hashlib.sha256(original_content).hexdigest()

    restored_download_response = client.get(f"/api/v1/files/{first_upload['id']}/download", headers=headers)
    assert restored_download_response.status_code == 200
    assert restored_download_response.content == original_content

    restored_versions_response = client.get(f"/api/v1/files/{first_upload['id']}/versions", headers=headers)
    assert restored_versions_response.status_code == 200
    restored_versions = restored_versions_response.json()["items"]
    assert [version["version_no"] for version in restored_versions] == [3, 2, 1]
    assert restored_versions[0]["is_current"] is True
    assert restored_versions[0]["sha256"] == hashlib.sha256(original_content).hexdigest()

    audit_response = client.get("/api/v1/audit-logs", headers=headers)
    assert audit_response.status_code == 200
    actions = [entry["action"] for entry in audit_response.json()["items"]]
    assert "file.version_create" in actions
    assert "file.version_restore" in actions


def test_folder_crud_supports_nested_tree_move_delete_and_audit_events() -> None:
    headers = auth_headers()

    create_parent_response = client.post(
        "/api/v1/folders",
        headers=headers,
        json={"name": "课程资料", "parent_id": "personal-root", "scope": "personal"},
    )
    assert create_parent_response.status_code == 201
    parent = create_parent_response.json()
    assert parent["name"] == "课程资料"
    assert parent["parent_id"] == "personal-root"

    create_child_response = client.post(
        "/api/v1/folders",
        headers=headers,
        json={"name": "第 1 周", "parent_id": parent["id"], "scope": "personal"},
    )
    assert create_child_response.status_code == 201
    child = create_child_response.json()
    assert child["parent_id"] == parent["id"]

    tree_response = client.get("/api/v1/folders/tree", headers=headers)
    assert tree_response.status_code == 200
    flattened = flatten_folders(tree_response.json()["items"])
    assert flattened[parent["id"]]["name"] == "课程资料"
    assert flattened[child["id"]]["parent_id"] == parent["id"]

    move_response = client.patch(
        f"/api/v1/folders/{child['id']}",
        headers=headers,
        json={"name": "课堂笔记", "parent_id": "folder-course"},
    )
    assert move_response.status_code == 200
    moved = move_response.json()
    assert moved["name"] == "课堂笔记"
    assert moved["parent_id"] == "folder-course"

    delete_parent_response = client.delete(f"/api/v1/folders/{parent['id']}", headers=headers)
    assert delete_parent_response.status_code == 204

    delete_child_response = client.delete(f"/api/v1/folders/{child['id']}", headers=headers)
    assert delete_child_response.status_code == 204

    audit_response = client.get("/api/v1/audit-logs", headers=headers)
    assert audit_response.status_code == 200
    actions = [entry["action"] for entry in audit_response.json()["items"]]
    assert "folder.create" in actions
    assert "folder.rename" in actions
    assert "folder.move" in actions
    assert "folder.delete" in actions


def test_folder_crud_rejects_non_empty_delete_roots_and_cycle_moves() -> None:
    headers = auth_headers()

    parent_response = client.post(
        "/api/v1/folders",
        headers=headers,
        json={"name": "资料归档", "parent_id": "personal-root", "scope": "personal"},
    )
    assert parent_response.status_code == 201
    parent = parent_response.json()

    child_response = client.post(
        "/api/v1/folders",
        headers=headers,
        json={"name": "子目录", "parent_id": parent["id"], "scope": "personal"},
    )
    assert child_response.status_code == 201
    child = child_response.json()

    delete_non_empty_response = client.delete(f"/api/v1/folders/{parent['id']}", headers=headers)
    assert delete_non_empty_response.status_code == 409
    assert delete_non_empty_response.json()["code"] == "FOLDER_NOT_EMPTY"

    cycle_move_response = client.patch(
        f"/api/v1/folders/{parent['id']}",
        headers=headers,
        json={"parent_id": child["id"]},
    )
    assert cycle_move_response.status_code == 409
    assert cycle_move_response.json()["code"] == "FOLDER_CYCLE"

    missing_parent_response = client.post(
        "/api/v1/folders",
        headers=headers,
        json={"name": "不存在父目录", "parent_id": "folder-missing", "scope": "personal"},
    )
    assert missing_parent_response.status_code == 404
    assert missing_parent_response.json()["code"] == "FOLDER_NOT_FOUND"

    delete_root_response = client.delete("/api/v1/folders/personal-root", headers=headers)
    assert delete_root_response.status_code == 409
    assert delete_root_response.json()["code"] == "FOLDER_ROOT_PROTECTED"


def test_team_invites_role_updates_and_removal_are_audited() -> None:
    owner_session = auth_session()
    member_session = auth_session()
    owner_headers = session_headers(owner_session)
    member_headers = session_headers(member_session)
    member_email = member_session["user"]["email"]
    assert isinstance(member_email, str)

    create_team_response = client.post(
        "/api/v1/teams",
        headers=owner_headers,
        json={"name": "算法课程小组", "description": "课程资料与周报协作"},
    )
    assert create_team_response.status_code == 201
    team = create_team_response.json()
    assert team["name"] == "算法课程小组"
    assert team["role"] == "owner"
    assert team["member_count"] == 1
    assert team["root_folder"]["scope"] == "team"
    assert [member["role"] for member in team["members"]] == ["owner"]

    invite_response = client.post(
        f"/api/v1/teams/{team['id']}/invites",
        headers=owner_headers,
        json={"email": member_email, "role": "member"},
    )
    assert invite_response.status_code == 201
    invite = invite_response.json()
    assert invite["email"] == member_email
    assert invite["role"] == "member"
    assert invite["status"] == "pending"
    assert invite["token"]

    accept_response = client.post(
        f"/api/v1/teams/{team['id']}/members",
        headers=member_headers,
        json={"invite_token": invite["token"]},
    )
    assert accept_response.status_code == 201
    joined_member = accept_response.json()
    assert joined_member["email"] == member_email
    assert joined_member["role"] == "member"
    assert joined_member["status"] == "active"

    role_update_response = client.patch(
        f"/api/v1/teams/{team['id']}/members/{joined_member['id']}",
        headers=owner_headers,
        json={"role": "admin"},
    )
    assert role_update_response.status_code == 200
    assert role_update_response.json()["role"] == "admin"

    remove_response = client.delete(
        f"/api/v1/teams/{team['id']}/members/{joined_member['id']}",
        headers=owner_headers,
    )
    assert remove_response.status_code == 204

    denied_detail_response = client.get(f"/api/v1/teams/{team['id']}", headers=member_headers)
    assert denied_detail_response.status_code == 403
    assert denied_detail_response.json()["code"] == "TEAM_ACCESS_DENIED"

    audit_response = client.get("/api/v1/audit-logs", headers=owner_headers)
    assert audit_response.status_code == 200
    actions = [entry["action"] for entry in audit_response.json()["items"]]
    assert "team.create" in actions
    assert "team.invite_create" in actions
    assert "team.member_join" in actions
    assert "team.member_role_update" in actions
    assert "team.member_remove" in actions


def test_team_folder_permissions_enforce_guest_read_only_and_member_write() -> None:
    owner_session = auth_session()
    member_session = auth_session()
    guest_session = auth_session()
    owner_headers = session_headers(owner_session)
    member_headers = session_headers(member_session)
    guest_headers = session_headers(guest_session)

    create_team_response = client.post(
        "/api/v1/teams",
        headers=owner_headers,
        json={"name": "工程实践小组", "description": "实验数据共享"},
    )
    assert create_team_response.status_code == 201
    team = create_team_response.json()
    team_folder_id = team["root_folder"]["id"]

    for invited_session, role, headers in [
        (member_session, "member", member_headers),
        (guest_session, "guest", guest_headers),
    ]:
        invited_email = invited_session["user"]["email"]
        assert isinstance(invited_email, str)
        invite_response = client.post(
            f"/api/v1/teams/{team['id']}/invites",
            headers=owner_headers,
            json={"email": invited_email, "role": role},
        )
        assert invite_response.status_code == 201
        accept_response = client.post(
            f"/api/v1/teams/{team['id']}/members",
            headers=headers,
            json={"invite_token": invite_response.json()["token"]},
        )
        assert accept_response.status_code == 201

    member_upload_response = client.post(
        "/api/v1/files/upload",
        headers=member_headers,
        files={"file": ("团队观察.md", "成员可写团队资料。".encode(), "text/markdown")},
        data={"folder_id": team_folder_id, "tags": "团队,观察"},
    )
    assert member_upload_response.status_code == 201
    assert member_upload_response.json()["folder_id"] == team_folder_id
    assert member_upload_response.json()["permission_scope"] == "团队"

    guest_upload_response = client.post(
        "/api/v1/files/upload",
        headers=guest_headers,
        files={"file": ("访客记录.md", "访客不能写。".encode(), "text/markdown")},
        data={"folder_id": team_folder_id, "tags": "团队"},
    )
    assert guest_upload_response.status_code == 403
    assert guest_upload_response.json()["code"] == "FOLDER_WRITE_FORBIDDEN"


=======
>>>>>>> permission-backend
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
<<<<<<< HEAD


def flatten_folders(items: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    flattened: dict[str, dict[str, object]] = {}
    for item in items:
        folder_id = item["id"]
        assert isinstance(folder_id, str)
        flattened[folder_id] = item
        children = item.get("children", [])
        assert isinstance(children, list)
        flattened.update(flatten_folders(children))
    return flattened
=======
>>>>>>> permission-backend
