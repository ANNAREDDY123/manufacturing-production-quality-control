from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth.routes import router as auth_router
from app.api.plants.routes import router as plants_router
from app.api.products.routes import router as products_router
from app.api.materials.routes import router as materials_router
from app.api.products.bom_routes import router as bom_router
from app.api.machines.routes import router as machines_router

from app.api.production.routes import (
    router as production_lines_router,
)

from app.api.production.order_routes import (
    router as production_orders_router,
)

from app.db.init_db import init_db
from app.api.production.batch_routes import (
    router as production_batches_router,
)

from app.api.workers.routes import (
    router as workers_router,
)
from app.api.shifts.routes import router as shifts_router
from app.api.quality import router as quality_inspection_router
from app.api.defects import router as defects_router
from app.api.maintenance import router as maintenance_router
from app.api.downtime import router as downtime_router
from app.api.inventory import router as inventory_router
from app.api.approvals import router as production_approval_router		
from app.api.dashboard import router as dashboard_router
from app.api.reports import router as reports_router
from app.api.audit_logs import router as audit_logs_router
from app.api.notifications import router as notifications_router



@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Manufacturing Production & Quality Control Management System",
    description=(
        "Advanced FastAPI backend for manufacturing "
        "production and quality control management."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


app.include_router(auth_router)
app.include_router(plants_router)
app.include_router(products_router)
app.include_router(materials_router)
app.include_router(bom_router)
app.include_router(machines_router)
app.include_router(maintenance_router)
app.include_router(production_lines_router)
app.include_router(production_orders_router)
app.include_router(production_batches_router)
app.include_router(shifts_router)
app.include_router(workers_router)
app.include_router(quality_inspection_router)
app.include_router(defects_router)
app.include_router(downtime_router)
app.include_router(inventory_router)
app.include_router(production_approval_router)
app.include_router(dashboard_router)
app.include_router(reports_router)
app.include_router(audit_logs_router)
app.include_router(notifications_router)




@app.get("/", tags=["Health"])
def root():
    return {
        "message": (
            "Manufacturing Production & Quality Control "
            "Management System API is running"
        )
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "manufacturing-production-quality-control",
    }