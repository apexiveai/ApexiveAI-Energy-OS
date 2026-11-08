
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.models import (
    Meter, MeterReading, Customer
)

router = APIRouter(prefix="/meters", tags=["Meter Management"])


@router.get("/")
def list_meters(db: Session = Depends(get_db)):
    return db.scalars(
        select(Meter).order_by(Meter.id.desc())
    ).all()


@router.post("/{meter_id}/readings", status_code=201)
def record_reading(
    meter_id: int,
    data: dict,
    db: Session = Depends(get_db),
):
    meter = db.get(Meter, meter_id)

    if not meter or not meter.is_active:
        raise HTTPException(404, "Active meter not found")

    period = data.get("reading_period", "")
    reading = data.get("reading_kwh")

    if (
        not isinstance(period, str)
        or len(period) != 7
        or period[4] != "-"
        or not period[:4].isdigit()
        or not period[5:7].isdigit()
        or not 1 <= int(period[5:7]) <= 12
    ):
        raise HTTPException(422, "Period must be YYYY-MM")

    if not isinstance(reading, (int, float)) or isinstance(reading, bool):
        raise HTTPException(422, "Reading must be numeric")

    if reading < 0:
        raise HTTPException(422, "Reading cannot be negative")

    existing = db.scalar(
        select(MeterReading).where(
            MeterReading.meter_id == meter_id,
            MeterReading.reading_period == period
        )
    )

    if existing:
        raise HTTPException(409, "Reading already exists for this period")

    previous = db.scalar(
        select(MeterReading)
        .where(MeterReading.meter_id == meter_id)
        .order_by(MeterReading.reading_period.desc())
        .limit(1)
    )

    previous_value = (
        previous.reading_kwh if previous
        else meter.last_reading_kwh
    )

    if reading < previous_value:
        raise HTTPException(
            422,
            "New reading cannot be lower than previous reading"
        )

    consumption = reading - previous_value

    record = MeterReading(
        meter_id=meter_id,
        reading_period=period,
        previous_reading_kwh=previous_value,
        reading_kwh=reading,
        consumption_kwh=consumption,
        recorded_by=data.get("recorded_by"),
    )

    meter.last_reading_kwh = reading

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


@router.get("/{meter_id}/readings")
def get_readings(
    meter_id: int,
    db: Session = Depends(get_db),
):
    if not db.get(Meter, meter_id):
        raise HTTPException(404, "Meter not found")

    return db.scalars(
        select(MeterReading)
        .where(MeterReading.meter_id == meter_id)
        .order_by(MeterReading.reading_period.desc())
    ).all()
