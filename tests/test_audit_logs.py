import uuid

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def unique_value(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def create_user(
    role: str = "Super Admin",
) -> str:
    username = unique_value("audit_user")

    response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "full_name": "Audit Test User",
            "password": "Test@12345",
            "role": role,
            "is_active": True,
        },
    )

    assert response.status_code == 201, response.text

    return username


def login(
    username: str,
) -> str:
    response = client.post(
        "/auth/login",
        json={
            "username": username,
            "password": "Test@12345",
        },
    )

    assert response.status_code == 200, response.text

    return response.json()["access_token"]


def headers(
    token: str,
) -> dict:
    return {
        "Authorization": f"Bearer {token}",
    }


def create_token(
    role: str = "Super Admin",
) -> str:
    username = create_user(role)

    return login(username)


def test_audit_logs_require_authentication():
    response = client.get(
        "/audit-logs"
    )

    assert response.status_code == 401


def test_super_admin_can_create_audit_log():
    token = create_token()

    response = client.post(
        "/audit-logs",
        headers=headers(token),
        json={
            "action": "CREATE",
            "entity_type": "Product",
            "entity_id": 1,
            "description": "Created test product",
            "old_values": None,
            "new_values": '{"name":"Test Product"}',
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["action"] == "CREATE"
    assert data["entity_type"] == "Product"
    assert data["entity_id"] == 1
    assert data["description"] == "Created test product"
    assert data["user_id"] is not None
    assert data["username"] is not None
    assert data["request_method"] == "POST"
    assert data["request_path"] == "/audit-logs"


def test_can_list_audit_logs():
    token = create_token()

    create_response = client.post(
        "/audit-logs",
        headers=headers(token),
        json={
            "action": "UPDATE",
            "entity_type": "ProductionOrder",
            "entity_id": 10,
            "description": "Updated production order",
        },
    )

    assert create_response.status_code == 201

    response = client.get(
        "/audit-logs",
        headers=headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1


def test_can_filter_audit_logs_by_action():
    token = create_token()

    response = client.post(
        "/audit-logs",
        headers=headers(token),
        json={
            "action": "DELETE",
            "entity_type": "Product",
            "entity_id": 99,
            "description": "Deleted product",
        },
    )

    assert response.status_code == 201

    response = client.get(
        "/audit-logs",
        params={
            "action": "DELETE",
        },
        headers=headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1

    for item in data:
        assert item["action"] == "DELETE"


def test_can_filter_audit_logs_by_entity():
    token = create_token()

    response = client.post(
        "/audit-logs",
        headers=headers(token),
        json={
            "action": "UPDATE",
            "entity_type": "Machine",
            "entity_id": 25,
            "description": "Updated machine",
        },
    )

    assert response.status_code == 201

    response = client.get(
        "/audit-logs",
        params={
            "entity_type": "Machine",
            "entity_id": 25,
        },
        headers=headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1

    for item in data:
        assert item["entity_type"] == "Machine"
        assert item["entity_id"] == 25


def test_can_get_single_audit_log():
    token = create_token()

    create_response = client.post(
        "/audit-logs",
        headers=headers(token),
        json={
            "action": "LOGIN",
            "entity_type": "User",
            "entity_id": 1,
            "description": "User login",
        },
    )

    assert create_response.status_code == 201

    audit_log_id = create_response.json()["id"]

    response = client.get(
        f"/audit-logs/{audit_log_id}",
        headers=headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == audit_log_id
    assert data["action"] == "LOGIN"


def test_get_missing_audit_log_returns_404():
    token = create_token()

    response = client.get(
        "/audit-logs/999999999",
        headers=headers(token),
    )

    assert response.status_code == 404


def test_worker_cannot_view_audit_logs():
    token = create_token("Worker")

    response = client.get(
        "/audit-logs",
        headers=headers(token),
    )

    assert response.status_code == 403


def test_worker_cannot_create_audit_log():
    token = create_token("Worker")

    response = client.post(
        "/audit-logs",
        headers=headers(token),
        json={
            "action": "CREATE",
            "entity_type": "Product",
            "entity_id": 1,
            "description": "Unauthorized audit log",
        },
    )

    assert response.status_code == 403


def test_super_admin_can_delete_audit_log():
    token = create_token()

    create_response = client.post(
        "/audit-logs",
        headers=headers(token),
        json={
            "action": "CREATE",
            "entity_type": "TestEntity",
            "entity_id": 100,
            "description": "Audit log to delete",
        },
    )

    assert create_response.status_code == 201

    audit_log_id = create_response.json()["id"]

    response = client.delete(
        f"/audit-logs/{audit_log_id}",
        headers=headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == audit_log_id

    response = client.get(
        f"/audit-logs/{audit_log_id}",
        headers=headers(token),
    )

    assert response.status_code == 404


def test_non_admin_cannot_delete_audit_log():
    admin_token = create_token()

    create_response = client.post(
        "/audit-logs",
        headers=headers(admin_token),
        json={
            "action": "CREATE",
            "entity_type": "Product",
            "entity_id": 5,
            "description": "Protected audit log",
        },
    )

    assert create_response.status_code == 201

    audit_log_id = create_response.json()["id"]

    manager_token = create_token(
        "Plant Manager"
    )

    response = client.delete(
        f"/audit-logs/{audit_log_id}",
        headers=headers(manager_token),
    )

    assert response.status_code == 403