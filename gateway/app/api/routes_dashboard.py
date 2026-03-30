from fastapi import APIRouter

from app.dashboard.service import DashboardReadService

router = APIRouter(prefix='/dashboard', tags=['dashboard'])
service = DashboardReadService()


@router.get('/overview')
def overview() -> dict:
    return service.overview()
