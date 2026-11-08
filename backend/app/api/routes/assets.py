
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.models.models import Substation, Transformer
from app.schemas.schemas import (
    SubstationCreate,
    SubstationResponse,
    TransformerCreate,
    TransformerResponse,
)

router = APIRouter(prefix="/assets", tags=["Grid Assets"])


@router.get("/substations", response_model=list[SubstationResponse])
def list_substations(db: Session = Depends(get_db)):
    return db.scalars(
        select(Substation).order_by(Substation.name)
    ).all()


@router.post("/substations", response_model=SubstationResponse, status_code=201)
def create_substation(
    data: SubstationCreate,
    db: Session = Depends(get_db),
):
    existing = db.scalar(
        select(Substation).where(Substation.code == data.code)
    )
    if existing:
        raise HTTPException(409, "Substation code already exists")

    substation = Substation(**data.model_dump())
    db.add(substation)
    db.commit()
    db.refresh(substation)
    return substation


@router.get("/transformers", response_model=list[TransformerResponse])
def list_transformers(db: Session = Depends(get_db)):
    return db.scalars(
        select(Transformer).order_by(Transformer.code)
    ).all()


@router.post("/transformers", response_model=TransformerResponse, status_code=201)
def create_transformer(
    data: TransformerCreate,
    db: Session = Depends(get_db),
):
    if db.scalar(
        select(Transformer).where(Transformer.code == data.code)
    ):
        raise HTTPException(409, "Transformer code already exists")

    if not db.get(Substation, data.substation_id):
        raise HTTPException(404, "Substation not found")

    transformer = Transformer(**data.model_dump())
    db.add(transformer)
    db.commit()
    db.refresh(transformer)
    return transformer
