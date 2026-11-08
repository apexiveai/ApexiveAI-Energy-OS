
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.models.models import OutageStatus, Priority


class OutageCreate(BaseModel):
    reference_number: str = Field(min_length=3, max_length=50)
    title: str
    description: str | None = None
    region: str
    township: str
    priority: Priority = Priority.MEDIUM
    affected_customers: int = Field(default=0, ge=0)


class OutageUpdate(BaseModel):
    status: OutageStatus
    resolved_at: datetime | None = None


class OutageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference_number: str
    title: str
    description: str | None
    region: str
    township: str
    priority: Priority
    status: OutageStatus
    affected_customers: int
    reported_at: datetime
    resolved_at: datetime | None


class SubstationCreate(BaseModel):
    code: str
    name: str
    region: str
    township: str
    voltage_kv: float = Field(gt=0)
    capacity_mva: float = Field(ge=0)
    latitude: float | None = None
    longitude: float | None = None


class SubstationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    region: str
    township: str
    voltage_kv: float
    capacity_mva: float
    latitude: float | None
    longitude: float | None
    is_active: bool


class TransformerCreate(BaseModel):
    code: str
    name: str
    substation_id: int
    capacity_kva: float = Field(gt=0)
    load_percentage: float = Field(default=0, ge=0, le=100)


class TransformerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    substation_id: int
    capacity_kva: float
    load_percentage: float
    condition: str
    is_active: bool
