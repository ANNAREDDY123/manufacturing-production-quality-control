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
    username = unique_name("order_admin")

    register_user(
        username,
        "Super Admin",
    )

    return login(username)


def create_plant(token: str) -> int:
    code = unique_name("OPLANT")

    response = client.post(
        "/plants",
        headers=headers(token),
        json={
            "plant_code": code,
            "name": f"Order Test Plant {code}",
            "description": "Production order test plant",
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
    code = unique_name("OLINE")

    response = client.post(
        "/production-lines",
        headers=headers(token),
        json={
            "line_code": code,
            "name": f"Order Test Line {code}",
            "capacity": 5000,
            "plant_id": plant_id,
            "supervisor_id": None,
            "status": "Active",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()["id"]


def create_product(token: str) -> int:
    code = unique_name("OPROD")

    response = client.post(
        "/products",
        headers=headers(token),
        json={
            "product_code": code,
            "name": f"Order Test Product {code}",
            "category": "Finished Goods",
            "sku": f"SKU_{uuid.uuid4().hex[:10]}",
            "unit": "Piece",
            "standard_production_time": 2.5,
            "status": "Active",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()["id"]


def create_supervisor() -> tuple[str, int]:
    username = unique_name("order_supervisor")

    register_user(
        username,
        "Production Supervisor",
    )

    token = login(username)

    response = client.get(
        "/auth/me",
        headers=headers(token),
    )

    assert response.status_code == 200

    return token, response.json()["id"]


def create_order(
    token: str,
    product_id: int,
    line_id: int,
    supervisor_id: int | None = None,
    priority: str = "Medium",
) -> dict:
    response = client.post(
        "/production-orders",
        headers=headers(token),
        json={
            "order_number": unique_name("PO"),
            "product_id": product_id,
            "quantity": 1000,
            "target_date": str(
                date.today() + timedelta(days=10)
            ),
            "production_line_id": line_id,
            "priority": priority,
            "supervisor_id": supervisor_id,
        },
    )

    assert response.status_code == 201, response.text

    return response.json()


def setup_order(token: str):
    plant_id = create_plant(token)

    line_id = create_production_line(
        token,
        plant_id,
    )

    product_id = create_product(token)

    return product_id, line_id


def test_production_order_creation():
    token = create_admin_token()

    product_id, line_id = setup_order(token)

    order = create_order(
        token,
        product_id,
        line_id,
    )

    assert order["order_number"].startswith("PO_")
    assert order["product_id"] == product_id
    assert order["production_line_id"] == line_id
    assert order["quantity"] == 1000
    assert order["priority"] == "Medium"
    assert order["status"] == "Draft"


def test_duplicate_order_number_rejected():
    token = create_admin_token()

    product_id, line_id = setup_order(token)

    order_number = unique_name("DUPPO")

    payload = {
        "order_number": order_number,
        "product_id": product_id,
        "quantity": 100,
        "target_date": str(
            date.today() + timedelta(days=5)
        ),
        "production_line_id": line_id,
        "priority": "High",
        "supervisor_id": None,
    }

    first = client.post(
        "/production-orders",
        headers=headers(token),
        json=payload,
    )

    assert first.status_code == 201, first.text

    second = client.post(
        "/production-orders",
        headers=headers(token),
        json=payload,
    )

    assert second.status_code == 400
    assert (
        second.json()["detail"]
        == "Production order number already exists"
    )


def test_invalid_product_rejected():
    token = create_admin_token()

    plant_id = create_plant(token)
    line_id = create_production_line(
        token,
        plant_id,
    )

    response = client.post(
        "/production-orders",
        headers=headers(token),
        json={
            "order_number": unique_name("BADPROD"),
            "product_id": 999999,
            "quantity": 100,
            "target_date": str(
                date.today() + timedelta(days=5)
            ),
            "production_line_id": line_id,
            "priority": "Medium",
            "supervisor_id": None,
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Product not found"
    )


def test_invalid_production_line_rejected():
    token = create_admin_token()

    product_id = create_product(token)

    response = client.post(
        "/production-orders",
        headers=headers(token),
        json={
            "order_number": unique_name("BADLINE"),
            "product_id": product_id,
            "quantity": 100,
            "target_date": str(
                date.today() + timedelta(days=5)
            ),
            "production_line_id": 999999,
            "priority": "Medium",
            "supervisor_id": None,
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Production line not found"
    )


def test_past_target_date_rejected():
    token = create_admin_token()

    product_id, line_id = setup_order(token)

    response = client.post(
        "/production-orders",
        headers=headers(token),
        json={
            "order_number": unique_name("PAST"),
            "product_id": product_id,
            "quantity": 100,
            "target_date": str(
                date.today() - timedelta(days=1)
            ),
            "production_line_id": line_id,
            "priority": "Medium",
            "supervisor_id": None,
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Target date cannot be in the past"
    )


def test_invalid_supervisor_rejected():
    token = create_admin_token()

    product_id, line_id = setup_order(token)

    response = client.post(
        "/production-orders",
        headers=headers(token),
        json={
            "order_number": unique_name("BADSUP"),
            "product_id": product_id,
            "quantity": 100,
            "target_date": str(
                date.today() + timedelta(days=5)
            ),
            "production_line_id": line_id,
            "priority": "Medium",
            "supervisor_id": 999999,
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Supervisor not found"
    )


def test_production_supervisor_assignment():
    token = create_admin_token()

    product_id, line_id = setup_order(token)

    _, supervisor_id = create_supervisor()

    order = create_order(
        token,
        product_id,
        line_id,
        supervisor_id=supervisor_id,
    )

    assert (
        order["supervisor_id"]
        == supervisor_id
    )


def test_non_supervisor_user_rejected():
    token = create_admin_token()

    product_id, line_id = setup_order(token)

    worker_username = unique_name(
        "order_worker"
    )

    register_user(
        worker_username,
        "Worker",
    )

    worker_token = login(
        worker_username
    )

    response = client.get(
        "/auth/me",
        headers=headers(worker_token),
    )

    assert response.status_code == 200

    worker_id = response.json()["id"]

    response = client.post(
        "/production-orders",
        headers=headers(token),
        json={
            "order_number": unique_name("BADROLE"),
            "product_id": product_id,
            "quantity": 100,
            "target_date": str(
                date.today() + timedelta(days=5)
            ),
            "production_line_id": line_id,
            "priority": "Medium",
            "supervisor_id": worker_id,
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Assigned user must have Production Supervisor role"
    )


def test_production_order_update():
    token = create_admin_token()

    product_id, line_id = setup_order(token)

    order = create_order(
        token,
        product_id,
        line_id,
    )

    response = client.put(
        f"/production-orders/{order['id']}",
        headers=headers(token),
        json={
            "quantity": 2500,
            "priority": "High",
            "target_date": str(
                date.today() + timedelta(days=20)
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["quantity"] == 2500
    assert data["priority"] == "High"


def test_draft_to_scheduled():
    token = create_admin_token()

    product_id, line_id = setup_order(token)

    order = create_order(
        token,
        product_id,
        line_id,
    )

    response = client.patch(
        f"/production-orders/{order['id']}/status",
        headers=headers(token),
        json={
            "status": "Scheduled",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Scheduled"


def test_scheduled_to_in_progress():
    token = create_admin_token()

    product_id, line_id = setup_order(token)

    order = create_order(
        token,
        product_id,
        line_id,
    )

    client.patch(
        f"/production-orders/{order['id']}/status",
        headers=headers(token),
        json={
            "status": "Scheduled",
        },
    )

    response = client.patch(
        f"/production-orders/{order['id']}/status",
        headers=headers(token),
        json={
            "status": "In Progress",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "In Progress"


def test_in_progress_to_paused_and_back():
    token = create_admin_token()

    product_id, line_id = setup_order(token)

    order = create_order(
        token,
        product_id,
        line_id,
    )

    client.patch(
        f"/production-orders/{order['id']}/status",
        headers=headers(token),
        json={
            "status": "Scheduled",
        },
    )

    client.patch(
        f"/production-orders/{order['id']}/status",
        headers=headers(token),
        json={
            "status": "In Progress",
        },
    )

    paused = client.patch(
        f"/production-orders/{order['id']}/status",
        headers=headers(token),
        json={
            "status": "Paused",
        },
    )

    assert paused.status_code == 200
    assert paused.json()["status"] == "Paused"

    resumed = client.patch(
        f"/production-orders/{order['id']}/status",
        headers=headers(token),
        json={
            "status": "In Progress",
        },
    )

    assert resumed.status_code == 200
    assert resumed.json()["status"] == "In Progress"


def test_in_progress_to_completed():
    token = create_admin_token()

    product_id, line_id = setup_order(token)

    order = create_order(
        token,
        product_id,
        line_id,
    )

    client.patch(
        f"/production-orders/{order['id']}/status",
        headers=headers(token),
        json={
            "status": "Scheduled",
        },
    )

    client.patch(
        f"/production-orders/{order['id']}/status",
        headers=headers(token),
        json={
            "status": "In Progress",
        },
    )

    response = client.patch(
        f"/production-orders/{order['id']}/status",
        headers=headers(token),
        json={
            "status": "Completed",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Completed"


def test_draft_to_cancelled():
    token = create_admin_token()

    product_id, line_id = setup_order(token)

    order = create_order(
        token,
        product_id,
        line_id,
    )

    response = client.patch(
        f"/production-orders/{order['id']}/status",
        headers=headers(token),
        json={
            "status": "Cancelled",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Cancelled"


def test_invalid_draft_to_in_progress():
    token = create_admin_token()

    product_id, line_id = setup_order(token)

    order = create_order(
        token,
        product_id,
        line_id,
    )

    response = client.patch(
        f"/production-orders/{order['id']}/status",
        headers=headers(token),
        json={
            "status": "In Progress",
        },
    )

    assert response.status_code == 400
    assert "Invalid status transition" in (
        response.json()["detail"]
    )


def test_completed_order_cannot_change_status():
    token = create_admin_token()

    product_id, line_id = setup_order(token)

    order = create_order(
        token,
        product_id,
        line_id,
    )

    for order_status in (
        "Scheduled",
        "In Progress",
        "Completed",
    ):
        response = client.patch(
            f"/production-orders/{order['id']}/status",
            headers=headers(token),
            json={
                "status": order_status,
            },
        )

        assert response.status_code == 200

    response = client.patch(
        f"/production-orders/{order['id']}/status",
        headers=headers(token),
        json={
            "status": "Cancelled",
        },
    )

    assert response.status_code == 400
    assert "Invalid status transition" in (
        response.json()["detail"]
    )


def test_cancelled_order_cannot_change_status():
    token = create_admin_token()

    product_id, line_id = setup_order(token)

    order = create_order(
        token,
        product_id,
        line_id,
    )

    response = client.patch(
        f"/production-orders/{order['id']}/status",
        headers=headers(token),
        json={
            "status": "Cancelled",
        },
    )

    assert response.status_code == 200

    response = client.patch(
        f"/production-orders/{order['id']}/status",
        headers=headers(token),
        json={
            "status": "Scheduled",
        },
    )

    assert response.status_code == 400
    assert "Invalid status transition" in (
        response.json()["detail"]
    )


def test_completed_order_cannot_be_updated():
    token = create_admin_token()

    product_id, line_id = setup_order(token)

    order = create_order(
        token,
        product_id,
        line_id,
    )

    for order_status in (
        "Scheduled",
        "In Progress",
        "Completed",
    ):
        response = client.patch(
            f"/production-orders/{order['id']}/status",
            headers=headers(token),
            json={
                "status": order_status,
            },
        )

        assert response.status_code == 200

    response = client.put(
        f"/production-orders/{order['id']}",
        headers=headers(token),
        json={
            "quantity": 5000,
        },
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "Only Draft or Scheduled orders can be modified"
    )


def test_order_details():
    token = create_admin_token()

    product_id, line_id = setup_order(token)

    order = create_order(
        token,
        product_id,
        line_id,
    )

    response = client.get(
        f"/production-orders/{order['id']}",
        headers=headers(token),
    )

    assert response.status_code == 200
    assert response.json()["id"] == order["id"]


def test_order_not_found():
    token = create_admin_token()

    response = client.get(
        "/production-orders/999999",
        headers=headers(token),
    )

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == "Production order not found"
    )


def test_order_search_and_filters():
    token = create_admin_token()

    product_id, line_id = setup_order(token)

    order = create_order(
        token,
        product_id,
        line_id,
        priority="Urgent",
    )

    search_response = client.get(
        "/production-orders",
        headers=headers(token),
        params={
            "search": order["order_number"],
        },
    )

    assert search_response.status_code == 200

    search_data = search_response.json()

    assert len(search_data) >= 1
    assert (
        search_data[0]["order_number"]
        == order["order_number"]
    )

    filter_response = client.get(
        "/production-orders",
        headers=headers(token),
        params={
            "priority": "Urgent",
            "product_id": product_id,
            "production_line_id": line_id,
        },
    )

    assert filter_response.status_code == 200

    filtered = filter_response.json()

    assert all(
        item["priority"] == "Urgent"
        and item["product_id"] == product_id
        and item["production_line_id"] == line_id
        for item in filtered
    )


def test_pagination():
    token = create_admin_token()

    product_id, line_id = setup_order(token)

    for _ in range(3):
        create_order(
            token,
            product_id,
            line_id,
        )

    response = client.get(
        "/production-orders",
        headers=headers(token),
        params={
            "skip": 1,
            "limit": 1,
        },
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_worker_cannot_create_order():
    admin_token = create_admin_token()

    product_id, line_id = setup_order(
        admin_token
    )

    username = unique_name(
        "production_order_worker"
    )

    register_user(
        username,
        "Worker",
    )

    worker_token = login(username)

    response = client.post(
        "/production-orders",
        headers=headers(worker_token),
        json={
            "order_number": unique_name("WORKERPO"),
            "product_id": product_id,
            "quantity": 100,
            "target_date": str(
                date.today() + timedelta(days=5)
            ),
            "production_line_id": line_id,
            "priority": "Medium",
            "supervisor_id": None,
        },
    )

    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "Insufficient permissions"
    )


def test_production_supervisor_can_update_status():
    admin_token = create_admin_token()

    product_id, line_id = setup_order(
        admin_token
    )

    order = create_order(
        admin_token,
        product_id,
        line_id,
    )

    username = unique_name(
        "status_supervisor"
    )

    register_user(
        username,
        "Production Supervisor",
    )

    supervisor_token = login(username)

    response = client.patch(
        f"/production-orders/{order['id']}/status",
        headers=headers(supervisor_token),
        json={
            "status": "Scheduled",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Scheduled"