
from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from decimal import Decimal
from app.db.session import Base
from sqlalchemy import (
    String, Integer, Float, Boolean, DateTime,
    ForeignKey, Enum, Text, Numeric, JSON,
    UniqueConstraint, CheckConstraint
)

def utc_now():
    return datetime.now(timezone.utc)


class OutageStatus(str, enum.Enum):
    REPORTED = "reported"
    INVESTIGATING = "investigating"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class Priority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Substation(Base):
    __tablename__ = "substations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    region: Mapped[str] = mapped_column(String(100), index=True)
    township: Mapped[str] = mapped_column(String(100))
    voltage_kv: Mapped[float] = mapped_column(Float)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    capacity_mva: Mapped[float] = mapped_column(Float, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )

    transformers = relationship("Transformer", back_populates="substation")


class Transformer(Base):
    __tablename__ = "transformers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    substation_id: Mapped[int] = mapped_column(
        ForeignKey("substations.id", ondelete="CASCADE")
    )
    capacity_kva: Mapped[float] = mapped_column(Float)
    load_percentage: Mapped[float] = mapped_column(Float, default=0)
    condition: Mapped[str] = mapped_column(String(50), default="operational")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    substation = relationship("Substation", back_populates="transformers")


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    customer_number: Mapped[str] = mapped_column(
        String(50), unique=True, index=True
    )
    full_name: Mapped[str] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    address: Mapped[str] = mapped_column(Text)
    region: Mapped[str] = mapped_column(String(100), index=True)
    township: Mapped[str] = mapped_column(String(100), index=True)
    customer_type: Mapped[str] = mapped_column(
        String(50), default="residential"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )


class Meter(Base):
    __tablename__ = "meters"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    meter_number: Mapped[str] = mapped_column(
        String(100), unique=True, index=True
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT")
    )
    meter_type: Mapped[str] = mapped_column(
        String(50), default="digital"
    )
    last_reading_kwh: Mapped[float] = mapped_column(Float, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Outage(Base):
    __tablename__ = "outages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    reference_number: Mapped[str] = mapped_column(
        String(50), unique=True, index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    region: Mapped[str] = mapped_column(String(100), index=True)
    township: Mapped[str] = mapped_column(String(100), index=True)
    priority: Mapped[Priority] = mapped_column(
        Enum(Priority), default=Priority.MEDIUM
    )
    status: Mapped[OutageStatus] = mapped_column(
        Enum(OutageStatus), default=OutageStatus.REPORTED
    )
    affected_customers: Mapped[int] = mapped_column(Integer, default=0)
    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class MaintenanceTask(Base):
    __tablename__ = "maintenance_tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    task_number: Mapped[str] = mapped_column(
        String(50), unique=True, index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    asset_type: Mapped[str] = mapped_column(String(100))
    asset_code: Mapped[str] = mapped_column(String(100))
    township: Mapped[str] = mapped_column(String(100), index=True)
    assigned_team: Mapped[str | None] = mapped_column(
        String(150), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default="pending"
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

class MeterReading(Base):
    __tablename__ = "meter_readings"

    __table_args__ = (
        CheckConstraint("reading_kwh >= 0"),
        UniqueConstraint("meter_id", "reading_period", name="uq_meter_period"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    meter_id: Mapped[int] = mapped_column(
        ForeignKey("meters.id", ondelete="RESTRICT"), index=True
    )
    reading_period: Mapped[str] = mapped_column(String(7), index=True)
    previous_reading_kwh: Mapped[float] = mapped_column(Float)
    reading_kwh: Mapped[float] = mapped_column(Float)
    consumption_kwh: Mapped[float] = mapped_column(Float)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    recorded_by: Mapped[str | None] = mapped_column(
        String(150), nullable=True
    )


class ElectricityBill(Base):
    __tablename__ = "electricity_bills"

    __table_args__ = (
        UniqueConstraint(
            "customer_id", "billing_period",
            name="uq_customer_billing_period"
        ),
        CheckConstraint("consumption_kwh >= 0"),
        CheckConstraint("total_amount >= 0"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_number: Mapped[str] = mapped_column(
        String(60), unique=True, index=True
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), index=True
    )
    meter_id: Mapped[int] = mapped_column(
        ForeignKey("meters.id", ondelete="RESTRICT")
    )
    billing_period: Mapped[str] = mapped_column(String(7), index=True)
    consumption_kwh: Mapped[float] = mapped_column(Float)
    unit_rate: Mapped[Decimal] = mapped_column(Numeric(14, 4))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3), default="MMK")
    status: Mapped[str] = mapped_column(String(30), default="unpaid")
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class ElectricityPayment(Base):
    __tablename__ = "electricity_payments"

    __table_args__ = (
        CheckConstraint("amount > 0"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    receipt_number: Mapped[str] = mapped_column(
        String(60), unique=True, index=True
    )
    bill_id: Mapped[int] = mapped_column(
        ForeignKey("electricity_bills.id", ondelete="RESTRICT"),
        index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    payment_method: Mapped[str] = mapped_column(
        String(40), default="cash"
    )
    transaction_reference: Mapped[str | None] = mapped_column(
        String(150), nullable=True
    )
    paid_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    received_by: Mapped[str | None] = mapped_column(
        String(150), nullable=True
    )

class GridMapFeature(Base):
    __tablename__ = "grid_map_features"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    feature_code: Mapped[str] = mapped_column(
        String(100), unique=True, index=True
    )

    feature_type: Mapped[str] = mapped_column(
        String(50), index=True
    )

    name: Mapped[str] = mapped_column(String(200))

    region: Mapped[str] = mapped_column(
        String(100), index=True
    )

    township: Mapped[str] = mapped_column(
        String(100), index=True
    )

    geometry: Mapped[dict] = mapped_column(JSON)

    properties: Mapped[dict] = mapped_column(
        JSON, default=dict
    )

    substation_id: Mapped[int | None] = mapped_column(
        ForeignKey("substations.id", ondelete="SET NULL"),
        nullable=True
    )

    transformer_id: Mapped[int | None] = mapped_column(
        ForeignKey("transformers.id", ondelete="SET NULL"),
        nullable=True
    )

    outage_id: Mapped[int | None] = mapped_column(
        ForeignKey("outages.id", ondelete="SET NULL"),
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )