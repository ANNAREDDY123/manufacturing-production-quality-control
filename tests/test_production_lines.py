import uuid

from fastapi.testclient import TestClient

from app.db.init_db import init_db
from app.main import app


client = TestClient(app)

init_db()


def unique_value(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def register_user(
    role: str = "Super Admin",
):
    username = unique_value("user")
    email = f"{username}@example.com"

    response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email,
            "full_name": "Test User",
            "password": "Test@12345",
            "role": role,
        },
    )

    assert response.status_code == 201

    return {
        "username": username,
        "password": "Test@12345",
    }


def login_user(username: str, password: str) -> str:
    response = client.post(
        "/auth/login",
        json={
            "username": username,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def create_plant(token: str) -> int:
    response = client.post(
        "/plants",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "plant_code": unique_value("PLANT"),
            "name": "Test Manufacturing Plant",
            "description": "Production test plant",
            "address": "Industrial Area",
            "city": "Hyderabad",
            "state": "Telangana",
            "country": "India",
            "capacity": 10000,
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def create_super_admin_token() -> str:
    user = register_user("Super Admin")

    return login_user(
        user["username"],
        user["password"],
    )


def test_create_production_line():
    token = create_super_admin_token()
    plant_id = create_plant(token)

    response = client.post(
        "/production-lines",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "line_code": unique_value("LINE"),
            "name": "Assembly Line 1",
            "capacity": 500,
            "plant_id": plant_id,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["plant_id"] == plant_id
    assert data["capacity"] == 500
    assert data["status"] == "Active"


def test_duplicate_line_code_rejected():
    token = create_super_admin_token()
    plant_id = create_plant(token)

    line_code = unique_value("LINE")

    payload = {
        "line_code": line_code,
        "name": "Assembly Line",
        "capacity": 500,
        "plant_id": plant_id,
    }

    first_response = client.post(
        "/production-lines",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/production-lines",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=payload,
    )

    assert second_response.status_code == 400
    assert "already exists" in second_response.json()["detail"]


def test_create_line_with_invalid_plant():
    token = create_super_admin_token()

    response = client.post(
        "/production-lines",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "line_code": unique_value("LINE"),
            "name": "Invalid Plant Line",
            "capacity": 500,
            "plant_id": 999999,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Plant not found"


def test_get_production_line():
    token = create_super_admin_token()
    plant_id = create_plant(token)

    create_response = client.post(
        "/production-lines",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "line_code": unique_value("LINE"),
            "name": "Assembly Line",
            "capacity": 700,
            "plant_id": plant_id,
        },
    )

    line_id = create_response.json()["id"]

    response = client.get(
        f"/production-lines/{line_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == line_id


def test_get_nonexistent_production_line():
    token = create_super_admin_token()

    response = client.get(
        "/production-lines/999999",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 404


def test_update_production_line():
    token = create_super_admin_token()
    plant_id = create_plant(token)

    create_response = client.post(
        "/production-lines",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "line_code": unique_value("LINE"),
            "name": "Old Line Name",
            "capacity": 500,
            "plant_id": plant_id,
        },
    )

    line_id = create_response.json()["id"]

    response = client.put(
        f"/production-lines/{line_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "name": "Updated Line Name",
            "capacity": 800,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated Line Name"
    assert data["capacity"] == 800


def test_update_production_line_status():
    token = create_super_admin_token()
    plant_id = create_plant(token)

    create_response = client.post(
        "/production-lines",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "line_code": unique_value("LINE"),
            "name": "Maintenance Test Line",
            "capacity": 500,
            "plant_id": plant_id,
        },
    )

    line_id = create_response.json()["id"]

    response = client.patch(
        f"/production-lines/{line_id}/status",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "status": "Maintenance"
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Maintenance"


def test_search_production_lines():
    token = create_super_admin_token()
    plant_id = create_plant(token)

    unique_name = unique_value("Assembly")

    client.post(
        "/production-lines",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "line_code": unique_value("LINE"),
            "name": unique_name,
            "capacity": 500,
            "plant_id": plant_id,
        },
    )

    response = client.get(
        "/production-lines",
        params={
            "search": unique_name,
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1
    assert any(item["name"] == unique_name for item in data)


def test_filter_production_lines_by_status():
    token = create_super_admin_token()
    plant_id = create_plant(token)

    client.post(
        "/production-lines",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "line_code": unique_value("LINE"),
            "name": "Inactive Test Line",
            "capacity": 500,
            "plant_id": plant_id,
            "status": "Inactive",
        },
    )

    response = client.get(
        "/production-lines",
        params={
            "status": "Inactive",
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1
    assert all(item["status"] == "Inactive" for item in data)


def test_filter_production_lines_by_plant():
    token = create_super_admin_token()
    plant_id = create_plant(token)

    client.post(
        "/production-lines",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "line_code": unique_value("LINE"),
            "name": "Plant Filter Line",
            "capacity": 500,
            "plant_id": plant_id,
        },
    )

    response = client.get(
        "/production-lines",
        params={
            "plant_id": plant_id,
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1
    assert all(item["plant_id"] == plant_id for item in data)


def test_worker_cannot_create_production_line():
    worker = register_user("Worker")

    token = login_user(
        worker["username"],
        worker["password"],
    )

    response = client.post(
        "/production-lines",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "line_code": unique_value("LINE"),
            "name": "Unauthorized Line",
            "capacity": 500,
            "plant_id": 1,
        },
    )

    assert response.status_code == 403


def test_invalid_capacity_rejected():
    token = create_super_admin_token()
    plant_id = create_plant(token)

    response = client.post(
        "/production-lines",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "line_code": unique_value("LINE"),
            "name": "Invalid Capacity Line",
            "capacity": 0,
            "plant_id": plant_id,
        },
    )

    assert response.status_code == 422


def test_delete_production_line():
    token = create_super_admin_token()
    plant_id = create_plant(token)

    create_response = client.post(
        "/production-lines",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "line_code": unique_value("LINE"),
            "name": "Delete Test Line",
            "capacity": 500,
            "plant_id": plant_id,
        },
    )

    line_id = create_response.json()["id"]

    delete_response = client.delete(
        f"/production-lines/{line_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert delete_response.status_code == 204

    get_response = client.get(
        f"/production-lines/{line_id}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert get_response.status_code == 404