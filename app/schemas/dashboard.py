from pydantic import BaseModel, ConfigDict


class DashboardOverview(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_plants: int
    active_plants: int

    total_production_lines: int
    active_production_lines: int

    total_products: int
    active_products: int

    total_raw_materials: int
    low_stock_materials: int

    total_machines: int
    active_machines: int
    machines_under_maintenance: int

    total_workers: int
    active_workers: int

    total_production_orders: int
    draft_orders: int
    scheduled_orders: int
    in_progress_orders: int
    completed_orders: int
    cancelled_orders: int

    total_production_batches: int
    planned_batches: int
    in_progress_batches: int
    paused_batches: int
    completed_batches: int
    cancelled_batches: int

    total_quality_inspections: int
    pending_inspections: int
    passed_inspections: int
    failed_inspections: int

    total_defects: int
    open_defects: int
    resolved_defects: int
    critical_defects: int

    total_maintenance_records: int
    scheduled_maintenance: int
    in_progress_maintenance: int
    completed_maintenance: int

    total_downtime_records: int
    total_inventory_movements: int
    total_production_approvals: int
    pending_production_approvals: int


class ProductionDashboard(BaseModel):
    total_orders: int
    active_orders: int
    completed_orders: int
    cancelled_orders: int

    total_batches: int
    planned_batches: int
    in_progress_batches: int
    paused_batches: int
    completed_batches: int
    cancelled_batches: int

    total_order_quantity: float
    total_batch_quantity: float

    order_completion_percentage: float
    batch_completion_percentage: float


class QualityDashboard(BaseModel):
    total_inspections: int
    pending_inspections: int
    passed_inspections: int
    failed_inspections: int

    total_defects: int
    open_defects: int
    under_review_defects: int
    corrective_action_defects: int
    resolved_defects: int
    closed_defects: int
    critical_defects: int

    inspection_pass_percentage: float
    defect_resolution_percentage: float


class MaintenanceDashboard(BaseModel):
    total_machines: int
    machines_under_maintenance: int

    total_maintenance_records: int
    scheduled_maintenance: int
    in_progress_maintenance: int
    completed_maintenance: int
    cancelled_maintenance: int

    total_downtime_records: int


class InventoryDashboard(BaseModel):
    total_materials: int
    active_materials: int
    low_stock_materials: int

    total_inventory_movements: int
    stock_in_movements: int
    stock_out_movements: int
    adjustment_movements: int