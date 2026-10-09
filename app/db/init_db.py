from app.db.database import Base, engine

from app.models.bom import BOM, BOMItem
from app.models.inventory_movement import InventoryMovement
from app.models.machine import Machine
from app.models.plant import Plant
from app.models.production_batch import ProductionBatch
from app.models.production_batch_worker import ProductionBatchWorker
from app.models.production_line import ProductionLine
from app.models.production_order import ProductionOrder
from app.models.product import Product
from app.models.raw_material import RawMaterial
from app.models.shift import Shift
from app.models.shift_worker import ShiftWorker
from app.models.user import User
from app.models.worker import Worker
from app.models.quality_inspection import QualityInspection
from app.models.defect import Defect
from app.models.machine_maintenance import MachineMaintenance
from app.models.downtime import MachineDowntime
from app.models.inventory_movement import InventoryMovement
from app.models.production_approval import ProductionApproval
from app.models.audit_log import AuditLog
from app.models.notification import Notification




def init_db() -> None:
    Base.metadata.create_all(bind=engine)