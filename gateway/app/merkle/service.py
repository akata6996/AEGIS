from dataclasses import dataclass
from datetime import datetime
import json

from app.db.repositories import MerkleRepository, VerificationLogRepository
from app.db.sqlite import transaction
from app.logging.hash_chain import sha256_hex


@dataclass
class MerkleBatchResult:
    batch_id: int
    merkle_root: str
    leaf_count: int


def _pair_hash(left: str, right: str) -> str:
    return sha256_hex(f'{left}|{right}')


def build_merkle_root(leaf_hashes: list[str]) -> str:
    if not leaf_hashes:
        raise ValueError('leaf_hashes cannot be empty')

    level = leaf_hashes[:]
    while len(level) > 1:
        next_level: list[str] = []
        if len(level) % 2 == 1:
            level.append(level[-1])
        for i in range(0, len(level), 2):
            next_level.append(_pair_hash(level[i], level[i + 1]))
        level = next_level
    return level[0]


def build_merkle_proof(leaf_hashes: list[str], leaf_index: int) -> list[dict[str, str]]:
    if leaf_index < 0 or leaf_index >= len(leaf_hashes):
        raise ValueError('leaf_index out of range')

    proof: list[dict[str, str]] = []
    level = leaf_hashes[:]
    index = leaf_index

    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])

        sibling_index = index + 1 if index % 2 == 0 else index - 1
        position = 'right' if index % 2 == 0 else 'left'
        proof.append({'position': position, 'hash': level[sibling_index]})

        next_level: list[str] = []
        for i in range(0, len(level), 2):
            next_level.append(_pair_hash(level[i], level[i + 1]))

        index //= 2
        level = next_level

    return proof


class MerkleAggregationService:
    """Build deterministic Merkle batches from admitted verification_log records."""

    def run_batch(self) -> MerkleBatchResult | None:
        with transaction() as conn:
            verification_repo = VerificationLogRepository(conn)
            merkle_repo = MerkleRepository(conn)

            records = verification_repo.fetch_unbatched()
            if not records:
                return None

            leaf_hashes = [row['record_hash'] for row in records]
            merkle_root = build_merkle_root(leaf_hashes)
            batch_start = min(datetime.fromisoformat(row['created_at']) for row in records).isoformat()
            batch_end = max(datetime.fromisoformat(row['created_at']) for row in records).isoformat()

            batch_id = merkle_repo.create_batch(
                batch_start_ts=batch_start,
                batch_end_ts=batch_end,
                leaf_count=len(records),
                merkle_root=merkle_root,
            )

            for idx, row in enumerate(records):
                merkle_repo.insert_leaf(batch_id, int(row['id']), idx, row['record_hash'])
                proof = build_merkle_proof(leaf_hashes, idx)
                merkle_repo.insert_proof(batch_id, int(row['id']), json.dumps(proof, separators=(',', ':')))
                verification_repo.mark_batch(int(row['id']), batch_id)

            return MerkleBatchResult(batch_id=batch_id, merkle_root=merkle_root, leaf_count=len(records))

    @staticmethod
    def recompute_root_from_proof(leaf_hash: str, proof: list[dict[str, str]]) -> str:
        current = leaf_hash
        for step in proof:
            if step['position'] == 'left':
                current = _pair_hash(step['hash'], current)
            else:
                current = _pair_hash(current, step['hash'])
        return current
