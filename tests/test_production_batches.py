from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import SessionLocal
from app.models.production_batch import ProductionBatchStatus
from app.models.production_order import (
    ProductionOrderPriority,
    ProductionOrderStatus,
)
from app.models.user import User, UserRole


client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def unique_suffix() -> str:
    return datetime.now().strftime("%H%M%S%f")


def create_user(
    role: UserRole,
    username: str | None = None,
    email: str | None = None,
):
    suffix = unique_suffix()

    payload = {
        "username": username or f"batch_user_{suffix}",
        "email": email or f"batch_{suffix}@example.com",
        "full_name": f"Batch Test User {suffix[-6:]}",
        "password": "Test@12345",
        "role": role.value,
    }

    response = client.post(
        "/auth/register",
        json=payload,
    )

    if response.status_code == 201:
        return response.json()

    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.email == payload["email"])
            .first()
        )

        if user:
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role.value,
            }

    finally:
        db.close()

    pytest.fail(
        f"Could not create user. "
        f"Status={response.status_code}, Body={response.text}"
    )


def login_user(
    username: str,
    password: str = "Test@12345",
) -> str:
    response = client.post(
        "/auth/login",
        json={
            "username": username,
            "password": password,
        },
    )

    if response.status_code != 200:
        pytest.fail(
            f"Login failed. "
            f"Status={response.status_code}, Body={response.text}"
        )

    data = response.json()

    token = data.get("access_token")

    if not token:
        pytest.fail(
            f"Login response does not contain access_token: {data}"
        )

    return token


def auth_headers(token: str):
    return {
        "Authorization": f"Bearer {token}",
    }


def create_plant(token: str):
    suffix = unique_suffix()

    payload = {
        "plant_code": f"PBPL{suffix[-8:]}",
        "name": f"Production Batch Plant {suffix[-6:]}",
        "description": "Production batch test plant",
        "address": "Industrial Area",
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India",
        "capacity": 10000,
        "manager_id": None,
        "status": "Active",
    }

    response = client.post(
        "/plants",
        json=payload,
        headers=auth_headers(token),
    )

    if response.status_code not in (200, 201):
        pytest.fail(
            f"Plant creation failed. "
            f"Status={response.status_code}, Body={response.text}"
        )

    return response.json()


def create_product(token: str):
    suffix = unique_suffix()

    payload = {
        "product_code": f"PBP{suffix[-8:]}",
        "name": f"Batch Product {suffix[-6:]}",
        "description": "Production batch test product",
        "category": "Finished Goods",
        "sku": f"SKU_{suffix[-10:]}",
        "unit": "Piece",
        "standard_production_time": 2.5,
        "status": "Active",
    }

    response = client.post(
        "/products",
        json=payload,
        headers=auth_headers(token),
    )

    if response.status_code not in (200, 201):
        pytest.fail(
            f"Product creation failed. "
            f"Status={response.status_code}, Body={response.text}"
        )

    return response.json()


def create_production_line(
    token: str,
    plant_id: int,
):
    suffix = unique_suffix()

    payload = {
        "line_code": f"PBL{suffix[-8:]}",
        "name": f"Batch Production Line {suffix[-6:]}",
        "capacity": 1000,
        "plant_id": plant_id,
        "supervisor_id": None,
        "status": "Active",
    }

    response = client.post(
        "/production-lines",
        json=payload,
        headers=auth_headers(token),
    )

    if response.status_code not in (200, 201):
        pytest.fail(
            f"Production line creation failed. "
            f"Status={response.status_code}, Body={response.text}"
        )

    return response.json()


def create_production_order(
    token: str,
    product_id: int,
    production_line_id: int,
    supervisor_id: int | None = None,
    quantity: float = 100,
):
    suffix = unique_suffix()

    payload = {
        "order_number": f"PBO{suffix[-8:]}",
        "product_id": product_id,
        "quantity": quantity,
        "target_date": (
    datetime.now() + timedelta(days=7)
).date().isoformat(),
        "production_line_id": production_line_id,
        "priority": ProductionOrderPriority.MEDIUM.value,
    }

    if supervisor_id is not None:
        payload["supervisor_id"] = supervisor_id

    response = client.post(
        "/production-orders",
        json=payload,
        headers=auth_headers(token),
    )

    if response.status_code not in (200, 201):
        pytest.fail(
            f"Production order creation failed. "
            f"Status={response.status_code}, Body={response.text}"
        )

    return response.json()


def create_batch(
    token: str,
    production_order_id: int,
    quantity: float = 20,
    supervisor_id: int | None = None,
):
    suffix = unique_suffix()

    payload = {
        "batch_number": f"BATCH{suffix[-8:]}",
        "production_order_id": production_order_id,
        "quantity": quantity,
    }

    if supervisor_id is not None:
        payload["supervisor_id"] = supervisor_id

    response = client.post(
        "/production-batches",
        json=payload,
        headers=auth_headers(token),
    )

    return response


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def management_user():
    return create_user(UserRole.PLANT_MANAGER)


@pytest.fixture
def supervisor_user():
    return create_user(UserRole.PRODUCTION_SUPERVISOR)


@pytest.fixture
def worker_user():
    return create_user(UserRole.WORKER)


@pytest.fixture
def batch_setup(
    management_user,
    supervisor_user,
):
    management_token = login_user(
        management_user["username"]
    )

    supervisor_token = login_user(
        supervisor_user["username"]
    )

    plant = create_plant(management_token)

    product = create_product(management_token)

    line = create_production_line(
        management_token,
        plant["id"],
    )

    order = create_production_order(
        management_token,
        product["id"],
        line["id"],
        supervisor_id=supervisor_user["id"],
        quantity=100,
    )

    return {
        "management_user": management_user,
        "management_token": management_token,
        "supervisor_user": supervisor_user,
        "supervisor_token": supervisor_token,
        "plant": plant,
        "product": product,
        "line": line,
        "order": order,
    }


# ---------------------------------------------------------------------------
# 1. Create Production Batch
# ---------------------------------------------------------------------------

def test_create_production_batch(batch_setup):
    response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=20,
        supervisor_id=batch_setup["supervisor_user"]["id"],
    )

    assert response.status_code == 201

    data = response.json()

    assert data["batch_number"]
    assert data["production_order_id"] == batch_setup["order"]["id"]
    assert data["quantity"] == 20
    assert data["supervisor_id"] == batch_setup["supervisor_user"]["id"]
    assert data["status"] == ProductionBatchStatus.PLANNED.value
    assert data["actual_start"] is None
    assert data["actual_end"] is None


# ---------------------------------------------------------------------------
# 2. Get Production Batch
# ---------------------------------------------------------------------------

def test_get_production_batch(batch_setup):
    create_response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=20,
    )

    assert create_response.status_code == 201

    batch_id = create_response.json()["id"]

    response = client.get(
        f"/production-batches/{batch_id}",
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == batch_id
    assert data["production_order_id"] == batch_setup["order"]["id"]
    assert data["quantity"] == 20


# ---------------------------------------------------------------------------
# 3. Get Non-existing Batch
# ---------------------------------------------------------------------------

def test_get_non_existing_production_batch(batch_setup):
    response = client.get(
        "/production-batches/999999999",
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert response.status_code == 404
    assert "Production batch not found" in response.text


# ---------------------------------------------------------------------------
# 4. List Production Batches
# ---------------------------------------------------------------------------

def test_list_production_batches(batch_setup):
    create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=10,
    )

    create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=20,
    )

    response = client.get(
        "/production-batches",
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 2


# ---------------------------------------------------------------------------
# 5. Search Production Batches
# ---------------------------------------------------------------------------

def test_search_production_batches(batch_setup):
    create_response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=10,
    )

    assert create_response.status_code == 201

    batch_number = create_response.json()["batch_number"]

    response = client.get(
        "/production-batches",
        params={"search": batch_number},
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1
    assert any(
        item["batch_number"] == batch_number
        for item in data
    )


# ---------------------------------------------------------------------------
# 6. Filter by Production Order
# ---------------------------------------------------------------------------

def test_filter_batches_by_production_order(batch_setup):
    create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=10,
    )

    response = client.get(
        "/production-batches",
        params={
            "production_order_id":
                batch_setup["order"]["id"],
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1

    for batch in data:
        assert (
            batch["production_order_id"]
            == batch_setup["order"]["id"]
        )


# ---------------------------------------------------------------------------
# 7. Filter by Status
# ---------------------------------------------------------------------------

def test_filter_batches_by_status(batch_setup):
    create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=10,
    )

    response = client.get(
        "/production-batches",
        params={"status": "Planned"},
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1

    for batch in data:
        assert (
            batch["status"]
            == ProductionBatchStatus.PLANNED.value
        )


# ---------------------------------------------------------------------------
# 8. Filter by Supervisor
# ---------------------------------------------------------------------------

def test_filter_batches_by_supervisor(batch_setup):
    create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=10,
        supervisor_id=batch_setup["supervisor_user"]["id"],
    )

    response = client.get(
        "/production-batches",
        params={
            "supervisor_id":
                batch_setup["supervisor_user"]["id"],
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) >= 1

    for batch in data:
        assert (
            batch["supervisor_id"]
            == batch_setup["supervisor_user"]["id"]
        )


# ---------------------------------------------------------------------------
# 9. Duplicate Batch Number
# ---------------------------------------------------------------------------

def test_duplicate_batch_number(batch_setup):
    suffix = unique_suffix()

    batch_number = f"DUPBATCH{suffix[-8:]}"

    payload = {
        "batch_number": batch_number,
        "production_order_id":
            batch_setup["order"]["id"],
        "quantity": 10,
    }

    first_response = client.post(
        "/production-batches",
        json=payload,
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/production-batches",
        json=payload,
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert second_response.status_code == 400
    assert "already exists" in second_response.text.lower()


# ---------------------------------------------------------------------------
# 10. Quantity Cannot Exceed Production Order Quantity
# ---------------------------------------------------------------------------

def test_batch_quantity_cannot_exceed_order_quantity(
    batch_setup,
):
    response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=101,
    )

    assert response.status_code == 400
    assert (
        "remaining production order quantity"
        in response.text.lower()
    )


# ---------------------------------------------------------------------------
# 11. Multiple Batches Cannot Exceed Order Quantity
# ---------------------------------------------------------------------------

def test_multiple_batches_cannot_exceed_order_quantity(
    batch_setup,
):
    first_response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=60,
    )

    assert first_response.status_code == 201

    second_response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=50,
    )

    assert second_response.status_code == 400
    assert (
        "remaining production order quantity"
        in second_response.text.lower()
    )


# ---------------------------------------------------------------------------
# 12. Valid Remaining Quantity
# ---------------------------------------------------------------------------

def test_batch_can_use_remaining_order_quantity(
    batch_setup,
):
    first_response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=60,
    )

    assert first_response.status_code == 201

    second_response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=40,
    )

    assert second_response.status_code == 201
    assert second_response.json()["quantity"] == 40


# ---------------------------------------------------------------------------
# 13. Invalid Supervisor
# ---------------------------------------------------------------------------

def test_batch_invalid_supervisor(batch_setup):
    response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=10,
        supervisor_id=999999999,
    )

    assert response.status_code == 400
    assert "supervisor not found" in response.text.lower()


# ---------------------------------------------------------------------------
# 14. Worker Cannot Be Assigned as Supervisor
# ---------------------------------------------------------------------------

def test_worker_cannot_be_batch_supervisor(
    batch_setup,
    worker_user,
):
    response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=10,
        supervisor_id=worker_user["id"],
    )

    assert response.status_code == 400
    assert "production supervisor role" in response.text.lower()


# ---------------------------------------------------------------------------
# 15. Update Planned Batch
# ---------------------------------------------------------------------------

def test_update_planned_batch(batch_setup):
    create_response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=20,
    )

    assert create_response.status_code == 201

    batch_id = create_response.json()["id"]

    new_start = (
        datetime.now() + timedelta(hours=2)
    ).isoformat()

    response = client.put(
        f"/production-batches/{batch_id}",
        json={
            "quantity": 30,
            "planned_start": new_start,
            "supervisor_id":
                batch_setup["supervisor_user"]["id"],
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["quantity"] == 30
    assert (
        data["supervisor_id"]
        == batch_setup["supervisor_user"]["id"]
    )
    assert data["planned_start"] is not None


# ---------------------------------------------------------------------------
# 16. Update Batch Quantity Cannot Exceed Remaining Order Quantity
# ---------------------------------------------------------------------------

def test_update_batch_quantity_cannot_exceed_order(
    batch_setup,
):
    first_response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=60,
    )

    assert first_response.status_code == 201

    batch_id = first_response.json()["id"]

    response = client.put(
        f"/production-batches/{batch_id}",
        json={
            "quantity": 101,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert response.status_code == 400
    assert (
        "remaining production order quantity"
        in response.text.lower()
    )


# ---------------------------------------------------------------------------
# 17. Planned -> In Progress
# ---------------------------------------------------------------------------

def test_batch_status_planned_to_in_progress(batch_setup):
    create_response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=20,
    )

    assert create_response.status_code == 201

    batch_id = create_response.json()["id"]

    response = client.patch(
        f"/production-batches/{batch_id}/status",
        json={
            "status":
                ProductionBatchStatus.IN_PROGRESS.value,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert (
        data["status"]
        == ProductionBatchStatus.IN_PROGRESS.value
    )
    assert data["actual_start"] is not None
    assert data["actual_end"] is None


# ---------------------------------------------------------------------------
# 18. In Progress -> Paused
# ---------------------------------------------------------------------------

def test_batch_status_in_progress_to_paused(batch_setup):
    create_response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=20,
    )

    assert create_response.status_code == 201

    batch_id = create_response.json()["id"]

    start_response = client.patch(
        f"/production-batches/{batch_id}/status",
        json={
            "status":
                ProductionBatchStatus.IN_PROGRESS.value,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert start_response.status_code == 200

    pause_response = client.patch(
        f"/production-batches/{batch_id}/status",
        json={
            "status":
                ProductionBatchStatus.PAUSED.value,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert pause_response.status_code == 200

    data = pause_response.json()

    assert (
        data["status"]
        == ProductionBatchStatus.PAUSED.value
    )
    assert data["actual_start"] is not None


# ---------------------------------------------------------------------------
# 19. Paused -> In Progress
# ---------------------------------------------------------------------------

def test_batch_status_paused_to_in_progress(batch_setup):
    create_response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=20,
    )

    assert create_response.status_code == 201

    batch_id = create_response.json()["id"]

    client.patch(
        f"/production-batches/{batch_id}/status",
        json={
            "status":
                ProductionBatchStatus.IN_PROGRESS.value,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    client.patch(
        f"/production-batches/{batch_id}/status",
        json={
            "status":
                ProductionBatchStatus.PAUSED.value,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    response = client.patch(
        f"/production-batches/{batch_id}/status",
        json={
            "status":
                ProductionBatchStatus.IN_PROGRESS.value,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert response.status_code == 200
    assert (
        response.json()["status"]
        == ProductionBatchStatus.IN_PROGRESS.value
    )


# ---------------------------------------------------------------------------
# 20. In Progress -> Completed
# ---------------------------------------------------------------------------

def test_batch_status_in_progress_to_completed(
    batch_setup,
):
    create_response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=20,
    )

    assert create_response.status_code == 201

    batch_id = create_response.json()["id"]

    start_response = client.patch(
        f"/production-batches/{batch_id}/status",
        json={
            "status":
                ProductionBatchStatus.IN_PROGRESS.value,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert start_response.status_code == 200

    complete_response = client.patch(
        f"/production-batches/{batch_id}/status",
        json={
            "status":
                ProductionBatchStatus.COMPLETED.value,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert complete_response.status_code == 200

    data = complete_response.json()

    assert (
        data["status"]
        == ProductionBatchStatus.COMPLETED.value
    )
    assert data["actual_start"] is not None
    assert data["actual_end"] is not None


# ---------------------------------------------------------------------------
# 21. Invalid Status Transition
# ---------------------------------------------------------------------------

def test_invalid_batch_status_transition(batch_setup):
    create_response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=20,
    )

    assert create_response.status_code == 201

    batch_id = create_response.json()["id"]

    response = client.patch(
        f"/production-batches/{batch_id}/status",
        json={
            "status":
                ProductionBatchStatus.COMPLETED.value,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert response.status_code == 400
    assert "cannot transition" in response.text.lower()


# ---------------------------------------------------------------------------
# 22. Completed Batch Is Terminal
# ---------------------------------------------------------------------------

def test_completed_batch_is_terminal(batch_setup):
    create_response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=20,
    )

    assert create_response.status_code == 201

    batch_id = create_response.json()["id"]

    client.patch(
        f"/production-batches/{batch_id}/status",
        json={
            "status":
                ProductionBatchStatus.IN_PROGRESS.value,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    complete_response = client.patch(
        f"/production-batches/{batch_id}/status",
        json={
            "status":
                ProductionBatchStatus.COMPLETED.value,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert complete_response.status_code == 200

    response = client.patch(
        f"/production-batches/{batch_id}/status",
        json={
            "status":
                ProductionBatchStatus.PAUSED.value,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert response.status_code == 400


# ---------------------------------------------------------------------------
# 23. Planned -> Cancelled
# ---------------------------------------------------------------------------

def test_batch_status_planned_to_cancelled(batch_setup):
    create_response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=20,
    )

    assert create_response.status_code == 201

    batch_id = create_response.json()["id"]

    response = client.patch(
        f"/production-batches/{batch_id}/status",
        json={
            "status":
                ProductionBatchStatus.CANCELLED.value,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert response.status_code == 200
    assert (
        response.json()["status"]
        == ProductionBatchStatus.CANCELLED.value
    )


# ---------------------------------------------------------------------------
# 24. Cancelled Batch Is Terminal
# ---------------------------------------------------------------------------

def test_cancelled_batch_is_terminal(batch_setup):
    create_response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=20,
    )

    assert create_response.status_code == 201

    batch_id = create_response.json()["id"]

    cancel_response = client.patch(
        f"/production-batches/{batch_id}/status",
        json={
            "status":
                ProductionBatchStatus.CANCELLED.value,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert cancel_response.status_code == 200

    response = client.patch(
        f"/production-batches/{batch_id}/status",
        json={
            "status":
                ProductionBatchStatus.IN_PROGRESS.value,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert response.status_code == 400


# ---------------------------------------------------------------------------
# 25. Cancelled Batch Does Not Consume Order Quantity
# ---------------------------------------------------------------------------

def test_cancelled_batch_does_not_consume_order_quantity(
    batch_setup,
):
    first_response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=100,
    )

    assert first_response.status_code == 201

    first_batch_id = first_response.json()["id"]

    cancel_response = client.patch(
        f"/production-batches/{first_batch_id}/status",
        json={
            "status":
                ProductionBatchStatus.CANCELLED.value,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert cancel_response.status_code == 200

    second_response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=100,
    )

    assert second_response.status_code == 201


# ---------------------------------------------------------------------------
# 26. Cannot Create Batch for Completed Order
# ---------------------------------------------------------------------------

def test_cannot_create_batch_for_completed_order(
    batch_setup,
):
    order_id = batch_setup["order"]["id"]

    scheduled_response = client.patch(
        f"/production-orders/{order_id}/status",
        json={
            "status":
                ProductionOrderStatus.SCHEDULED.value,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert scheduled_response.status_code == 200

    in_progress_response = client.patch(
        f"/production-orders/{order_id}/status",
        json={
            "status":
                ProductionOrderStatus.IN_PROGRESS.value,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert in_progress_response.status_code == 200

    completed_response = client.patch(
        f"/production-orders/{order_id}/status",
        json={
            "status":
                ProductionOrderStatus.COMPLETED.value,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert completed_response.status_code == 200

    response = create_batch(
        batch_setup["management_token"],
        order_id,
        quantity=10,
    )

    assert response.status_code == 400
    assert "completed or cancelled" in response.text.lower()


# ---------------------------------------------------------------------------
# 27. Cannot Create Batch for Cancelled Order
# ---------------------------------------------------------------------------

def test_cannot_create_batch_for_cancelled_order(
    batch_setup,
):
    order_id = batch_setup["order"]["id"]

    response = client.patch(
        f"/production-orders/{order_id}/status",
        json={
            "status":
                ProductionOrderStatus.CANCELLED.value,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert response.status_code == 200

    batch_response = create_batch(
        batch_setup["management_token"],
        order_id,
        quantity=10,
    )

    assert batch_response.status_code == 400
    assert (
        "completed or cancelled"
        in batch_response.text.lower()
    )


# ---------------------------------------------------------------------------
# 28. Pagination
# ---------------------------------------------------------------------------

def test_production_batch_pagination(batch_setup):
    for _ in range(3):
        response = create_batch(
            batch_setup["management_token"],
            batch_setup["order"]["id"],
            quantity=10,
        )

        assert response.status_code == 201

    response = client.get(
        "/production-batches",
        params={
            "skip": 0,
            "limit": 2,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) <= 2


# ---------------------------------------------------------------------------
# 29. Production Supervisor Can View Batches
# ---------------------------------------------------------------------------

def test_production_supervisor_can_view_batches(
    batch_setup,
):
    create_response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=20,
        supervisor_id=batch_setup["supervisor_user"]["id"],
    )

    assert create_response.status_code == 201

    response = client.get(
        "/production-batches",
        headers=auth_headers(
            batch_setup["supervisor_token"]
        ),
    )

    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 30. Production Supervisor Can Change Batch Status
# ---------------------------------------------------------------------------

def test_production_supervisor_can_change_batch_status(
    batch_setup,
):
    create_response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=20,
        supervisor_id=batch_setup["supervisor_user"]["id"],
    )

    assert create_response.status_code == 201

    batch_id = create_response.json()["id"]

    response = client.patch(
        f"/production-batches/{batch_id}/status",
        json={
            "status":
                ProductionBatchStatus.IN_PROGRESS.value,
        },
        headers=auth_headers(
            batch_setup["supervisor_token"]
        ),
    )

    assert response.status_code == 200
    assert (
        response.json()["status"]
        == ProductionBatchStatus.IN_PROGRESS.value
    )


# ---------------------------------------------------------------------------
# 31. Worker Cannot View Production Batches
# ---------------------------------------------------------------------------

def test_worker_cannot_view_production_batches(
    batch_setup,
    worker_user,
):
    worker_token = login_user(
        worker_user["username"]
    )

    response = client.get(
        "/production-batches",
        headers=auth_headers(worker_token),
    )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# 32. Worker Cannot Create Production Batch
# ---------------------------------------------------------------------------

def test_worker_cannot_create_production_batch(
    batch_setup,
    worker_user,
):
    worker_token = login_user(
        worker_user["username"]
    )

    response = create_batch(
        worker_token,
        batch_setup["order"]["id"],
        quantity=10,
    )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# 33. Production Supervisor Cannot Create Production Batch
# ---------------------------------------------------------------------------

def test_production_supervisor_cannot_create_batch(
    batch_setup,
):
    response = create_batch(
        batch_setup["supervisor_token"],
        batch_setup["order"]["id"],
        quantity=10,
    )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# 34. Batch Response Contains Audit Fields
# ---------------------------------------------------------------------------

def test_batch_response_contains_audit_fields(
    batch_setup,
):
    response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=20,
    )

    assert response.status_code == 201

    data = response.json()

    assert "created_at" in data
    assert "updated_at" in data
    assert data["created_at"] is not None
    assert data["updated_at"] is not None


# ---------------------------------------------------------------------------
# 35. Batch Created By Current User
# ---------------------------------------------------------------------------

def test_batch_created_by_current_user(batch_setup):
    response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=20,
    )

    assert response.status_code == 201

    data = response.json()

    assert (
        data["created_by"]
        == batch_setup["management_user"]["id"]
    )


# ---------------------------------------------------------------------------
# 36. Invalid Quantity Rejected
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "quantity",
    [0, -1, -10],
)
def test_invalid_batch_quantity_rejected(
    batch_setup,
    quantity,
):
    response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=quantity,
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 37. Invalid Production Order Rejected
# ---------------------------------------------------------------------------

def test_invalid_production_order_rejected(batch_setup):
    response = create_batch(
        batch_setup["management_token"],
        999999999,
        quantity=10,
    )

    assert response.status_code == 400
    assert "production order" in response.text.lower()


# ---------------------------------------------------------------------------
# 38. Update Batch Not Found
# ---------------------------------------------------------------------------

def test_update_non_existing_batch(batch_setup):
    response = client.put(
        "/production-batches/999999999",
        json={
            "quantity": 20,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# 39. Update Cancelled Batch Rejected
# ---------------------------------------------------------------------------

def test_update_cancelled_batch_rejected(batch_setup):
    create_response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=20,
    )

    assert create_response.status_code == 201

    batch_id = create_response.json()["id"]

    cancel_response = client.patch(
        f"/production-batches/{batch_id}/status",
        json={
            "status":
                ProductionBatchStatus.CANCELLED.value,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert cancel_response.status_code == 200

    update_response = client.put(
        f"/production-batches/{batch_id}",
        json={
            "quantity": 30,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert update_response.status_code == 400


# ---------------------------------------------------------------------------
# 40. Update Completed Batch Rejected
# ---------------------------------------------------------------------------

def test_update_completed_batch_rejected(batch_setup):
    create_response = create_batch(
        batch_setup["management_token"],
        batch_setup["order"]["id"],
        quantity=20,
    )

    assert create_response.status_code == 201

    batch_id = create_response.json()["id"]

    start_response = client.patch(
        f"/production-batches/{batch_id}/status",
        json={
            "status":
                ProductionBatchStatus.IN_PROGRESS.value,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert start_response.status_code == 200

    complete_response = client.patch(
        f"/production-batches/{batch_id}/status",
        json={
            "status":
                ProductionBatchStatus.COMPLETED.value,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert complete_response.status_code == 200

    update_response = client.put(
        f"/production-batches/{batch_id}",
        json={
            "quantity": 30,
        },
        headers=auth_headers(
            batch_setup["management_token"]
        ),
    )

    assert update_response.status_code == 400