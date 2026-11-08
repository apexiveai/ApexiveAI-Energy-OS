
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.models import Customer, Meter

router = APIRouter(prefix="/customers", tags=["Customer Management"])


@router.get("/")
def list_customers(
    township: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    stmt = select(Customer).order_by(Customer.id.desc())

    if township:
        stmt = stmt.where(Customer.township.ilike(f"%{township}%"))

    return db.scalars(stmt.limit(limit)).all()


@router.post("/", status_code=201)
def create_customer(data: dict, db: Session = Depends(get_db)):
    required = [
        "customer_number", "full_name",
        "address", "region", "township"
    ]

    if any(not data.get(field) for field in required):
        raise HTTPException(422, "Required customer fields are missing")

    if db.scalar(
        select(Customer).where(
            Customer.customer_number == data["customer_number"]
        )
    ):
        raise HTTPException(409, "Customer number already exists")

    allowed = {
        "customer_number", "full_name", "phone",
        "address", "region", "township", "customer_type"
    }

    customer = Customer(**{
        k: v for k, v in data.items() if k in allowed
    })

    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{customer_id}")
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.get(Customer, customer_id)

    if not customer:
        raise HTTPException(404, "Customer not found")

    return customer


@router.post("/{customer_id}/meters", status_code=201)
def register_meter(
    customer_id: int,
    data: dict,
    db: Session = Depends(get_db),
):
    customer = db.get(Customer, customer_id)

    if not customer:
        raise HTTPException(404, "Customer not found")

    meter_number = data.get("meter_number")
    if not meter_number:
        raise HTTPException(422, "Meter number is required")

    if db.scalar(
        select(Meter).where(Meter.meter_number == meter_number)
    ):
        raise HTTPException(409, "Meter already registered")

    meter = Meter(
        meter_number=meter_number,
        customer_id=customer_id,
        meter_type=data.get("meter_type", "digital"),
    )

    db.add(meter)
    db.commit()
    db.refresh(meter)
    return meter


@router.get("/{customer_id}/meters")
def list_customer_meters(
    customer_id: int,
    db: Session = Depends(get_db),
):
    if not db.get(Customer, customer_id):
        raise HTTPException(404, "Customer not found")

    return db.scalars(
        select(Meter).where(Meter.customer_id == customer_id)
    ).all()
