from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.auth.dependencies import get_current_user
from app.db.database import get_db
from app.models.user import User, UserRole
from app.models.worker import WorkerStatus
from app.schemas.worker import (
    WorkerBatchAssignment,
    WorkerCreate,
    WorkerResponse,
    WorkerStatusUpdate,
    WorkerUpdate,
)

from app.services.worker_service import (
    assign_worker_to_batch,
    create_worker,
    get_worker,
    list_workers,
    remove_worker_from_batch,
    update_worker,
    update_worker_status,
)

from app.services.worker_service import (
    assign_worker_to_batch,
    create_worker,
    get_worker,
    list_workers,
    update_worker,
    update_worker_status,
)


router = APIRouter(
    prefix="/workers",
    tags=["Workers"],
)


MANAGEMENT_ROLES = {
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
}


VIEW_ROLES = {
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
    UserRole.PRODUCTION_SUPERVISOR,
    UserRole.WORKER,
}


ASSIGNMENT_ROLES = {
    UserRole.SUPER_ADMIN,
    UserRole.PLANT_MANAGER,
    UserRole.PRODUCTION_MANAGER,
    UserRole.PRODUCTION_SUPERVISOR,
}


def require_role(
    current_user: User,
    allowed_roles: set[UserRole],
) -> User:
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions",
        )

    return current_user


@router.post(
    "",
    response_model=WorkerResponse,
    status_code=201,
)
def create_worker_api(
    data: WorkerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(
        current_user,
        MANAGEMENT_ROLES,
    )

    try:
        return create_worker(
            db,
            data,
            created_by=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[WorkerResponse],
)
def list_workers_api(
    search: str | None = Query(
        default=None,
    ),
    skill: str | None = Query(
        default=None,
    ),
    department: str | None = Query(
        default=None,
    ),
    shift: str | None = Query(
        default=None,
    ),
    production_line_id: int | None = Query(
        default=None,
        gt=0,
    ),
    status: WorkerStatus | None = Query(
        default=None,
    ),
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(
        current_user,
        VIEW_ROLES,
    )

    return list_workers(
        db,
        search=search,
        skill=skill,
        department=department,
        shift=shift,
        production_line_id=production_line_id,
        status=status,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{worker_id}",
    response_model=WorkerResponse,
)
def get_worker_api(
    worker_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(
        current_user,
        VIEW_ROLES,
    )

    try:
        return get_worker(
            db,
            worker_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.put(
    "/{worker_id}",
    response_model=WorkerResponse,
)
def update_worker_api(
    worker_id: int,
    data: WorkerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(
        current_user,
        MANAGEMENT_ROLES,
    )

    try:
        return update_worker(
            db,
            worker_id,
            data,
        )
    except ValueError as exc:
        if str(exc) == "Worker not found":
            raise HTTPException(
                status_code=404,
                detail=str(exc),
            )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.patch(
    "/{worker_id}/status",
    response_model=WorkerResponse,
)
def update_worker_status_api(
    worker_id: int,
    data: WorkerStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(
        current_user,
        MANAGEMENT_ROLES,
    )

    try:
        return update_worker_status(
            db,
            worker_id,
            data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.post(
    "/{worker_id}/assign-batch",
    response_model=WorkerResponse,
)
def assign_worker_to_batch_api(
    worker_id: int,
    data: WorkerBatchAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(
        current_user,
        ASSIGNMENT_ROLES,
    )

    try:
        assign_worker_to_batch(
            db,
            worker_id,
            data.batch_id,
        )

        return get_worker(
            db,
            worker_id,
        )

    except ValueError as exc:
        message = str(exc)

        if (
            message == "Worker not found"
            or message == "Production batch not found"
        ):
            raise HTTPException(
                status_code=404,
                detail=message,
            )

        raise HTTPException(
            status_code=400,
            detail=message,
        )

@router.delete(
    "/{worker_id}/batches/{batch_id}",
)
def remove_worker_from_batch_api(
    worker_id: int,
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_role(
        current_user,
        ASSIGNMENT_ROLES,
    )

    try:
        remove_worker_from_batch(
            db,
            worker_id,
            batch_id,
        )

        return {
            "message": (
                "Worker removed from "
                "production batch"
            )
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )