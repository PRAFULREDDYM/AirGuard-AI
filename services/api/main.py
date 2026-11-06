import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.api.config import settings
from services.api.database import init_db, AsyncSessionLocal
from services.api.routers import (
    auth, homes, rooms, devices, readings, events, automations, models, websocket,
    gateway, catalog
)
from services.integrations.simulation_adapter import simulation_adapter
from services.api.models import Device, IntegrationType
from services.api.schemas import SensorReadingCreate
from services.ingestion.service import IngestionService
from services.automation.engine import AutomationEngine
from services.ml_environment.anomaly import AnomalyDetector
from sqlalchemy.future import select

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("airguard")

background_tasks = set()

async def background_simulation_loop():
    """Periodically generates fresh synthetic telemetry for simulated devices."""
    await asyncio.sleep(5)  # Initial grace delay
    logger.info("Starting background environmental telemetry simulation loop...")
    while True:
        try:
            async with AsyncSessionLocal() as db:
                res = await db.execute(
                    select(Device).where(Device.connection_protocol == IntegrationType.SIMULATION)
                )
                sim_devices = res.scalars().all()
                for dev in sim_devices:
                    device_key = "sim_airgradient_01" if "airgradient" in dev.name.lower() else "sim_purifier_01"
                    readings_raw = await simulation_adapter.read_telemetry(device_key)
                    for item in readings_raw:
                        r_create = SensorReadingCreate(
                            device_id=dev.id,
                            sensor_id=item["sensor_id"],
                            timestamp=item["timestamp"],
                            measurement_type=item["measurement_type"],
                            value=item["value"],
                            unit=item["unit"],
                            provenance=item["provenance"],
                            calibration_quality=item["calibration_quality"],
                            source_integration="simulation"
                        )
                        reading = await IngestionService.ingest_reading(db, r_create, broadcast=True)
                        await AnomalyDetector.evaluate_reading(db, reading)
                        await AutomationEngine.evaluate_rules_for_reading(db, reading)
        except Exception as e:
            logger.error(f"Error in simulation loop: {e}")
        await asyncio.sleep(8)  # 8-second sampling interval

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables created
    logger.info("Initializing database schema...")
    await init_db()
    # Start background simulator
    task = asyncio.create_task(background_simulation_loop())
    background_tasks.add(task)
    yield
    # Shutdown
    task.cancel()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-powered environmental air-quality monitoring, odor-pattern recognition and smart-device automation API.",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
v1 = settings.API_V1_STR
app.include_router(auth.router, prefix=v1)
app.include_router(homes.router, prefix=v1)
app.include_router(rooms.router, prefix=v1)
app.include_router(devices.router, prefix=v1)
app.include_router(readings.router, prefix=v1)
app.include_router(events.router, prefix=v1)
app.include_router(automations.router, prefix=v1)
app.include_router(models.router, prefix=v1)
app.include_router(gateway.router, prefix=v1)
app.include_router(catalog.router, prefix=v1)
app.include_router(websocket.router)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

@app.get("/")
async def root():
    return {
        "message": "AirGuard AI API is operational.",
        "documentation": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.api.main:app", host="0.0.0.0", port=8000, reload=True)

