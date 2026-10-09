from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def unique_username(prefix: str) -> str:
    import uuid

    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def create_user(
    role: str = "Super Admin",
) -> tuple[str, str]:
    username = unique_username("dashboard_user")
    password = "Test@12345"

    response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "full_name": "Dashboard Test User",
            "password": password,
            "role": role,
        },
    )

    assert response.status_code == 201, response.text

    return username, password


def login(
    username: str,
    password: str,
) -> str:
    response = client.post(
        "/auth/login",
        json={
            "username": username,
            "password": password,
        },
    )

    assert response.status_code == 200, response.text

    return response.json()["access_token"]


def headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
    }


def test_dashboard_requires_authentication():
    response = client.get("/dashboard")

    assert response.status_code in {
        401,
        403,
    }


def test_dashboard_overview_for_super_admin():
    username, password = create_user(
        "Super Admin",
    )

    token = login(
        username,
        password,
    )

    response = client.get(
        "/dashboard",
        headers=headers(token),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    expected_fields = [
        "total_plants",
        "active_plants",
        "total_production_lines",
        "active_production_lines",
        "total_products",
        "active_products",
        "total_raw_materials",
        "low_stock_materials",
        "total_machines",
        "total_workers",
        "total_production_orders",
        "total_production_batches",
        "total_quality_inspections",
        "total_defects",
        "total_maintenance_records",
        "total_downtime_records",
        "total_inventory_movements",
        "total_production_approvals",
        "pending_production_approvals",
    ]

    for field in expected_fields:
        assert field in data
        assert isinstance(data[field], int)


def test_production_dashboard():
    username, password = create_user(
        "Production Manager",
    )

    token = login(
        username,
        password,
    )

    response = client.get(
        "/dashboard/production",
        headers=headers(token),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert "total_orders" in data
    assert "active_orders" in data
    assert "completed_orders" in data
    assert "total_batches" in data
    assert "total_order_quantity" in data
    assert "total_batch_quantity" in data
    assert "order_completion_percentage" in data
    assert "batch_completion_percentage" in data

    assert data["total_orders"] >= 0
    assert data["total_batches"] >= 0


def test_quality_dashboard():
    username, password = create_user(
        "Quality Manager",
    )

    token = login(
        username,
        password,
    )

    response = client.get(
        "/dashboard/quality",
        headers=headers(token),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert "total_inspections" in data
    assert "pending_inspections" in data
    assert "passed_inspections" in data
    assert "failed_inspections" in data
    assert "total_defects" in data
    assert "critical_defects" in data
    assert "inspection_pass_percentage" in data
    assert "defect_resolution_percentage" in data


def test_maintenance_dashboard():
    username, password = create_user(
        "Maintenance Engineer",
    )

    token = login(
        username,
        password,
    )

    response = client.get(
        "/dashboard/maintenance",
        headers=headers(token),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert "total_machines" in data
    assert "machines_under_maintenance" in data
    assert "total_maintenance_records" in data
    assert "scheduled_maintenance" in data
    assert "in_progress_maintenance" in data
    assert "completed_maintenance" in data
    assert "total_downtime_records" in data


def test_inventory_dashboard():
    username, password = create_user(
        "Store Manager",
    )

    token = login(
        username,
        password,
    )

    response = client.get(
        "/dashboard/inventory",
        headers=headers(token),
    )

    assert response.status_code == 200, response.text

    data = response.json()

    assert "total_materials" in data
    assert "active_materials" in data
    assert "low_stock_materials" in data
    assert "total_inventory_movements" in data
    assert "stock_in_movements" in data
    assert "stock_out_movements" in data
    assert "adjustment_movements" in data


def test_worker_cannot_access_dashboard():
    username, password = create_user(
        "Worker",
    )

    token = login(
        username,
        password,
    )

    response = client.get(
        "/dashboard",
        headers=headers(token),
    )

    assert response.status_code == 403