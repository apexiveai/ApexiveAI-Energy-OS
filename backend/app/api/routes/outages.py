
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.models import Outage, OutageStatus, utc_now
from app.schemas.schemas import OutageCreate, OutageResponse, OutageUpdate

router = APIRouter(prefix="/outages", tags=["Outage Management"])


@router.get("/", response_model=list[OutageResponse])
def list_outages(
    status: OutageStatus | None = None,
    township: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    stmt = select(Outage).order_by(Outage.reported_at.desc())

    if status:
        stmt = stmt.where(Outage.status == status)

    if township:
        stmt = stmt.where(Outage.township.ilike(f"%{township}%"))

    return db.scalars(stmt.limit(limit)).all()


@router.post("/", response_model=OutageResponse, status_code=201)
def create_outage(data: OutageCreate, db: Session = Depends(get_db)):
    existing = db.scalar(
        select(Outage).where(
            Outage.reference_number == data.reference_number
        )
    )
    if existing:
        raise HTTPException(409, "Outage reference already exists")

    outage = Outage(**data.model_dump())
    db.add(outage)
    db.commit()
    db.refresh(outage)
    return outage


@router.get("/{outage_id}", response_model=OutageResponse)
def get_outage(outage_id: int, db: Session = Depends(get_db)):
    outage = db.get(Outage, outage_id)
    if not outage:
        raise HTTPException(404, "Outage not found")
    return outage


@router.patch("/{outage_id}", response_model=OutageResponse)
def update_outage(
    outage_id: int,
    data: OutageUpdate,
    db: Session = Depends(get_db),
):
    outage = db.get(Outage, outage_id)
    if not outage:
        raise HTTPException(404, "Outage not found")

    outage.status = data.status

    if data.resolved_at is not None:
        outage.resolved_at = data.resolved_at
    elif data.status == OutageStatus.RESOLVED:
        outage.resolved_at = utc_now()

    db.commit()
    db.refresh(outage)
    return outage
