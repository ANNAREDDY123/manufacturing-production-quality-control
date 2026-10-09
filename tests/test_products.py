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


def create_super_admin_token() -> str:
    username, password = register_user(
        "Super Admin"
    )

    return login_user(
        username,
        password,
    )


def create_product(
    token: str,
    name: str | None = None,
    category: str = "Electronics",
) -> dict:

    response = client.post(
        "/products",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "product_code": unique_value("PROD"),
            "name": name or unique_value("Product"),
            "category": category,
            "sku": unique_value("SKU"),
            "unit": "Piece",
            "standard_production_time": 15,
        },
    )

    assert response.status_code == 201

    return response.json()


def test_create_product():
    token = create_super_admin_token()

    product = create_product(
        token,
        name="Industrial Motor",
    )

    assert product["name"] == "Industrial Motor"
    assert product["category"] == "Electronics"
    assert product["unit"] == "Piece"
    assert product["status"] == "Active"


def test_duplicate_product_code_rejected():
    token = create_super_admin_token()

    product_code = unique_value("PROD")

    payload = {
        "product_code": product_code,
        "name": "Product One",
        "category": "Mechanical",
        "sku": unique_value("SKU"),
        "unit": "Piece",
        "standard_production_time": 10,
    }

    first = client.post(
        "/products",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=payload,
    )

    assert first.status_code == 201

    payload["sku"] = unique_value("SKU")

    second = client.post(
        "/products",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json=payload,
    )

    assert second.status_code == 400
    assert second.json()["detail"] == (
        "Product code already exists"
    )


def test_duplicate_sku_rejected():
    token = create_super_admin_token()

    sku = unique_value("SKU")

    first = client.post(
        "/products",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "product_code": unique_value("PROD"),
            "name": "Product One",
            "category": "Mechanical",
            "sku": sku,
            "unit": "Piece",
            "standard_production_time": 10,
        },
    )

    assert first.status_code == 201

    second = client.post(
        "/products",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "product_code": unique_value("PROD"),
            "name": "Product Two",
            "category": "Mechanical",
            "sku": sku,
            "unit": "Piece",
            "standard_production_time": 20,
        },
    )

    assert second.status_code == 400
    assert second.json()["detail"] == (
        "SKU already exists"
    )


def test_get_product():
    token = create_super_admin_token()

    product = create_product(token)

    response = client.get(
        f"/products/{product['id']}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == product["id"]


def test_get_nonexistent_product():
    token = create_super_admin_token()

    response = client.get(
        "/products/999999",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 404


def test_update_product():
    token = create_super_admin_token()

    product = create_product(token)

    response = client.put(
        f"/products/{product['id']}",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "name": "Updated Product",
            "category": "Updated Category",
            "unit": "Box",
            "standard_production_time": 25,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated Product"
    assert data["category"] == "Updated Category"
    assert data["unit"] == "Box"
    assert data["standard_production_time"] == 25


def test_update_product_status():
    token = create_super_admin_token()

    product = create_product(token)

    response = client.patch(
        f"/products/{product['id']}/status",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "status": "Discontinued"
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Discontinued"


def test_search_products():
    token = create_super_admin_token()

    product_name = unique_value("Industrial")

    create_product(
        token,
        name=product_name,
    )

    response = client.get(
        "/products",
        params={
            "search": product_name,
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1
    assert any(
        item["name"] == product_name
        for item in data
    )


def test_filter_products_by_category():
    token = create_super_admin_token()

    category = unique_value("Automotive")

    create_product(
        token,
        category=category,
    )

    response = client.get(
        "/products",
        params={
            "category": category,
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1
    assert all(
        item["category"] == category
        for item in data
    )


def test_filter_products_by_status():
    token = create_super_admin_token()

    product = create_product(token)

    client.patch(
        f"/products/{product['id']}/status",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "status": "Inactive"
        },
    )

    response = client.get(
        "/products",
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
    assert all(
        item["status"] == "Inactive"
        for item in data
    )


def test_pagination():
    token = create_super_admin_token()

    for _ in range(3):
        create_product(token)

    response = client.get(
        "/products",
        params={
            "skip": 0,
            "limit": 2,
        },
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) <= 2


def test_worker_cannot_create_product():
    username, password = register_user(
        "Worker"
    )

    token = login_user(
        username,
        password,
    )

    response = client.post(
        "/products",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "product_code": unique_value("PROD"),
            "name": "Unauthorized Product",
            "category": "Test",
            "sku": unique_value("SKU"),
            "unit": "Piece",
            "standard_production_time": 10,
        },
    )

    assert response.status_code == 403


def test_invalid_production_time_rejected():
    token = create_super_admin_token()

    response = client.post(
        "/products",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "product_code": unique_value("PROD"),
            "name": "Invalid Product",
            "category": "Test",
            "sku": unique_value("SKU"),
            "unit": "Piece",
            "standard_production_time": 0,
        },
    )

    assert response.status_code == 422


def test_delete_product():
    token = create_super_admin_token()

    product = create_product(token)

    response = client.delete(
        f"/products/{product['id']}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/products/{product['id']}",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert get_response.status_code == 404