from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.time import as_iso8601, utc_now

router = APIRouter()

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / 'templates'
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok', 'timestamp': as_iso8601(utc_now())}


@router.get('/')
def root() -> RedirectResponse:
    return RedirectResponse(url='/ui', status_code=302)


@router.get('/ui')
def dashboard_ui(request: Request):
    return templates.TemplateResponse(
        request=request,
        name='dashboard.html',
        context={'title': 'AEGIS Operator Console'},
    )
