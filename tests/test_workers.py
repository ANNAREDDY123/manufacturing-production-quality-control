from fastapi.testclient import TestClient

from app.main import app
from app.models.production_batch_worker import ProductionBatchWorker
from app.models.worker import Worker, WorkerStatus
from app.schemas.worker import WorkerCreate

client = TestClient(app)


def test_worker_module_imports():
    assert Worker.__tablename__ == "workers"
    assert ProductionBatchWorker.__tablename__ == "production_batch_workers"


def test_worker_status_values():
    assert WorkerStatus.ACTIVE.value == "Active"
    assert WorkerStatus.ON_LEAVE.value == "On Leave"
    assert WorkerStatus.INACTIVE.value == "Inactive"


def test_worker_schema_validation():
    worker = WorkerCreate(
        employee_code="EMP1001",
        name="Test Worker",
        skill="Machine Operator",
        department="Production",
        shift="Morning",
    )

    assert worker.employee_code == "EMP1001"
    assert worker.name == "Test Worker"
    assert worker.skill == "Machine Operator"
    assert worker.department == "Production"
    assert worker.shift == "Morning"
    assert worker.status == WorkerStatus.ACTIVE


def test_worker_model_has_required_fields():
    fields = Worker.__table__.columns.keys()

    required_fields = [
        "id",
        "employee_code",
        "name",
        "skill",
        "department",
        "shift",
        "production_line_id",
        "status",
        "created_by",
        "created_at",
        "updated_at",
    ]

    for field in required_fields:
        assert field in fields


def test_batch_worker_model_has_required_fields():
    fields = ProductionBatchWorker.__table__.columns.keys()

    required_fields = [
        "id",
        "batch_id",
        "worker_id",
        "assigned_at",
    ]

    for field in required_fields:
        assert field in fields


def test_worker_status_enum_is_string_based():
    assert isinstance(WorkerStatus.ACTIVE.value, str)
    assert isinstance(WorkerStatus.ON_LEAVE.value, str)
    assert isinstance(WorkerStatus.INACTIVE.value, str)