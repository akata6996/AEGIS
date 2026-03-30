from fastapi import APIRouter

from app.verification.service import VerificationWorkspaceService

router = APIRouter(prefix='/verification', tags=['verification'])
service = VerificationWorkspaceService()


@router.get('/records/{record_id}')
def verify_record(record_id: int) -> dict:
    return service.verify_record(record_id)
