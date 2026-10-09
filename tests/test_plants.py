import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.db.init_db import init_db

client = TestClient(app)

init_db()
def create_user(
    role: str,
    prefix: str,
):
    unique_id = uuid.uuid4().hex[:8]

    response = client.post(
        "/auth/register",
        json={
            "username": f"{prefix}_{unique_id}",
            "email": f"{unique_id}_{prefix}@test.com",
            "full_name": f"Test {role}",
            "password": "Test@12345",
            "role": role,
        },
    )

    assert response.status_code == 201

    return response.json()


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


def create_admin_token():
    unique_id = uuid.uuid4().hex[:8]

    user = create_user(
        "Super Admin",
        f"plant_admin_{unique_id}",
    )

    return login_user(user["username"])


def test_create_plant():
    token = create_admin_token()

    plant_code = f"PLANT-{uuid.uuid4().hex[:8]}"

    response = client.post(
        "/plants",
        headers=auth_headers(token),
        json={
            "plant_code": plant_code,
            "name": "Hyderabad Manufacturing Plant",
            "description": "Main production facility",
            "address": "Industrial Area",
            "city": "Hyderabad",
            "state": "Telangana",
            "country": "India",
            "capacity": 10000,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["plant_code"] == plant_code
    assert data["name"] == "Hyderabad Manufacturing Plant"
    assert data["capacity"] == 10000
    assert data["status"] == "Active"


def test_create_plant_rejects_duplicate_code():
    token = create_admin_token()

    plant_code = f"DUP-{uuid.uuid4().hex[:8]}"

    payload = {
        "plant_code": plant_code,
        "name": "Duplicate Test Plant",
        "address": "Industrial Area",
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India",
        "capacity": 5000,
    }

    first_response = client.post(
        "/plants",
        headers=auth_headers(token),
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/plants",
        headers=auth_headers(token),
        json=payload,
    )

    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Plant code already exists"


def test_get_plant():
    token = create_admin_token()

    plant_code = f"GET-{uuid.uuid4().hex[:8]}"

    create_response = client.post(
        "/plants",
        headers=auth_headers(token),
        json={
            "plant_code": plant_code,
            "name": "Get Plant Test",
            "address": "Test Address",
            "city": "Hyderabad",
            "state": "Telangana",
            "country": "India",
            "capacity": 2500,
        },
    )

    assert create_response.status_code == 201

    plant_id = create_response.json()["id"]

    response = client.get(
        f"/plants/{plant_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == plant_id
    assert response.json()["plant_code"] == plant_code


def test_get_nonexistent_plant():
    token = create_admin_token()

    response = client.get(
        "/plants/999999999",
        headers=auth_headers(token),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Plant not found"


def test_update_plant():
    token = create_admin_token()

    plant_code = f"UPDATE-{uuid.uuid4().hex[:8]}"

    create_response = client.post(
        "/plants",
        headers=auth_headers(token),
        json={
            "plant_code": plant_code,
            "name": "Original Plant",
            "address": "Original Address",
            "city": "Hyderabad",
            "state": "Telangana",
            "country": "India",
            "capacity": 3000,
        },
    )

    assert create_response.status_code == 201

    plant_id = create_response.json()["id"]

    response = client.put(
        f"/plants/{plant_id}",
        headers=auth_headers(token),
        json={
            "name": "Updated Plant",
            "address": "Updated Address",
            "capacity": 7500,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated Plant"
    assert data["address"] == "Updated Address"
    assert data["capacity"] == 7500


def test_update_plant_status():
    token = create_admin_token()

    plant_code = f"STATUS-{uuid.uuid4().hex[:8]}"

    create_response = client.post(
        "/plants",
        headers=auth_headers(token),
        json={
            "plant_code": plant_code,
            "name": "Status Test Plant",
            "address": "Test Address",
            "city": "Hyderabad",
            "state": "Telangana",
            "country": "India",
            "capacity": 4000,
        },
    )

    assert create_response.status_code == 201

    plant_id = create_response.json()["id"]

    response = client.patch(
        f"/plants/{plant_id}/status",
        headers=auth_headers(token),
        json={
            "status": "Maintenance",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Maintenance"


def test_list_plants_with_search():
    token = create_admin_token()

    unique_id = uuid.uuid4().hex[:8]

    response = client.post(
        "/plants",
        headers=auth_headers(token),
        json={
            "plant_code": f"SEARCH-{unique_id}",
            "name": f"Search Manufacturing {unique_id}",
            "address": "Search Address",
            "city": "Hyderabad",
            "state": "Telangana",
            "country": "India",
            "capacity": 6000,
        },
    )

    assert response.status_code == 201

    list_response = client.get(
        "/plants",
        headers=auth_headers(token),
        params={
            "search": unique_id,
        },
    )

    assert list_response.status_code == 200

    plants = list_response.json()

    assert len(plants) >= 1
    assert any(
        plant["plant_code"] == f"SEARCH-{unique_id}"
        for plant in plants
    )


def test_worker_cannot_create_plant():
    user = create_user(
        "Worker",
        f"plant_worker_{uuid.uuid4().hex[:8]}",
    )

    token = login_user(user["username"])

    response = client.post(
        "/plants",
        headers=auth_headers(token),
        json={
            "plant_code": f"WORKER-{uuid.uuid4().hex[:8]}",
            "name": "Unauthorized Plant",
            "address": "Test Address",
            "city": "Hyderabad",
            "state": "Telangana",
            "country": "India",
            "capacity": 1000,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_invalid_capacity_rejected():
    token = create_admin_token()

    response = client.post(
        "/plants",
        headers=auth_headers(token),
        json={
            "plant_code": f"INVALID-{uuid.uuid4().hex[:8]}",
            "name": "Invalid Capacity Plant",
            "address": "Test Address",
            "city": "Hyderabad",
            "state": "Telangana",
            "country": "India",
            "capacity": 0,
        },
    )

    assert response.status_code == 422