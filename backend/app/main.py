
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.db.session import Base, engine
from app.models import (
    Substation, Transformer, Customer,
    Meter, Outage, MaintenanceTask
)
from app.api.routes import dashboard, outages, assets, customers, meters, billing, gis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Development bootstrap only.
    # Production schema changes will use Alembic migrations.
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="ApexiveAI Smart Energy and EPC Management Platform API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    dashboard.router,
    prefix=settings.API_V1_PREFIX
)

app.include_router(
    outages.router,
    prefix=settings.API_V1_PREFIX
)

app.include_router(
    assets.router,
    prefix=settings.API_V1_PREFIX
)

app.include_router(
    customers.router,
    prefix=settings.API_V1_PREFIX
)

app.include_router(
    meters.router,
    prefix=settings.API_V1_PREFIX
)

app.include_router(
    billing.router,
    prefix=settings.API_V1_PREFIX
)

app.include_router(
    gis.router,
    prefix=settings.API_V1_PREFIX
)

@app.get("/")
def root():
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "documentation": "/docs",
    }


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "application": settings.APP_NAME,
        }
    except Exception as exc:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(exc),
        }
