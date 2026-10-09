import uuid

from fastapi.testclient import TestClient

from app.db.init_db import init_db
from app.main import app


client = TestClient(app)

init_db()


def unique_value(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def register_user(role: str = "Super Admin"):
    username = unique_value("notification_user")
    email = f"{username}@example.com"

    response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "full_name": "Notification Test User",
            "password": "Test@12345",
            "role": role,
        },
    )

    assert response.status_code == 201

    return username


def login_user(username: str):
    response = client.post(
        "/auth/login",
        json={
            "username": username,
            "password": "Test@12345",
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def auth_headers(token: str):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_notification(
    token: str,
    user_id: int,
    title: str = "Test Notification",
):
    return client.post(
        "/notifications",
        json={
            "user_id": user_id,
            "notification_type": "Info",
            "title": title,
            "message": "This is a test notification",
            "entity_type": "ProductionBatch",
            "entity_id": 1,
        },
        headers=auth_headers(token),
    )


def test_notifications_require_authentication():

    response = client.get("/notifications")

    assert response.status_code == 401


def test_super_admin_can_create_notification():

    username = register_user("Super Admin")
    token = login_user(username)

    response = client.get(
        "/auth/me",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    user_id = response.json()["id"]

    response = create_notification(
        token,
        user_id,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == user_id
    assert data["status"] == "Unread"
    assert data["title"] == "Test Notification"
    assert data["notification_type"] == "Info"


def test_user_can_list_own_notifications():

    username = register_user("Super Admin")
    token = login_user(username)

    me = client.get(
        "/auth/me",
        headers=auth_headers(token),
    )

    user_id = me.json()["id"]

    created = create_notification(
        token,
        user_id,
        "List Test",
    )

    assert created.status_code == 201

    response = client.get(
        "/notifications",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1
    assert any(
        item["title"] == "List Test"
        for item in data
    )


def test_notification_filter_by_status():

    username = register_user("Super Admin")
    token = login_user(username)

    me = client.get(
        "/auth/me",
        headers=auth_headers(token),
    )

    user_id = me.json()["id"]

    create_notification(
        token,
        user_id,
        "Unread Filter Test",
    )

    response = client.get(
        "/notifications?status=Unread",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    for item in response.json():
        assert item["status"] == "Unread"


def test_unread_count():

    username = register_user("Super Admin")
    token = login_user(username)

    me = client.get(
        "/auth/me",
        headers=auth_headers(token),
    )

    user_id = me.json()["id"]

    create_notification(
        token,
        user_id,
        "Unread Count Test",
    )

    response = client.get(
        "/notifications/unread-count",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] == user_id
    assert data["unread_count"] >= 1


def test_user_can_get_own_notification():

    username = register_user("Super Admin")
    token = login_user(username)

    me = client.get(
        "/auth/me",
        headers=auth_headers(token),
    )

    user_id = me.json()["id"]

    created = create_notification(
        token,
        user_id,
        "Get Test",
    )

    notification_id = created.json()["id"]

    response = client.get(
        f"/notifications/{notification_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == notification_id


def test_user_can_mark_notification_read():

    username = register_user("Super Admin")
    token = login_user(username)

    me = client.get(
        "/auth/me",
        headers=auth_headers(token),
    )

    user_id = me.json()["id"]

    created = create_notification(
        token,
        user_id,
        "Read Test",
    )

    notification_id = created.json()["id"]

    response = client.patch(
        f"/notifications/{notification_id}/read",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "Read"
    assert data["read_at"] is not None


def test_mark_all_notifications_read():

    username = register_user("Super Admin")
    token = login_user(username)

    me = client.get(
        "/auth/me",
        headers=auth_headers(token),
    )

    user_id = me.json()["id"]

    create_notification(
        token,
        user_id,
        "Read All 1",
    )

    create_notification(
        token,
        user_id,
        "Read All 2",
    )

    response = client.patch(
        "/notifications/read-all",
        headers=auth_headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["user_id"] == user_id
    assert data["marked_read"] >= 2


def test_worker_cannot_create_notification():

    username = register_user("Worker")
    token = login_user(username)

    me = client.get(
        "/auth/me",
        headers=auth_headers(token),
    )

    user_id = me.json()["id"]

    response = create_notification(
        token,
        user_id,
    )

    assert response.status_code == 403


def test_user_cannot_access_another_users_notification():

    admin_username = register_user("Super Admin")
    admin_token = login_user(admin_username)

    admin_me = client.get(
        "/auth/me",
        headers=auth_headers(admin_token),
    )

    admin_id = admin_me.json()["id"]

    created = create_notification(
        admin_token,
        admin_id,
        "Private Notification",
    )

    notification_id = created.json()["id"]

    worker_username = register_user("Worker")
    worker_token = login_user(worker_username)

    response = client.get(
        f"/notifications/{notification_id}",
        headers=auth_headers(worker_token),
    )

    assert response.status_code == 403


def test_user_cannot_delete_another_users_notification():

    admin_username = register_user("Super Admin")
    admin_token = login_user(admin_username)

    admin_me = client.get(
        "/auth/me",
        headers=auth_headers(admin_token),
    )

    admin_id = admin_me.json()["id"]

    created = create_notification(
        admin_token,
        admin_id,
        "Delete Protection Test",
    )

    notification_id = created.json()["id"]

    worker_username = register_user("Worker")
    worker_token = login_user(worker_username)

    response = client.delete(
        f"/notifications/{notification_id}",
        headers=auth_headers(worker_token),
    )

    assert response.status_code == 403


def test_user_can_delete_own_notification():

    username = register_user("Super Admin")
    token = login_user(username)

    me = client.get(
        "/auth/me",
        headers=auth_headers(token),
    )

    user_id = me.json()["id"]

    created = create_notification(
        token,
        user_id,
        "Delete Test",
    )

    notification_id = created.json()["id"]

    response = client.delete(
        f"/notifications/{notification_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == notification_id

    get_response = client.get(
        f"/notifications/{notification_id}",
        headers=auth_headers(token),
    )

    assert get_response.status_code == 404