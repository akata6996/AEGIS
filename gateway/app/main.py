from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as base_router
from app.api.routes_dashboard import router as dashboard_router
from app.api.routes_operator import router as operator_router
from app.api.routes_verification import router as verification_router
from app.ingestion.mqtt_service import MqttIngestionService
from app.workers.pipeline_worker import PipelineWorker

mqtt_service = MqttIngestionService()
pipeline_worker = PipelineWorker()


@asynccontextmanager
async def lifespan(_: FastAPI):
    mqtt_service.start()
    pipeline_worker.start()
    yield
    pipeline_worker.stop()
    mqtt_service.stop()


app = FastAPI(title='AEGIS Gateway', version='0.1.0', lifespan=lifespan)
STATIC_DIR = Path(__file__).resolve().parent / 'static'
app.mount('/static', StaticFiles(directory=str(STATIC_DIR)), name='static')

app.include_router(base_router, prefix='/api/v1')
app.include_router(dashboard_router, prefix='/api/v1')
app.include_router(verification_router, prefix='/api/v1')
app.include_router(operator_router, prefix='/api/v1')


@app.get('/')
def root_redirect():
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url='/api/v1/ui', status_code=302)
