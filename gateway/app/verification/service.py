import json

from app.db.repositories import AnchorAttemptsRepository, MerkleRepository, VerificationLogRepository
from app.db.sqlite import transaction
from app.logging.hash_chain import compute_record_hash
from app.merkle.service import MerkleAggregationService


class VerificationWorkspaceService:
    """Independent recomputation service for chain, Merkle path, and anchor references."""

    def verify_record(self, verification_log_id: int) -> dict:
        with transaction() as conn:
            verification_repo = VerificationLogRepository(conn)
            merkle_repo = MerkleRepository(conn)
            anchor_repo = AnchorAttemptsRepository(conn)

            row = verification_repo.fetch_by_id(verification_log_id)
            if not row:
                return {'status': 'not_found', 'verification_log_id': verification_log_id}

            recomputed_hash = compute_record_hash(row['packet_canonical_json'], row['prev_record_hash'])
            hash_chain_ok = recomputed_hash == row['record_hash']

            if row['merkle_batch_id'] is None:
                return {
                    'status': 'pending_merkle',
                    'verification_log_id': verification_log_id,
                    'hash_chain_ok': hash_chain_ok,
                    'recomputed_hash': recomputed_hash,
                    'stored_hash': row['record_hash'],
                }

            batch_id = int(row['merkle_batch_id'])
            batch = merkle_repo.fetch_batch(batch_id)
            leaf = merkle_repo.fetch_leaf_by_record(verification_log_id)
            proof_row = merkle_repo.fetch_proof(batch_id, verification_log_id)
            if not batch or not leaf or not proof_row:
                return {
                    'status': 'incomplete_merkle_data',
                    'verification_log_id': verification_log_id,
                    'hash_chain_ok': hash_chain_ok,
                }

            proof = json.loads(proof_row['proof_json'])
            recomputed_root = MerkleAggregationService.recompute_root_from_proof(leaf['leaf_hash'], proof)
            merkle_ok = recomputed_root == batch['merkle_root']

            anchor = anchor_repo.fetch_success_for_batch(batch_id)
            anchor_ok = anchor is not None

            return {
                'status': 'verified' if (hash_chain_ok and merkle_ok and anchor_ok) else 'partial',
                'verification_log_id': verification_log_id,
                'hash_chain_ok': hash_chain_ok,
                'merkle_ok': merkle_ok,
                'anchor_ok': anchor_ok,
                'batch_id': batch_id,
                'recomputed_hash': recomputed_hash,
                'stored_hash': row['record_hash'],
                'recomputed_root': recomputed_root,
                'stored_root': batch['merkle_root'],
                'anchor_tx_signature': anchor['tx_signature'] if anchor else None,
            }
