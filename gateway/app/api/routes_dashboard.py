from fastapi import APIRouter, Query

from app.dashboard.service import DashboardReadService

router = APIRouter(prefix='/dashboard', tags=['dashboard'])
service = DashboardReadService()


@router.get('/overview')
def overview() -> dict:
    return service.overview()


@router.get('/rejections/recent')
def recent_rejections(limit: int = Query(default=20, ge=1, le=200)) -> dict:
    return {'items': service.recent_rejections(limit=limit)}


@router.get('/anchors/recent')
def recent_anchors(limit: int = Query(default=20, ge=1, le=200)) -> dict:
    return {'items': service.recent_anchor_attempts(limit=limit)}
