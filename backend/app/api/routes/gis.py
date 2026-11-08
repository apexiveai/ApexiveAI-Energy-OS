from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import (
    GridMapFeature,
    Substation,
    Transformer,
    Outage,
)


router = APIRouter(
    prefix="/gis",
    tags=["GIS & Grid Mapping"]
)


class GISFeatureCreate(BaseModel):
    feature_code: str = Field(min_length=2, max_length=100)
    feature_type: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=200)

    region: str = Field(min_length=2, max_length=100)
    township: str = Field(min_length=2, max_length=100)

    geometry: dict[str, Any]
    properties: dict[str, Any] = {}

    substation_id: int | None = None
    transformer_id: int | None = None
    outage_id: int | None = None


ALLOWED_GEOMETRIES = {
    "Point",
    "LineString",
    "Polygon",
}


def validate_coordinates(value):
    """
    Validate GeoJSON coordinates using WGS84:
    longitude: -180 to 180
    latitude:  -90 to 90
    """

    if (
        isinstance(value, list)
        and len(value) >= 2
        and isinstance(value[0], (int, float))
        and isinstance(value[1], (int, float))
    ):
        longitude = float(value[0])
        latitude = float(value[1])

        if not -180 <= longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180")

        if not -90 <= latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90")

        return

    if isinstance(value, list) and value:
        for item in value:
            validate_coordinates(item)
        return

    raise ValueError("Invalid GeoJSON coordinates")


def validate_geometry(geometry):
    if not isinstance(geometry, dict):
        raise HTTPException(422, "Geometry must be a GeoJSON object")

    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")

    if geometry_type not in ALLOWED_GEOMETRIES:
        raise HTTPException(
            422,
            "Supported geometry types: Point, LineString, Polygon"
        )

    try:
        validate_coordinates(coordinates)
    except ValueError as exc:
        raise HTTPException(422, str(exc))

    if geometry_type == "Point":
        if (
            not isinstance(coordinates, list)
            or len(coordinates) < 2
            or not isinstance(coordinates[0], (int, float))
        ):
            raise HTTPException(422, "Invalid Point geometry")

    if geometry_type == "LineString":
        if len(coordinates) < 2:
            raise HTTPException(
                422,
                "LineString requires at least two coordinates"
            )

    if geometry_type == "Polygon":
        if not coordinates or not coordinates[0]:
            raise HTTPException(422, "Invalid Polygon geometry")

        for ring in coordinates:
            if len(ring) < 4 or ring[0] != ring[-1]:
                raise HTTPException(
                    422,
                    "Polygon rings must contain at least 4 points "
                    "and be closed"
                )


@router.get("/features")
def list_features(
    region: str | None = None,
    township: str | None = None,
    feature_type: str | None = None,
    db: Session = Depends(get_db),
):
    query = select(GridMapFeature).where(
        GridMapFeature.is_active.is_(True)
    )

    if region:
        query = query.where(GridMapFeature.region == region)

    if township:
        query = query.where(GridMapFeature.township == township)

    if feature_type:
        query = query.where(
            GridMapFeature.feature_type == feature_type
        )

    features = db.scalars(
        query.order_by(GridMapFeature.name)
    ).all()

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": item.id,
                "geometry": item.geometry,
                "properties": {
                    "feature_code": item.feature_code,
                    "feature_type": item.feature_type,
                    "name": item.name,
                    "region": item.region,
                    "township": item.township,
                    "properties": item.properties,
                    "substation_id": item.substation_id,
                    "transformer_id": item.transformer_id,
                    "outage_id": item.outage_id,
                }
            }
            for item in features
        ]
    }


@router.post("/features", status_code=201)
def create_feature(
    data: GISFeatureCreate,
    db: Session = Depends(get_db),
):
    existing = db.scalar(
        select(GridMapFeature).where(
            GridMapFeature.feature_code == data.feature_code
        )
    )

    if existing:
        raise HTTPException(409, "Feature code already exists")

    validate_geometry(data.geometry)

    if data.substation_id is not None:
        if not db.get(Substation, data.substation_id):
            raise HTTPException(404, "Substation not found")

    if data.transformer_id is not None:
        if not db.get(Transformer, data.transformer_id):
            raise HTTPException(404, "Transformer not found")

    if data.outage_id is not None:
        if not db.get(Outage, data.outage_id):
            raise HTTPException(404, "Outage not found")

    feature = GridMapFeature(**data.model_dump())

    db.add(feature)
    db.commit()
    db.refresh(feature)

    return {
        "success": True,
        "id": feature.id,
        "feature_code": feature.feature_code,
        "feature_type": feature.feature_type,
        "name": feature.name,
    }


@router.get("/map")
def get_grid_map(
    region: str | None = None,
    township: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Return substations and registered GIS features
    as one GeoJSON FeatureCollection.
    """

    substation_query = select(Substation).where(
        Substation.is_active.is_(True),
        Substation.latitude.is_not(None),
        Substation.longitude.is_not(None),
    )

    feature_query = select(GridMapFeature).where(
        GridMapFeature.is_active.is_(True)
    )

    if region:
        substation_query = substation_query.where(
            Substation.region == region
        )
        feature_query = feature_query.where(
            GridMapFeature.region == region
        )

    if township:
        substation_query = substation_query.where(
            Substation.township == township
        )
        feature_query = feature_query.where(
            GridMapFeature.township == township
        )

    substations = db.scalars(substation_query).all()
    features = db.scalars(feature_query).all()

    output = []

    for item in substations:
        output.append({
            "type": "Feature",
            "id": f"substation-{item.id}",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    item.longitude,
                    item.latitude
                ]
            },
            "properties": {
                "feature_type": "substation",
                "feature_code": item.code,
                "name": item.name,
                "region": item.region,
                "township": item.township,
                "voltage_kv": item.voltage_kv,
                "capacity_mva": item.capacity_mva,
            }
        })

    for item in features:
        output.append({
            "type": "Feature",
            "id": f"gis-{item.id}",
            "geometry": item.geometry,
            "properties": {
                "feature_type": item.feature_type,
                "feature_code": item.feature_code,
                "name": item.name,
                "region": item.region,
                "township": item.township,
                **(item.properties or {}),
            }
        })

    return {
        "type": "FeatureCollection",
        "total_features": len(output),
        "features": output,
        "data_source": "postgresql_demo_data",
    }