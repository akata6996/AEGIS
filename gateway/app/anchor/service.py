from dataclasses import asdict, dataclass

from app.anchor.solana_client import SolanaDevnetAnchorClient
from app.core.config import settings
from app.db.repositories import AnchorAttemptsRepository, MerkleRepository
from app.db.sqlite import transaction


@dataclass
class AnchorExecutionResult:
    attempted: bool
    batch_id: int | None
    success: bool
    tx_signature: str | None
    error: str | None


class AnchorOrchestrator:
    def __init__(self, client: SolanaDevnetAnchorClient | None = None) -> None:
        self.client = client or SolanaDevnetAnchorClient()

    def anchor_next_pending_batch(self) -> AnchorExecutionResult:
        with transaction() as conn:
            merkle_repo = MerkleRepository(conn)
            attempts_repo = AnchorAttemptsRepository(conn)

            pending = merkle_repo.fetch_latest_pending_batch()
            if not pending:
                return AnchorExecutionResult(False, None, False, None, 'no pending batch')

            batch_id = int(pending['id'])
            merkle_root = pending['merkle_root']
            attempt_no = attempts_repo.next_attempt_no(batch_id)
            if attempt_no > settings.anchor_retry_limit:
                merkle_repo.update_batch_status(batch_id, 'anchor_failed')
                return AnchorExecutionResult(True, batch_id, False, None, 'retry limit exceeded')

            result = self.client.anchor_merkle_root(merkle_root)
            attempts_repo.insert_attempt(
                merkle_batch_id=batch_id,
                attempt_no=attempt_no,
                rpc_endpoint=settings.solana_devnet_rpc,
                request_payload_json=result.request_payload_json,
                response_payload_json=result.response_payload_json,
                tx_signature=result.tx_signature,
                status='success' if result.success else 'failed',
                error_message=result.error,
            )

            merkle_repo.update_batch_status(batch_id, 'anchored' if result.success else 'anchor_failed')
            return AnchorExecutionResult(True, batch_id, result.success, result.tx_signature, result.error)

    def anchor_next_pending_batch_dict(self) -> dict:
        return asdict(self.anchor_next_pending_batch())
