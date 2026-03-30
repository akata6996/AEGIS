from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router as base_router
from app.api.routes_dashboard import router as dashboard_router
from app.api.routes_verification import router as verification_router
from app.ingestion.mqtt_service import MqttIngestionService

mqtt_service = MqttIngestionService()


@asynccontextmanager
async def lifespan(_: FastAPI):
    mqtt_service.start()
    yield
    mqtt_service.stop()


app = FastAPI(title='AEGIS Gateway', version='0.1.0', lifespan=lifespan)
app.include_router(base_router, prefix='/api/v1')
app.include_router(dashboard_router, prefix='/api/v1')
app.include_router(verification_router, prefix='/api/v1')
