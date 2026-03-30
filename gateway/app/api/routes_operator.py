from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db.repositories import SessionRepository
from app.db.sqlite import transaction

router = APIRouter(prefix='/operator', tags=['operator'])


class ResetRequest(BaseModel):
    new_expected_seq: int = Field(ge=0)
    reason: str = Field(min_length=3, max_length=256)
    operator_id: str = Field(min_length=1, max_length=64)


@router.post('/sessions/{node_id}/reset')
def reset_session(node_id: str, request: ResetRequest) -> dict:
    with transaction() as conn:
        session_repo = SessionRepository(conn)
        ok = session_repo.operator_reset(
            node_id=node_id,
            new_expected_seq=request.new_expected_seq,
            reason=request.reason,
            operator_id=request.operator_id,
        )
        if not ok:
            raise HTTPException(status_code=404, detail='session not found for node')

    return {'status': 'ok', 'node_id': node_id, 'new_expected_seq': request.new_expected_seq}
