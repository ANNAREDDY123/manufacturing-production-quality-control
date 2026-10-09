from pydantic import BaseModel


class ReportsOverview(BaseModel):
    total_plants: int
    total_production_lines: int
    total_products: int
    total_raw_materials: int
    low_stock_materials: int
    total_machines: int
    total_workers: int

    total_production_orders: int
    completed_production_orders: int
    active_production_orders: int
    cancelled_production_orders: int

    total_production_batches: int
    completed_production_batches: int
    active_production_batches: int
    cancelled_production_batches: int

    total_quality_inspections: int
    passed_quality_inspections: int
    failed_quality_inspections: int
    pending_quality_inspections: int

    total_defects: int
    open_defects: int
    resolved_defects: int
    critical_defects: int

    total_maintenance_records: int
    completed_maintenance_records: int

    total_downtime_records: int

    total_inventory_movements: int

    total_production_approvals: int
    pending_production_approvals: int


class ProductionReport(BaseModel):
    total_orders: int
    draft_orders: int
    scheduled_orders: int
    active_orders: int
    completed_orders: int
    cancelled_orders: int

    total_order_quantity: float

    total_batches: int
    planned_batches: int
    active_batches: int
    completed_batches: int
    cancelled_batches: int

    total_batch_quantity: float

    order_completion_percentage: float
    batch_completion_percentage: float


class QualityReport(BaseModel):
    total_inspections: int
    pending_inspections: int
    passed_inspections: int
    failed_inspections: int
    cancelled_inspections: int

    inspection_pass_percentage: float

    total_defects: int
    open_defects: int
    under_review_defects: int
    corrective_action_defects: int
    resolved_defects: int
    closed_defects: int
    critical_defects: int

    defect_resolution_percentage: float


class InventoryReport(BaseModel):
    total_materials: int
    active_materials: int
    inactive_materials: int
    low_stock_materials: int

    total_inventory_movements: int
    stock_in_movements: int
    stock_out_movements: int
    adjustment_movements: int


class MaintenanceReport(BaseModel):
    total_machines: int
    machines_under_maintenance: int

    total_maintenance_records: int
    scheduled_maintenance: int
    in_progress_maintenance: int
    completed_maintenance: int
    cancelled_maintenance: int

    total_downtime_records: int


class DowntimeReport(BaseModel):
    total_downtime_records: int
    open_downtime_records: int
    in_progress_downtime_records: int
    resolved_downtime_records: int
    cancelled_downtime_records: int

    total_duration_hours: float


class ProductionApprovalReport(BaseModel):
    total_approvals: int
    pending_approvals: int
    approved_approvals: int
    rejected_approvals: int
    cancelled_approvals: int