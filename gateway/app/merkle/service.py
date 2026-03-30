from dataclasses import dataclass


@dataclass
class MerkleBatchResult:
    batch_id: int
    merkle_root: str
    leaf_count: int


class MerkleAggregationService:
    """Builds deterministic Merkle batches from admitted verification_log records."""

    def run_batch(self) -> MerkleBatchResult | None:
        # Phase 5 implementation point.
        return None
