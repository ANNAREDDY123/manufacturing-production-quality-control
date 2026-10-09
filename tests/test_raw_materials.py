import uuid

from fastapi.testclient import TestClient

from app.db.init_db import init_db
from app.main import app


client = TestClient(app)

init_db()


def unique_value(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def register_user(role: str = "Super Admin"):
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

    return username, "Test@12345"


def login_user(
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

    assert response.status_code == 200

    return response.json()["access_token"]


def create_token(
    role: str = "Super Admin",
) -> str:
    username, password = register_user(role)

    return login_user(
        username,
        password,
    )


def create_material(
    token: str,
    quantity: float = 100,
) -> dict:

    response = client.post(
        "/raw-materials",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "material_code": unique_value("MAT"),
            "name": "Steel Sheet",
            "category": "Metal",
            "unit": "Kg",
            "supplier": "ABC Metals",
            "available_quantity": quantity,
            "minimum_stock": 20,
            "reorder_level": 30,
        },
    )

    assert response.status_code == 201

    return response.json()


def test_create_raw_material():
    token = create_token()

    material = create_material(
        token,
        quantity=100,
    )

    assert material["available_quantity"] == 100
    assert material["status"] == "Active"
    assert material["unit"] == "Kg"


def test_duplicate_material_code_rejected():
    token = create_token()

    material_code = unique_value("MAT")

    payload = {
        "material_code": material_code,
        "name": "Steel",
        "category": "Metal",
        "unit": "Kg",
        "supplier": "Supplier A",
        "available_quantity": 100,
        "minimum_stock": 20,
        "reorder_level": 30,
    }

    first = client.post(
        "/raw-materials",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=payload,
    )

    assert first.status_code == 201

    payload["name"] = "Another Steel"

    second = client.post(
        "/raw-materials",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=payload,
    )

    assert second.status_code == 400
    assert second.json()["detail"] == (
        "Material code already exists"
    )


def test_get_raw_material():
    token = create_token()

    material = create_material(token)

    response = client.get(
        f"/raw-materials/{material['id']}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == material["id"]


def test_update_raw_material():
    token = create_token()

    material = create_material(token)

    response = client.put(
        f"/raw-materials/{material['id']}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "name": "Updated Steel",
            "supplier": "XYZ Metals",
            "minimum_stock": 25,
            "reorder_level": 40,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated Steel"
    assert data["supplier"] == "XYZ Metals"
    assert data["minimum_stock"] == 25
    assert data["reorder_level"] == 40


def test_update_material_status():
    token = create_token()

    material = create_material(token)

    response = client.patch(
        f"/raw-materials/{material['id']}/status",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "status": "Inactive"
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Inactive"


def test_search_materials():
    token = create_token()

    material_name = unique_value("Steel")

    response = client.post(
        "/raw-materials",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "material_code": unique_value("MAT"),
            "name": material_name,
            "category": "Metal",
            "unit": "Kg",
            "supplier": "Supplier",
            "available_quantity": 50,
            "minimum_stock": 10,
            "reorder_level": 20,
        },
    )

    assert response.status_code == 201

    response = client.get(
        "/raw-materials",
        params={
            "search": material_name,
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1
    assert any(
        item["name"] == material_name
        for item in data
    )


def test_filter_low_stock_materials():
    token = create_token()

    create_material(
        token,
        quantity=10,
    )

    response = client.get(
        "/raw-materials",
        params={
            "low_stock": True,
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1

    assert all(
        item["available_quantity"]
        <= item["reorder_level"]
        for item in data
    )


def test_stock_in():
    token = create_token()

    material = create_material(
        token,
        quantity=100,
    )

    response = client.post(
        f"/raw-materials/{material['id']}/stock-in",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "quantity": 50,
            "reference": "PO-001",
            "remarks": "New material received",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["movement_type"] == "Stock In"
    assert data["quantity"] == 50
    assert data["previous_quantity"] == 100
    assert data["new_quantity"] == 150


def test_stock_out():
    token = create_token()

    material = create_material(
        token,
        quantity=100,
    )

    response = client.post(
        f"/raw-materials/{material['id']}/stock-out",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "quantity": 40,
            "reference": "PROD-001",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["movement_type"] == "Stock Out"
    assert data["quantity"] == 40
    assert data["previous_quantity"] == 100
    assert data["new_quantity"] == 60


def test_negative_inventory_prevented():
    token = create_token()

    material = create_material(
        token,
        quantity=20,
    )

    response = client.post(
        f"/raw-materials/{material['id']}/stock-out",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "quantity": 50,
        },
    )

    assert response.status_code == 400

    assert response.json()["detail"] == (
        "Insufficient inventory: stock cannot become negative"
    )


def test_stock_adjustment():
    token = create_token()

    material = create_material(
        token,
        quantity=100,
    )

    response = client.post(
        f"/raw-materials/{material['id']}/adjust-stock",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "quantity": 75,
            "reference": "Physical Count",
            "remarks": "Inventory reconciliation",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["movement_type"] == "Adjustment"
    assert data["quantity"] == 75
    assert data["previous_quantity"] == 100
    assert data["new_quantity"] == 75


def test_inventory_history():
    token = create_token()

    material = create_material(
        token,
        quantity=100,
    )

    client.post(
        f"/raw-materials/{material['id']}/stock-in",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "quantity": 20,
        },
    )

    client.post(
        f"/raw-materials/{material['id']}/stock-out",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "quantity": 10,
        },
    )

    response = client.get(
        f"/raw-materials/{material['id']}/history",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 3


def test_inactive_material_cannot_receive_stock():
    token = create_token()

    material = create_material(token)

    client.patch(
        f"/raw-materials/{material['id']}/status",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "status": "Inactive"
        },
    )

    response = client.post(
        f"/raw-materials/{material['id']}/stock-in",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "quantity": 10,
        },
    )

    assert response.status_code == 400


def test_worker_cannot_create_material():
    token = create_token("Worker")

    response = client.post(
        "/raw-materials",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "material_code": unique_value("MAT"),
            "name": "Unauthorized Material",
            "category": "Test",
            "unit": "Kg",
            "supplier": "Supplier",
            "available_quantity": 10,
            "minimum_stock": 2,
            "reorder_level": 5,
        },
    )

    assert response.status_code == 403


def test_negative_initial_quantity_rejected():
    token = create_token()

    response = client.post(
        "/raw-materials",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "material_code": unique_value("MAT"),
            "name": "Invalid Material",
            "category": "Test",
            "unit": "Kg",
            "supplier": "Supplier",
            "available_quantity": -10,
            "minimum_stock": 2,
            "reorder_level": 5,
        },
    )

    assert response.status_code == 422


def test_delete_material():
    token = create_token()

    material = create_material(
        token,
        quantity=0,
    )

    response = client.delete(
        f"/raw-materials/{material['id']}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/raw-materials/{material['id']}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert get_response.status_code == 404


def test_material_with_history_cannot_be_deleted():
    token = create_token()

    material = create_material(
        token,
        quantity=100,
    )

    response = client.delete(
        f"/raw-materials/{material['id']}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 400
    assert "inventory history" in response.json()["detail"]