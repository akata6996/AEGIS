from fastapi import APIRouter

from app.core.time import as_iso8601, utc_now

router = APIRouter()


@router.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok', 'timestamp': as_iso8601(utc_now())}
