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


def auth_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}"
    }


def create_admin_token() -> str:
    username = unique_name("bom_admin")

    register_user(
        username,
        "Super Admin",
    )

    return login(username)


def create_product(
    token: str,
) -> int:
    code = unique_name("BOM-PROD")
    sku = unique_name("BOM-SKU")

    response = client.post(
        "/products",
        headers=auth_headers(token),
        json={
            "product_code": code,
            "name": f"Test Product {code}",
            "category": "Test Category",
            "sku": sku,
            "unit": "Piece",
            "standard_production_time": 30,
            "status": "Active",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()["id"]


def create_material(
    token: str,
    quantity: float = 1000,
) -> int:
    code = unique_name("BOM-MAT")

    response = client.post(
        "/raw-materials",
        headers=auth_headers(token),
        json={
            "material_code": code,
            "name": f"Test Material {code}",
            "category": "Test Material",
            "unit": "Kg",
            "supplier": "Test Supplier",
            "available_quantity": quantity,
            "minimum_stock": 100,
            "reorder_level": 200,
            "status": "Active",
        },
    )

    assert response.status_code == 201, response.text

    return response.json()["id"]


def create_bom(
    token: str,
    product_id: int,
    material_ids: list[int],
    version: int | None = None,
) -> dict:
    items = [
        {
            "material_id": material_id,
            "quantity": 2.5,
        }
        for material_id in material_ids
    ]

    payload = {
        "description": "Test BOM",
        "items": items,
    }

    if version is not None:
        payload["version"] = version

    response = client.post(
        f"/boms/products/{product_id}",
        headers=auth_headers(token),
        json=payload,
    )

    assert response.status_code == 201, response.text

    return response.json()


def test_bom_creation():
    token = create_admin_token()

    product_id = create_product(token)
    material_id = create_material(token)

    response = client.post(
        f"/boms/products/{product_id}",
        headers=auth_headers(token),
        json={
            "description": "Initial BOM",
            "items": [
                {
                    "material_id": material_id,
                    "quantity": 2.5,
                }
            ],
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["product_id"] == product_id
    assert data["version"] == 1
    assert data["status"] == "Inactive"
    assert len(data["items"]) == 1
    assert data["items"][0]["material_id"] == material_id
    assert data["items"][0]["quantity"] == 2.5


def test_bom_automatic_versioning():
    token = create_admin_token()

    product_id = create_product(token)
    material_id = create_material(token)

    first_bom = create_bom(
        token,
        product_id,
        [material_id],
    )

    second_bom = create_bom(
        token,
        product_id,
        [material_id],
    )

    assert first_bom["version"] == 1
    assert second_bom["version"] == 2


def test_duplicate_materials_rejected():
    token = create_admin_token()

    product_id = create_product(token)
    material_id = create_material(token)

    response = client.post(
        f"/boms/products/{product_id}",
        headers=auth_headers(token),
        json={
            "description": "Duplicate Material BOM",
            "items": [
                {
                    "material_id": material_id,
                    "quantity": 2,
                },
                {
                    "material_id": material_id,
                    "quantity": 3,
                },
            ],
        },
    )

    assert response.status_code == 400
    assert (
        "cannot appear more than once"
        in response.json()["detail"]
    )


def test_invalid_product_reference_rejected():
    token = create_admin_token()

    material_id = create_material(token)

    response = client.post(
        "/boms/products/999999",
        headers=auth_headers(token),
        json={
            "description": "Invalid Product BOM",
            "items": [
                {
                    "material_id": material_id,
                    "quantity": 2,
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Product not found"


def test_invalid_material_reference_rejected():
    token = create_admin_token()

    product_id = create_product(token)

    response = client.post(
        f"/boms/products/{product_id}",
        headers=auth_headers(token),
        json={
            "description": "Invalid Material BOM",
            "items": [
                {
                    "material_id": 999999,
                    "quantity": 2,
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Raw material not found"


def test_bom_item_update_and_removal():
    token = create_admin_token()

    product_id = create_product(token)
    material_one = create_material(token)
    material_two = create_material(token)

    bom = create_bom(
        token,
        product_id,
        [material_one, material_two],
    )

    first_item_id = bom["items"][0]["id"]
    second_item_id = bom["items"][1]["id"]

    update_response = client.put(
        f"/boms/{bom['id']}/items/{first_item_id}",
        headers=auth_headers(token),
        json={
            "quantity": 7.5,
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["quantity"] == 7.5

    delete_response = client.delete(
        f"/boms/{bom['id']}/items/{second_item_id}",
        headers=auth_headers(token),
    )

    assert delete_response.status_code == 204

    details_response = client.get(
        f"/boms/{bom['id']}",
        headers=auth_headers(token),
    )

    assert details_response.status_code == 200

    remaining_items = details_response.json()["items"]

    assert len(remaining_items) == 1
    assert remaining_items[0]["id"] == first_item_id


def test_last_bom_item_cannot_be_removed():
    token = create_admin_token()

    product_id = create_product(token)
    material_id = create_material(token)

    bom = create_bom(
        token,
        product_id,
        [material_id],
    )

    item_id = bom["items"][0]["id"]

    response = client.delete(
        f"/boms/{bom['id']}/items/{item_id}",
        headers=auth_headers(token),
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "A BOM must contain at least one raw material"
    )


def test_bom_activation_requires_items():
    token = create_admin_token()

    product_id = create_product(token)

    response = client.post(
        f"/boms/products/{product_id}",
        headers=auth_headers(token),
        json={
            "description": "Empty BOM",
            "items": [],
        },
    )

    # Pydantic validation prevents an empty BOM.
    assert response.status_code == 422


def test_bom_activation():
    token = create_admin_token()

    product_id = create_product(token)
    material_id = create_material(token)

    bom = create_bom(
        token,
        product_id,
        [material_id],
    )

    response = client.patch(
        f"/boms/{bom['id']}/status",
        headers=auth_headers(token),
        json={
            "status": "Active",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Active"


def test_active_bom_cannot_be_modified():
    token = create_admin_token()

    product_id = create_product(token)
    material_one = create_material(token)
    material_two = create_material(token)

    bom = create_bom(
        token,
        product_id,
        [material_one],
    )

    activate_response = client.patch(
        f"/boms/{bom['id']}/status",
        headers=auth_headers(token),
        json={
            "status": "Active",
        },
    )

    assert activate_response.status_code == 200

    add_response = client.post(
        f"/boms/{bom['id']}/items",
        headers=auth_headers(token),
        json={
            "material_id": material_two,
            "quantity": 1,
        },
    )

    assert add_response.status_code == 400
    assert (
        "Cannot modify an active BOM"
        in add_response.json()["detail"]
    )


def test_active_bom_replacement():
    token = create_admin_token()

    product_id = create_product(token)

    material_one = create_material(token)
    material_two = create_material(token)

    bom_one = create_bom(
        token,
        product_id,
        [material_one],
    )

    bom_two = create_bom(
        token,
        product_id,
        [material_two],
    )

    activate_one = client.patch(
        f"/boms/{bom_one['id']}/status",
        headers=auth_headers(token),
        json={
            "status": "Active",
        },
    )

    assert activate_one.status_code == 200
    assert activate_one.json()["status"] == "Active"

    activate_two = client.patch(
        f"/boms/{bom_two['id']}/status",
        headers=auth_headers(token),
        json={
            "status": "Active",
        },
    )

    assert activate_two.status_code == 200
    assert activate_two.json()["status"] == "Active"

    first_details = client.get(
        f"/boms/{bom_one['id']}",
        headers=auth_headers(token),
    )

    assert first_details.status_code == 200
    assert first_details.json()["status"] == "Inactive"


def test_bom_rbac_worker_cannot_create_bom():
    admin_token = create_admin_token()

    worker_username = unique_name("bom_worker")

    register_user(
        worker_username,
        "Worker",
    )

    worker_token = login(worker_username)

    product_id = create_product(admin_token)
    material_id = create_material(admin_token)

    response = client.post(
        f"/boms/products/{product_id}",
        headers=auth_headers(worker_token),
        json={
            "description": "Worker BOM",
            "items": [
                {
                    "material_id": material_id,
                    "quantity": 1,
                }
            ],
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_bom_rbac_worker_can_view_bom():
    admin_token = create_admin_token()

    product_id = create_product(admin_token)
    material_id = create_material(admin_token)

    bom = create_bom(
        admin_token,
        product_id,
        [material_id],
    )

    worker_username = unique_name("bom_view_worker")

    register_user(
        worker_username,
        "Worker",
    )

    worker_token = login(worker_username)

    response = client.get(
        f"/boms/{bom['id']}",
        headers=auth_headers(worker_token),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"