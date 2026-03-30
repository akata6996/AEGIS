from fastapi import APIRouter

from app.anchor.service import AnchorOrchestrator
from app.merkle.service import MerkleAggregationService
from app.verification.service import VerificationWorkspaceService

router = APIRouter(prefix='/verification', tags=['verification'])
verification_service = VerificationWorkspaceService()
merkle_service = MerkleAggregationService()
anchor_service = AnchorOrchestrator()


@router.get('/records/{record_id}')
def verify_record(record_id: int) -> dict:
    return verification_service.verify_record(record_id)


@router.post('/batches/run')
def run_merkle_batch() -> dict:
    result = merkle_service.run_batch()
    if result is None:
        return {'status': 'no_unbatched_records'}
    return {'status': 'ok', 'batch_id': result.batch_id, 'merkle_root': result.merkle_root}


@router.post('/anchors/run-next')
def run_anchor_attempt() -> dict:
    return anchor_service.anchor_next_pending_batch_dict()
