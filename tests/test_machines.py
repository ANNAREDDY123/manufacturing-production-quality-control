from datetime import date, timedelta
import uuid

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def unique_name(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def register_user(
    username: str,
    role: str,
) -> None:
    response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "full_name": username,
            "password": "Test@12345",
            "role": role,
        },
    )

    assert response.status_code == 201, response.text


def login(username: str) -> str:
    response = client.post(
        "/auth/login",
        json={
            "username": username,
            "password": "Test@12345",
        },
    )

    assert response.status_code == 200, response.text

    return response.json()["access_token"]


def headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}"
    }


def create_admin_token() -> str:
    username = unique_name("machine_admin")

    register_user(
        username,
        "Super Admin",
    )

    return login(username)


def create_plant(token: str) -> int:
    code = unique_name("MPLANT")

    response = client.post(
        "/plants",
        headers=headers(token),
        json={
            "plant_code": code,
            "name": f"Machine Test Plant {code}",
            "description": "Machine test plant",
            "address": "Industrial Area",
            "city": "Hyderabad",
            "state": "Telangana",
            "country": "India",
            "capacity": 10000,
            "manager_id": None,
            "status": "Active",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()["id"]


def create_production_line(
    token: str,
    plant_id: int,
) -> int:
    code = unique_name("MLINE")

    response = client.post(
        "/production-lines",
        headers=headers(token),
        json={
            "line_code": code,
            "name": f"Machine Test Line {code}",
            "capacity": 5000,
            "plant_id": plant_id,
            "supervisor_id": None,
            "status": "Active",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()["id"]


def create_machine(
    token: str,
    line_id: int,
    status: str = "Idle",
) -> dict:
    code = unique_name("MACHINE")

    response = client.post(
        "/machines",
        headers=headers(token),
        json={
            "machine_code": code,
            "name": f"Test Machine {code}",
            "machine_type": "CNC",
            "production_line_id": line_id,
            "installation_date": str(date.today()),
            "status": status,
            "operating_hours": 100,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def test_machine_creation():
    token = create_admin_token()

    plant_id = create_plant(token)
    line_id = create_production_line(
        token,
        plant_id,
    )

    machine = create_machine(
        token,
        line_id,
    )

    assert machine["machine_code"].startswith(
        "MACHINE_"
    )
    assert machine["production_line_id"] == line_id
    assert machine["machine_type"] == "CNC"
    assert machine["status"] == "Idle"
    assert machine["operating_hours"] == 100


def test_duplicate_machine_code_rejected():
    token = create_admin_token()

    plant_id = create_plant(token)
    line_id = create_production_line(
        token,
        plant_id,
    )

    code = unique_name("DUPMACHINE")

    payload = {
        "machine_code": code,
        "name": "Machine One",
        "machine_type": "CNC",
        "production_line_id": line_id,
        "installation_date": str(date.today()),
        "status": "Idle",
        "operating_hours": 0,
    }

    first = client.post(
        "/machines",
        headers=headers(token),
        json=payload,
    )

    assert first.status_code == 201, first.text

    second = client.post(
        "/machines",
        headers=headers(token),
        json=payload,
    )

    assert second.status_code == 400
    assert (
        second.json()["detail"]
        == "Machine code already registered"
    )


def test_invalid_production_line_rejected():
    token = create_admin_token()

    response = client.post(
        "/machines",
        headers=headers(token),
        json={
            "machine_code": unique_name("INVALIDLINE"),
            "name": "Invalid Line Machine",
            "machine_type": "CNC",
            "production_line_id": 999999,
            "installation_date": str(date.today()),
            "status": "Idle",
            "operating_hours": 0,
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Production line not found"
    )


def test_future_installation_date_rejected():
    token = create_admin_token()

    plant_id = create_plant(token)
    line_id = create_production_line(
        token,
        plant_id,
    )

    future_date = date.today() + timedelta(
        days=10
    )

    response = client.post(
        "/machines",
        headers=headers(token),
        json={
            "machine_code": unique_name("FUTURE"),
            "name": "Future Machine",
            "machine_type": "CNC",
            "production_line_id": line_id,
            "installation_date": str(future_date),
            "status": "Idle",
            "operating_hours": 0,
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Installation date cannot be in the future"
    )


def test_machine_update():
    token = create_admin_token()

    plant_id = create_plant(token)
    line_id = create_production_line(
        token,
        plant_id,
    )

    machine = create_machine(
        token,
        line_id,
    )

    response = client.put(
        f"/machines/{machine['id']}",
        headers=headers(token),
        json={
            "name": "Updated CNC Machine",
            "machine_type": "Advanced CNC",
            "operating_hours": 250,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated CNC Machine"
    assert data["machine_type"] == "Advanced CNC"
    assert data["operating_hours"] == 250


def test_machine_status_update():
    token = create_admin_token()

    plant_id = create_plant(token)
    line_id = create_production_line(
        token,
        plant_id,
    )

    machine = create_machine(
        token,
        line_id,
    )

    response = client.patch(
        f"/machines/{machine['id']}/status",
        headers=headers(token),
        json={
            "status": "Running",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Running"


def test_machine_all_statuses():
    token = create_admin_token()

    plant_id = create_plant(token)
    line_id = create_production_line(
        token,
        plant_id,
    )

    machine = create_machine(
        token,
        line_id,
    )

    statuses = [
        "Running",
        "Idle",
        "Maintenance",
        "Breakdown",
        "Decommissioned",
    ]

    for machine_status in statuses:
        response = client.patch(
            f"/machines/{machine['id']}/status",
            headers=headers(token),
            json={
                "status": machine_status,
            },
        )

        assert response.status_code == 200
        assert (
            response.json()["status"]
            == machine_status
        )


def test_decommissioned_machine_cannot_be_reactivated():
    token = create_admin_token()

    plant_id = create_plant(token)
    line_id = create_production_line(
        token,
        plant_id,
    )

    machine = create_machine(
        token,
        line_id,
    )

    decommission = client.patch(
        f"/machines/{machine['id']}/status",
        headers=headers(token),
        json={
            "status": "Decommissioned",
        },
    )

    assert decommission.status_code == 200

    reactivate = client.patch(
        f"/machines/{machine['id']}/status",
        headers=headers(token),
        json={
            "status": "Running",
        },
    )

    assert reactivate.status_code == 400
    assert (
        reactivate.json()["detail"]
        == "Decommissioned machine cannot be reactivated"
    )


def test_decommissioned_machine_cannot_be_updated():
    token = create_admin_token()

    plant_id = create_plant(token)
    line_id = create_production_line(
        token,
        plant_id,
    )

    machine = create_machine(
        token,
        line_id,
    )

    decommission = client.patch(
        f"/machines/{machine['id']}/status",
        headers=headers(token),
        json={
            "status": "Decommissioned",
        },
    )

    assert decommission.status_code == 200

    response = client.put(
        f"/machines/{machine['id']}",
        headers=headers(token),
        json={
            "name": "Should Fail",
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Decommissioned machine cannot be modified"
    )


def test_machine_list_search_and_filter():
    token = create_admin_token()

    plant_id = create_plant(token)
    line_id = create_production_line(
        token,
        plant_id,
    )

    machine = create_machine(
        token,
        line_id,
    )

    search_response = client.get(
        "/machines",
        headers=headers(token),
        params={
            "search": machine["machine_code"],
        },
    )

    assert search_response.status_code == 200

    search_data = search_response.json()

    assert len(search_data) >= 1
    assert search_data[0]["machine_code"] == (
        machine["machine_code"]
    )

    filter_response = client.get(
        "/machines",
        headers=headers(token),
        params={
            "status_filter": "Idle",
            "production_line_id": line_id,
        },
    )

    assert filter_response.status_code == 200

    filtered = filter_response.json()

    assert all(
        item["status"] == "Idle"
        and item["production_line_id"] == line_id
        for item in filtered
    )


def test_machine_details():
    token = create_admin_token()

    plant_id = create_plant(token)
    line_id = create_production_line(
        token,
        plant_id,
    )

    machine = create_machine(
        token,
        line_id,
    )

    response = client.get(
        f"/machines/{machine['id']}",
        headers=headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == machine["id"]


def test_machine_not_found():
    token = create_admin_token()

    response = client.get(
        "/machines/999999",
        headers=headers(token),
    )

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "Machine not found"
    )


def test_worker_cannot_create_machine():
    admin_token = create_admin_token()

    plant_id = create_plant(admin_token)
    line_id = create_production_line(
        admin_token,
        plant_id,
    )

    worker_username = unique_name(
        "machine_worker"
    )

    register_user(
        worker_username,
        "Worker",
    )

    worker_token = login(
        worker_username
    )

    response = client.post(
        "/machines",
        headers=headers(worker_token),
        json={
            "machine_code": unique_name(
                "WORKER_MACHINE"
            ),
            "name": "Worker Machine",
            "machine_type": "CNC",
            "production_line_id": line_id,
            "installation_date": str(date.today()),
            "status": "Idle",
            "operating_hours": 0,
        },
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "Insufficient permissions"
    )


def test_maintenance_engineer_can_create_machine():
    admin_token = create_admin_token()

    plant_id = create_plant(admin_token)

    line_id = create_production_line(
        admin_token,
        plant_id,
    )

    username = unique_name(
        "maintenance_engineer"
    )

    register_user(
        username,
        "Maintenance Engineer",
    )

    maintenance_token = login(username)

    response = client.post(
        "/machines",
        headers=headers(maintenance_token),
        json={
            "machine_code": unique_name("MAINT"),
            "name": "Maintenance Machine",
            "machine_type": "CNC",
            "production_line_id": line_id,
            "installation_date": str(date.today()),
            "status": "Maintenance",
            "operating_hours": 50,
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["status"] == "Maintenance"
    assert data["production_line_id"] == line_id
    assert data["machine_type"] == "CNC"


def test_worker_cannot_view_machine():
    admin_token = create_admin_token()

    plant_id = create_plant(admin_token)
    line_id = create_production_line(
        admin_token,
        plant_id,
    )

    machine = create_machine(
        admin_token,
        line_id,
    )

    worker_username = unique_name(
        "machine_view_worker"
    )

    register_user(
        worker_username,
        "Worker",
    )

    worker_token = login(
        worker_username
    )

    response = client.get(
        f"/machines/{machine['id']}",
        headers=headers(worker_token),
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "Insufficient permissions"
    )


def test_decommissioned_machine_can_be_deleted():
    token = create_admin_token()

    plant_id = create_plant(token)
    line_id = create_production_line(
        token,
        plant_id,
    )

    machine = create_machine(
        token,
        line_id,
    )

    response = client.patch(
        f"/machines/{machine['id']}/status",
        headers=headers(token),
        json={
            "status": "Decommissioned",
        },
    )

    assert response.status_code == 200

    delete_response = client.delete(
        f"/machines/{machine['id']}",
        headers=headers(token),
    )

    assert delete_response.status_code == 204

    get_response = client.get(
        f"/machines/{machine['id']}",
        headers=headers(token),
    )

    assert get_response.status_code == 404


def test_active_machine_cannot_be_deleted():
    token = create_admin_token()

    plant_id = create_plant(token)
    line_id = create_production_line(
        token,
        plant_id,
    )

    machine = create_machine(
        token,
        line_id,
    )

    response = client.delete(
        f"/machines/{machine['id']}",
        headers=headers(token),
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Only decommissioned machines can be deleted"
    )