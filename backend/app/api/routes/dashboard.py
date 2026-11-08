
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.models import (
    Customer, Substation, Transformer, Outage,
    MaintenanceTask, OutageStatus
)

router = APIRouter(prefix="/dashboard", tags=["Executive Dashboard"])


@router.get("/overview")
def get_overview(db: Session = Depends(get_db)):
    total_customers = db.scalar(
        select(func.count(Customer.id)).where(Customer.is_active.is_(True))
    ) or 0

    total_substations = db.scalar(
        select(func.count(Substation.id)).where(Substation.is_active.is_(True))
    ) or 0

    total_transformers = db.scalar(
        select(func.count(Transformer.id)).where(Transformer.is_active.is_(True))
    ) or 0

    active_outages = db.scalar(
        select(func.count(Outage.id)).where(
            Outage.status != OutageStatus.RESOLVED
        )
    ) or 0

    pending_maintenance = db.scalar(
        select(func.count(MaintenanceTask.id)).where(
            MaintenanceTask.status.in_(["pending", "in_progress"])
        )
    ) or 0

    affected_customers = db.scalar(
        select(func.coalesce(func.sum(Outage.affected_customers), 0)).where(
            Outage.status != OutageStatus.RESOLVED
        )
    ) or 0

    return {
        "success": True,
        "data": {
            "total_customers": total_customers,
            "total_substations": total_substations,
            "total_transformers": total_transformers,
            "active_outages": active_outages,
            "pending_maintenance": pending_maintenance,
            "affected_customers": affected_customers,
            "data_source": "postgresql",
        }
    }
