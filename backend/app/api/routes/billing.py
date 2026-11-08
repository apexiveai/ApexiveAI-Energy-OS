
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.db.session import get_db
from app.models.models import (
    Customer,
    Meter,
    MeterReading,
    ElectricityBill,
    ElectricityPayment,
)

router = APIRouter(prefix="/billing", tags=["Billing & Revenue"])


@router.post("/bills", status_code=201)
def create_bill(data: dict, db: Session = Depends(get_db)):
    customer_id = data.get("customer_id")
    meter_id = data.get("meter_id")
    period = data.get("billing_period")
    invoice = data.get("invoice_number")

    if not all([customer_id, meter_id, period, invoice]):
        raise HTTPException(422, "Required billing fields are missing")

    try:
        if (
            not isinstance(period, str)
            or len(period) != 7
            or period[4] != "-"
            or not period[:4].isdigit()
            or not period[5:7].isdigit()
            or not 1 <= int(period[5:7]) <= 12
        ):
            raise ValueError()

        unit_rate = Decimal(str(data.get("unit_rate")))
        if not unit_rate.is_finite() or unit_rate < 0:
            raise ValueError()
    except (ValueError, TypeError, InvalidOperation):
        raise HTTPException(422, "Invalid billing period or unit rate")

    customer = db.get(Customer, customer_id)
    meter = db.get(Meter, meter_id)

    if not customer or not customer.is_active:
        raise HTTPException(404, "Active customer not found")

    if not meter or not meter.is_active:
        raise HTTPException(404, "Active meter not found")

    if meter.customer_id != customer.id:
        raise HTTPException(422, "Meter does not belong to customer")

    if db.scalar(
        select(ElectricityBill).where(
            ElectricityBill.invoice_number == invoice
        )
    ):
        raise HTTPException(409, "Invoice number already exists")

    if db.scalar(
        select(ElectricityBill).where(
            ElectricityBill.customer_id == customer_id,
            ElectricityBill.billing_period == period
        )
    ):
        raise HTTPException(409, "Bill already exists for this period")

    reading = db.scalar(
        select(MeterReading).where(
            MeterReading.meter_id == meter_id,
            MeterReading.reading_period == period
        )
    )

    if not reading:
        raise HTTPException(
            422, "Meter reading must exist before billing"
        )

    consumption = Decimal(str(reading.consumption_kwh))
    amount = (consumption * unit_rate).quantize(Decimal("0.01"))

    bill = ElectricityBill(
        invoice_number=invoice,
        customer_id=customer_id,
        meter_id=meter_id,
        billing_period=period,
        consumption_kwh=float(consumption),
        unit_rate=unit_rate,
        total_amount=amount,
        currency="MMK",
        status="unpaid",
    )

    db.add(bill)
    db.commit()
    db.refresh(bill)

    return bill


@router.get("/bills")
def list_bills(
    status: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(ElectricityBill).order_by(
        ElectricityBill.issued_at.desc()
    )

    if status:
        stmt = stmt.where(ElectricityBill.status == status)

    return db.scalars(stmt.limit(500)).all()


@router.get("/bills/{bill_id}")
def get_bill(bill_id: int, db: Session = Depends(get_db)):
    bill = db.get(ElectricityBill, bill_id)

    if not bill:
        raise HTTPException(404, "Bill not found")

    return bill


@router.post("/payments", status_code=201)
def record_payment(data: dict, db: Session = Depends(get_db)):
    bill_id = data.get("bill_id")
    receipt = data.get("receipt_number")

    if not bill_id or not receipt:
        raise HTTPException(422, "Bill ID and receipt are required")

    try:
        amount = Decimal(str(data.get("amount")))
        if not amount.is_finite() or amount <= 0:
            raise ValueError()
    except (ValueError, TypeError, InvalidOperation):
        raise HTTPException(422, "Invalid payment amount")

    if db.scalar(
        select(ElectricityPayment).where(
            ElectricityPayment.receipt_number == receipt
        )
    ):
        raise HTTPException(409, "Receipt number already exists")

    bill = db.get(ElectricityBill, bill_id)

    if not bill:
        raise HTTPException(404, "Bill not found")

    if bill.status == "paid":
        raise HTTPException(409, "Bill is already paid")

    paid = db.scalar(
        select(func.coalesce(func.sum(ElectricityPayment.amount), 0))
        .where(ElectricityPayment.bill_id == bill_id)
    ) or Decimal("0")

    remaining = bill.total_amount - paid

    if amount > remaining:
        raise HTTPException(
            422,
            f"Payment exceeds remaining balance: {remaining}"
        )

    payment = ElectricityPayment(
        receipt_number=receipt,
        bill_id=bill_id,
        amount=amount,
        payment_method=data.get("payment_method", "cash"),
        transaction_reference=data.get("transaction_reference"),
        received_by=data.get("received_by"),
    )

    db.add(payment)

    new_paid = paid + amount

    if new_paid == bill.total_amount:
        bill.status = "paid"
    else:
        bill.status = "partial"

    db.commit()
    db.refresh(payment)

    return {
        "success": True,
        "payment": payment,
        "total_bill": str(bill.total_amount),
        "total_paid": str(new_paid),
        "remaining_balance": str(bill.total_amount - new_paid),
        "bill_status": bill.status,
    }


@router.get("/revenue/summary")
def revenue_summary(db: Session = Depends(get_db)):
    total_billed = db.scalar(
        select(func.coalesce(func.sum(ElectricityBill.total_amount), 0))
    ) or Decimal("0")

    total_collected = db.scalar(
        select(func.coalesce(func.sum(ElectricityPayment.amount), 0))
    ) or Decimal("0")

    outstanding = total_billed - total_collected

    return {
        "currency": "MMK",
        "total_billed": str(total_billed),
        "total_collected": str(total_collected),
        "outstanding_balance": str(outstanding),
    }
