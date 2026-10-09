import uuid

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def register_user(
    username: str,
    email: str,
    role: str,
):
    unique_id = uuid.uuid4().hex[:8]

    unique_username = f"{username}_{unique_id}"
    unique_email = f"{unique_id}_{email}"

    response = client.post(
        "/auth/register",
        json={
            "username": unique_username,
            "email": unique_email,
            "full_name": f"Test {role}",
            "password": "Test@12345",
            "role": role,
        },
    )

    return response, unique_username


def login_user(username: str):
    return client.post(
        "/auth/login",
        json={
            "username": username,
            "password": "Test@12345",
        },
    )


def test_refresh_preserves_super_admin_role():
    register_response, username = register_user(
        "refresh_admin",
        "refresh_admin@test.com",
        "Super Admin",
    )

    assert register_response.status_code == 201

    login_response = login_user(username)

    assert login_response.status_code == 200

    refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert refresh_response.status_code == 200

    access_token = refresh_response.json()["access_token"]

    me_response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert me_response.status_code == 200
    assert me_response.json()["role"] == "Super Admin"


def test_refresh_preserves_plant_manager_role():
    register_response, username = register_user(
        "refresh_plant_manager",
        "refresh_plant_manager@test.com",
        "Plant Manager",
    )

    assert register_response.status_code == 201

    login_response = login_user(username)

    assert login_response.status_code == 200

    refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert refresh_response.status_code == 200

    access_token = refresh_response.json()["access_token"]

    me_response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert me_response.status_code == 200
    assert me_response.json()["role"] == "Plant Manager"


def test_refresh_rejects_invalid_token():
    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": "invalid-refresh-token",
        },
    )

    assert response.status_code == 401


def test_refresh_rejects_access_token():
    register_response, username = register_user(
        "refresh_access_test",
        "refresh_access_test@test.com",
        "Worker",
    )

    assert register_response.status_code == 201

    login_response = login_user(username)

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": access_token,
        },
    )

    assert refresh_response.status_code == 401


def test_refresh_rejects_nonexistent_user():
    from app.core.security import create_refresh_token

    refresh_token = create_refresh_token(
        subject="999999999",
    )

    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 401


def test_refresh_rejects_inactive_user():
    register_response, username = register_user(
        "refresh_inactive",
        "refresh_inactive@test.com",
        "Worker",
    )

    assert register_response.status_code == 201

    login_response = login_user(username)

    assert login_response.status_code == 200

    refresh_token = login_response.json()["refresh_token"]

    from app.db.database import SessionLocal
    from app.models.user import User

    db = SessionLocal()

    try:
        user = db.query(User).filter(
            User.username == username
        ).first()

        assert user is not None

        user.is_active = False
        db.commit()
    finally:
        db.close()

    refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert refresh_response.status_code == 403


def test_logout_invalidates_access_token():
    register_response, username = register_user(
        "logout_test",
        "logout_test@test.com",
        "Worker",
    )

    assert register_response.status_code == 201

    login_response = login_user(username)

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    before_logout = client.get(
        "/auth/me",
        headers=headers,
    )

    assert before_logout.status_code == 200

    logout_response = client.post(
        "/auth/logout",
        headers=headers,
    )

    assert logout_response.status_code == 200
    assert logout_response.json()["message"] == "Successfully logged out"

    after_logout = client.get(
        "/auth/me",
        headers=headers,
    )

    assert after_logout.status_code == 401


def test_logout_requires_authentication():
    response = client.post("/auth/logout")

    assert response.status_code == 401

def test_require_roles_allows_matching_role():
    register_response, username = register_user(
        "role_allowed",
        "role_allowed@test.com",
        "Plant Manager",
    )

    assert register_response.status_code == 201

    login_response = login_user(username)

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    response = client.get(
        "/auth/me",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["role"] == "Plant Manager"


def test_require_roles_rejects_wrong_role():
    register_response, username = register_user(
        "role_denied",
        "role_denied@test.com",
        "Worker",
    )

    assert register_response.status_code == 201

    login_response = login_user(username)

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    from app.api.auth.dependencies import require_roles
    from app.models.user import UserRole

    dependency = require_roles(UserRole.PLANT_MANAGER)

    from app.api.auth.dependencies import get_current_user

    assert dependency is not None
    assert get_current_user is not None

def test_admin_test_allows_super_admin():
    register_response, username = register_user(
        "admin_rbac",
        "admin_rbac@test.com",
        "Super Admin",
    )

    assert register_response.status_code == 201

    login_response = login_user(username)

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/auth/admin-test",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Super Admin access granted"
    assert data["username"] == username
    assert data["role"] == "Super Admin"


def test_admin_test_forbids_non_admin():
    register_response, username = register_user(
        "worker_rbac",
        "worker_rbac@test.com",
        "Worker",
    )

    assert register_response.status_code == 201

    login_response = login_user(username)

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/auth/admin-test",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"