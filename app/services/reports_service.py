from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.defect import (
    Defect,
    DefectSeverity,
    DefectStatus,
)
from app.models.downtime import (
    DowntimeStatus,
    MachineDowntime,
)
from app.models.inventory_movement import (
    InventoryMovement,
    InventoryMovementType,
)
from app.models.machine import Machine
from app.models.machine_maintenance import (
    MachineMaintenance,
    MaintenanceStatus,
)
from app.models.plant import Plant
from app.models.production_approval import (
    ProductionApproval,
    ProductionApprovalStatus,
)
from app.models.production_batch import (
    ProductionBatch,
    ProductionBatchStatus,
)
from app.models.production_line import ProductionLine
from app.models.production_order import (
    ProductionOrder,
    ProductionOrderStatus,
)
from app.models.product import Product
from app.models.quality_inspection import (
    QualityInspection,
    QualityInspectionStatus,
)
from app.models.raw_material import RawMaterial
from app.models.worker import Worker

from app.schemas.reports import (
    DowntimeReport,
    InventoryReport,
    MaintenanceReport,
    ProductionApprovalReport,
    ProductionReport,
    QualityReport,
    ReportsOverview,
)


def _count(
    db: Session,
    model,
    condition=None,
) -> int:
    query = select(func.count()).select_from(model)

    if condition is not None:
        query = query.where(condition)

    return int(db.scalar(query) or 0)


def _sum(
    db: Session,
    model,
    column,
) -> float:
    value = db.scalar(
        select(
            func.coalesce(
                func.sum(column),
                0,
            )
        ).select_from(model)
    )

    return float(value or 0)


def get_reports_overview(
    db: Session,
) -> ReportsOverview:

    total_orders = _count(
        db,
        ProductionOrder,
    )

    completed_orders = _count(
        db,
        ProductionOrder,
        ProductionOrder.status
        == ProductionOrderStatus.COMPLETED,
    )

    active_orders = _count(
        db,
        ProductionOrder,
        ProductionOrder.status.in_(
            [
                ProductionOrderStatus.SCHEDULED,
                ProductionOrderStatus.IN_PROGRESS,
                ProductionOrderStatus.PAUSED,
            ]
        ),
    )

    cancelled_orders = _count(
        db,
        ProductionOrder,
        ProductionOrder.status
        == ProductionOrderStatus.CANCELLED,
    )

    total_batches = _count(
        db,
        ProductionBatch,
    )

    completed_batches = _count(
        db,
        ProductionBatch,
        ProductionBatch.status
        == ProductionBatchStatus.COMPLETED,
    )

    active_batches = _count(
        db,
        ProductionBatch,
        ProductionBatch.status.in_(
            [
                ProductionBatchStatus.IN_PROGRESS,
                ProductionBatchStatus.PAUSED,
            ]
        ),
    )

    cancelled_batches = _count(
        db,
        ProductionBatch,
        ProductionBatch.status
        == ProductionBatchStatus.CANCELLED,
    )

    total_inspections = _count(
        db,
        QualityInspection,
    )

    passed_inspections = _count(
        db,
        QualityInspection,
        QualityInspection.status
        == QualityInspectionStatus.PASSED,
    )

    failed_inspections = _count(
        db,
        QualityInspection,
        QualityInspection.status
        == QualityInspectionStatus.FAILED,
    )

    pending_inspections = _count(
        db,
        QualityInspection,
        QualityInspection.status
        == QualityInspectionStatus.PENDING,
    )

    total_defects = _count(
        db,
        Defect,
    )

    open_defects = _count(
        db,
        Defect,
        Defect.status == DefectStatus.OPEN,
    )

    resolved_defects = _count(
        db,
        Defect,
        Defect.status == DefectStatus.RESOLVED,
    )

    critical_defects = _count(
        db,
        Defect,
        Defect.severity == DefectSeverity.CRITICAL,
    )

    return ReportsOverview(
        total_plants=_count(db, Plant),
        total_production_lines=_count(
            db,
            ProductionLine,
        ),
        total_products=_count(
            db,
            Product,
        ),
        total_raw_materials=_count(
            db,
            RawMaterial,
        ),
        low_stock_materials=_count(
            db,
            RawMaterial,
            RawMaterial.available_quantity
            <= RawMaterial.reorder_level,
        ),
        total_machines=_count(
            db,
            Machine,
        ),
        total_workers=_count(
            db,
            Worker,
        ),

        total_production_orders=total_orders,
        completed_production_orders=completed_orders,
        active_production_orders=active_orders,
        cancelled_production_orders=cancelled_orders,

        total_production_batches=total_batches,
        completed_production_batches=completed_batches,
        active_production_batches=active_batches,
        cancelled_production_batches=cancelled_batches,

        total_quality_inspections=total_inspections,
        passed_quality_inspections=passed_inspections,
        failed_quality_inspections=failed_inspections,
        pending_quality_inspections=pending_inspections,

        total_defects=total_defects,
        open_defects=open_defects,
        resolved_defects=resolved_defects,
        critical_defects=critical_defects,

        total_maintenance_records=_count(
            db,
            MachineMaintenance,
        ),
        completed_maintenance_records=_count(
            db,
            MachineMaintenance,
            MachineMaintenance.status
            == MaintenanceStatus.COMPLETED,
        ),

        total_downtime_records=_count(
            db,
            MachineDowntime,
        ),

        total_inventory_movements=_count(
            db,
            InventoryMovement,
        ),

        total_production_approvals=_count(
            db,
            ProductionApproval,
        ),
        pending_production_approvals=_count(
            db,
            ProductionApproval,
            ProductionApproval.status
            == ProductionApprovalStatus.PENDING,
        ),
    )


def get_production_report(
    db: Session,
) -> ProductionReport:

    total_orders = _count(
        db,
        ProductionOrder,
    )

    draft_orders = _count(
        db,
        ProductionOrder,
        ProductionOrder.status
        == ProductionOrderStatus.DRAFT,
    )

    scheduled_orders = _count(
        db,
        ProductionOrder,
        ProductionOrder.status
        == ProductionOrderStatus.SCHEDULED,
    )

    active_orders = _count(
        db,
        ProductionOrder,
        ProductionOrder.status.in_(
            [
                ProductionOrderStatus.SCHEDULED,
                ProductionOrderStatus.IN_PROGRESS,
                ProductionOrderStatus.PAUSED,
            ]
        ),
    )

    completed_orders = _count(
        db,
        ProductionOrder,
        ProductionOrder.status
        == ProductionOrderStatus.COMPLETED,
    )

    cancelled_orders = _count(
        db,
        ProductionOrder,
        ProductionOrder.status
        == ProductionOrderStatus.CANCELLED,
    )

    total_order_quantity = _sum(
        db,
        ProductionOrder,
        ProductionOrder.quantity,
    )

    total_batches = _count(
        db,
        ProductionBatch,
    )

    planned_batches = _count(
        db,
        ProductionBatch,
        ProductionBatch.status
        == ProductionBatchStatus.PLANNED,
    )

    active_batches = _count(
        db,
        ProductionBatch,
        ProductionBatch.status.in_(
            [
                ProductionBatchStatus.IN_PROGRESS,
                ProductionBatchStatus.PAUSED,
            ]
        ),
    )

    completed_batches = _count(
        db,
        ProductionBatch,
        ProductionBatch.status
        == ProductionBatchStatus.COMPLETED,
    )

    cancelled_batches = _count(
        db,
        ProductionBatch,
        ProductionBatch.status
        == ProductionBatchStatus.CANCELLED,
    )

    total_batch_quantity = _sum(
        db,
        ProductionBatch,
        ProductionBatch.quantity,
    )

    order_completion_percentage = 0.0

    if total_orders:
        order_completion_percentage = round(
            completed_orders
            / total_orders
            * 100,
            2,
        )

    batch_completion_percentage = 0.0

    if total_batches:
        batch_completion_percentage = round(
            completed_batches
            / total_batches
            * 100,
            2,
        )

    return ProductionReport(
        total_orders=total_orders,
        draft_orders=draft_orders,
        scheduled_orders=scheduled_orders,
        active_orders=active_orders,
        completed_orders=completed_orders,
        cancelled_orders=cancelled_orders,
        total_order_quantity=total_order_quantity,

        total_batches=total_batches,
        planned_batches=planned_batches,
        active_batches=active_batches,
        completed_batches=completed_batches,
        cancelled_batches=cancelled_batches,
        total_batch_quantity=total_batch_quantity,

        order_completion_percentage=order_completion_percentage,
        batch_completion_percentage=batch_completion_percentage,
    )


def get_quality_report(
    db: Session,
) -> QualityReport:

    total_inspections = _count(
        db,
        QualityInspection,
    )

    pending_inspections = _count(
        db,
        QualityInspection,
        QualityInspection.status
        == QualityInspectionStatus.PENDING,
    )

    passed_inspections = _count(
        db,
        QualityInspection,
        QualityInspection.status
        == QualityInspectionStatus.PASSED,
    )

    failed_inspections = _count(
        db,
        QualityInspection,
        QualityInspection.status
        == QualityInspectionStatus.FAILED,
    )

    cancelled_inspections = _count(
        db,
        QualityInspection,
        QualityInspection.status
        == QualityInspectionStatus.CANCELLED,
    )

    inspection_pass_percentage = 0.0

    if total_inspections:
        inspection_pass_percentage = round(
            passed_inspections
            / total_inspections
            * 100,
            2,
        )

    total_defects = _count(
        db,
        Defect,
    )

    open_defects = _count(
        db,
        Defect,
        Defect.status == DefectStatus.OPEN,
    )

    under_review_defects = _count(
        db,
        Defect,
        Defect.status == DefectStatus.UNDER_REVIEW,
    )

    corrective_action_defects = _count(
        db,
        Defect,
        Defect.status
        == DefectStatus.CORRECTIVE_ACTION,
    )

    resolved_defects = _count(
        db,
        Defect,
        Defect.status == DefectStatus.RESOLVED,
    )

    closed_defects = _count(
        db,
        Defect,
        Defect.status == DefectStatus.CLOSED,
    )

    critical_defects = _count(
        db,
        Defect,
        Defect.severity == DefectSeverity.CRITICAL,
    )

    resolved_defect_count = (
        resolved_defects
        + closed_defects
    )

    defect_resolution_percentage = 0.0

    if total_defects:
        defect_resolution_percentage = round(
            resolved_defect_count
            / total_defects
            * 100,
            2,
        )

    return QualityReport(
        total_inspections=total_inspections,
        pending_inspections=pending_inspections,
        passed_inspections=passed_inspections,
        failed_inspections=failed_inspections,
        cancelled_inspections=cancelled_inspections,

        inspection_pass_percentage=(
            inspection_pass_percentage
        ),

        total_defects=total_defects,
        open_defects=open_defects,
        under_review_defects=under_review_defects,
        corrective_action_defects=(
            corrective_action_defects
        ),
        resolved_defects=resolved_defects,
        closed_defects=closed_defects,
        critical_defects=critical_defects,

        defect_resolution_percentage=(
            defect_resolution_percentage
        ),
    )


def get_inventory_report(
    db: Session,
) -> InventoryReport:

    total_materials = _count(
        db,
        RawMaterial,
    )

    active_materials = _count(
        db,
        RawMaterial,
        RawMaterial.status == "Active",
    )

    inactive_materials = _count(
        db,
        RawMaterial,
        RawMaterial.status == "Inactive",
    )

    low_stock_materials = _count(
        db,
        RawMaterial,
        RawMaterial.available_quantity
        <= RawMaterial.reorder_level,
    )

    total_inventory_movements = _count(
        db,
        InventoryMovement,
    )

    stock_in_movements = _count(
        db,
        InventoryMovement,
        InventoryMovement.movement_type
        == InventoryMovementType.STOCK_IN,
    )

    stock_out_movements = _count(
        db,
        InventoryMovement,
        InventoryMovement.movement_type
        == InventoryMovementType.STOCK_OUT,
    )

    adjustment_movements = _count(
        db,
        InventoryMovement,
        InventoryMovement.movement_type
        == InventoryMovementType.ADJUSTMENT,
    )

    return InventoryReport(
        total_materials=total_materials,
        active_materials=active_materials,
        inactive_materials=inactive_materials,
        low_stock_materials=low_stock_materials,

        total_inventory_movements=(
            total_inventory_movements
        ),
        stock_in_movements=stock_in_movements,
        stock_out_movements=stock_out_movements,
        adjustment_movements=adjustment_movements,
    )


def get_maintenance_report(
    db: Session,
) -> MaintenanceReport:

    total_machines = _count(
        db,
        Machine,
    )

    machines_under_maintenance = _count(
        db,
        Machine,
        Machine.status == "Under Maintenance",
    )

    total_maintenance_records = _count(
        db,
        MachineMaintenance,
    )

    scheduled_maintenance = _count(
        db,
        MachineMaintenance,
        MachineMaintenance.status
        == MaintenanceStatus.SCHEDULED,
    )

    in_progress_maintenance = _count(
        db,
        MachineMaintenance,
        MachineMaintenance.status
        == MaintenanceStatus.IN_PROGRESS,
    )

    completed_maintenance = _count(
        db,
        MachineMaintenance,
        MachineMaintenance.status
        == MaintenanceStatus.COMPLETED,
    )

    cancelled_maintenance = _count(
        db,
        MachineMaintenance,
        MachineMaintenance.status
        == MaintenanceStatus.CANCELLED,
    )

    total_downtime_records = _count(
        db,
        MachineDowntime,
    )

    return MaintenanceReport(
        total_machines=total_machines,
        machines_under_maintenance=(
            machines_under_maintenance
        ),

        total_maintenance_records=(
            total_maintenance_records
        ),
        scheduled_maintenance=scheduled_maintenance,
        in_progress_maintenance=(
            in_progress_maintenance
        ),
        completed_maintenance=completed_maintenance,
        cancelled_maintenance=cancelled_maintenance,

        total_downtime_records=(
            total_downtime_records
        ),
    )


def get_downtime_report(
    db: Session,
) -> DowntimeReport:

    total_downtime_records = _count(
        db,
        MachineDowntime,
    )

    open_downtime_records = _count(
        db,
        MachineDowntime,
        MachineDowntime.status
        == DowntimeStatus.OPEN,
    )

    in_progress_downtime_records = _count(
        db,
        MachineDowntime,
        MachineDowntime.status
        == DowntimeStatus.IN_PROGRESS,
    )

    resolved_downtime_records = _count(
        db,
        MachineDowntime,
        MachineDowntime.status
        == DowntimeStatus.RESOLVED,
    )

    cancelled_downtime_records = _count(
        db,
        MachineDowntime,
        MachineDowntime.status
        == DowntimeStatus.CANCELLED,
    )

    total_duration_hours = _sum(
        db,
        MachineDowntime,
        MachineDowntime.duration_hours,
    )

    return DowntimeReport(
        total_downtime_records=(
            total_downtime_records
        ),
        open_downtime_records=(
            open_downtime_records
        ),
        in_progress_downtime_records=(
            in_progress_downtime_records
        ),
        resolved_downtime_records=(
            resolved_downtime_records
        ),
        cancelled_downtime_records=(
            cancelled_downtime_records
        ),
        total_duration_hours=total_duration_hours,
    )


def get_production_approval_report(
    db: Session,
) -> ProductionApprovalReport:

    total_approvals = _count(
        db,
        ProductionApproval,
    )

    pending_approvals = _count(
        db,
        ProductionApproval,
        ProductionApproval.status
        == ProductionApprovalStatus.PENDING,
    )

    approved_approvals = _count(
        db,
        ProductionApproval,
        ProductionApproval.status
        == ProductionApprovalStatus.APPROVED,
    )

    rejected_approvals = _count(
        db,
        ProductionApproval,
        ProductionApproval.status
        == ProductionApprovalStatus.REJECTED,
    )

    cancelled_approvals = _count(
        db,
        ProductionApproval,
        ProductionApproval.status
        == ProductionApprovalStatus.CANCELLED,
    )

    return ProductionApprovalReport(
        total_approvals=total_approvals,
        pending_approvals=pending_approvals,
        approved_approvals=approved_approvals,
        rejected_approvals=rejected_approvals,
        cancelled_approvals=cancelled_approvals,
    )