import uuid

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def unique_value(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def create_user(
    role: str = "Super Admin",
):
    username = unique_value("report_user")

    response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": f"{username}@example.com",
            "full_name": "Reports Test User",
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


def test_reports_requires_authentication():
    response = client.get("/reports")

    assert response.status_code == 401


def test_reports_overview():
    token = create_token()

    response = client.get(
        "/reports",
        headers=headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert "total_plants" in data
    assert "total_production_orders" in data
    assert "total_production_batches" in data
    assert "total_quality_inspections" in data
    assert "total_defects" in data
    assert "total_maintenance_records" in data
    assert "total_downtime_records" in data
    assert "total_inventory_movements" in data
    assert "total_production_approvals" in data


def test_production_report():
    token = create_token()

    response = client.get(
        "/reports/production",
        headers=headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert "total_orders" in data
    assert "active_orders" in data
    assert "completed_orders" in data
    assert "cancelled_orders" in data
    assert "total_order_quantity" in data

    assert "total_batches" in data
    assert "active_batches" in data
    assert "completed_batches" in data
    assert "cancelled_batches" in data
    assert "total_batch_quantity" in data

    assert "order_completion_percentage" in data
    assert "batch_completion_percentage" in data

    assert data["order_completion_percentage"] >= 0
    assert data["batch_completion_percentage"] >= 0


def test_quality_report():
    token = create_token()

    response = client.get(
        "/reports/quality",
        headers=headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert "total_inspections" in data
    assert "pending_inspections" in data
    assert "passed_inspections" in data
    assert "failed_inspections" in data
    assert "cancelled_inspections" in data

    assert "inspection_pass_percentage" in data

    assert "total_defects" in data
    assert "open_defects" in data
    assert "resolved_defects" in data
    assert "critical_defects" in data
    assert "defect_resolution_percentage" in data

    assert data["inspection_pass_percentage"] >= 0
    assert data["defect_resolution_percentage"] >= 0


def test_inventory_report():
    token = create_token()

    response = client.get(
        "/reports/inventory",
        headers=headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert "total_materials" in data
    assert "active_materials" in data
    assert "inactive_materials" in data
    assert "low_stock_materials" in data

    assert "total_inventory_movements" in data
    assert "stock_in_movements" in data
    assert "stock_out_movements" in data
    assert "adjustment_movements" in data


def test_maintenance_report():
    token = create_token()

    response = client.get(
        "/reports/maintenance",
        headers=headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert "total_machines" in data
    assert "machines_under_maintenance" in data
    assert "total_maintenance_records" in data
    assert "scheduled_maintenance" in data
    assert "in_progress_maintenance" in data
    assert "completed_maintenance" in data
    assert "cancelled_maintenance" in data
    assert "total_downtime_records" in data


def test_downtime_report():
    token = create_token()

    response = client.get(
        "/reports/downtime",
        headers=headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert "total_downtime_records" in data
    assert "open_downtime_records" in data
    assert "in_progress_downtime_records" in data
    assert "resolved_downtime_records" in data
    assert "cancelled_downtime_records" in data
    assert "total_duration_hours" in data

    assert data["total_duration_hours"] >= 0


def test_production_approval_report():
    token = create_token()

    response = client.get(
        "/reports/production-approvals",
        headers=headers(token),
    )

    assert response.status_code == 200

    data = response.json()

    assert "total_approvals" in data
    assert "pending_approvals" in data
    assert "approved_approvals" in data
    assert "rejected_approvals" in data
    assert "cancelled_approvals" in data


def test_worker_cannot_access_reports():
    token = create_token("Worker")

    response = client.get(
        "/reports",
        headers=headers(token),
    )

    assert response.status_code == 403