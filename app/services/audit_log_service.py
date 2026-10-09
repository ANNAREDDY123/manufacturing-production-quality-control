from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.schemas.audit_log import AuditLogCreate


def create_audit_log(
    db: Session,
    data: AuditLogCreate,
) -> AuditLog:
    audit_log = AuditLog(
        user_id=data.user_id,
        username=data.username,
        action=data.action,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        description=data.description,
        old_values=data.old_values,
        new_values=data.new_values,
        ip_address=data.ip_address,
        user_agent=data.user_agent,
        request_method=data.request_method,
        request_path=data.request_path,
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log


def get_audit_log(
    db: Session,
    audit_log_id: int,
) -> AuditLog:
    audit_log = db.scalar(
        select(AuditLog).where(
            AuditLog.id == audit_log_id
        )
    )

    if audit_log is None:
        raise ValueError("Audit log not found")

    return audit_log


def list_audit_logs(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    user_id: int | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
) -> list[AuditLog]:

    query = select(AuditLog)

    if user_id is not None:
        query = query.where(
            AuditLog.user_id == user_id
        )

    if action is not None:
        query = query.where(
            AuditLog.action == action
        )

    if entity_type is not None:
        query = query.where(
            AuditLog.entity_type == entity_type
        )

    if entity_id is not None:
        query = query.where(
            AuditLog.entity_id == entity_id
        )

    query = (
        query
        .order_by(AuditLog.id.desc())
        .offset(skip)
        .limit(limit)
    )

    return list(
        db.scalars(query).all()
    )


def delete_audit_log(
    db: Session,
    audit_log_id: int,
) -> AuditLog:
    audit_log = get_audit_log(
        db,
        audit_log_id,
    )

    db.delete(audit_log)
    db.commit()

    return audit_log