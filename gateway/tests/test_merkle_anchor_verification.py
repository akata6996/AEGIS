import json

from app.anchor.service import AnchorOrchestrator
from app.core.config import settings
from app.db.bootstrap import run_sql_file
from app.db.repositories import MerkleRepository, VerificationLogRepository
from app.db.sqlite import transaction
from app.logging.hash_chain import compute_record_hash
from app.merkle.service import MerkleAggregationService
from app.verification.service import VerificationWorkspaceService


def _seed_admitted(conn):
    conn.execute(
        "INSERT INTO enrollment_registry(node_id, is_active, enrolled_at) VALUES ('node-1',1,datetime('now'))"
    )
    vrepo = VerificationLogRepository(conn)
    prev_hash = None
    for seq in range(3):
        canonical = json.dumps(
            {
                'node_id': 'node-1',
                'seq_num': seq,
                'timestamp': f'2026-01-01T00:00:0{seq}+00:00',
                'sensor_value': str(20 + seq),
                'sensor_type': 'temperature',
                'unit': 'C',
                'metadata': {},
            },
            sort_keys=True,
            separators=(',', ':'),
        )
        record_hash = compute_record_hash(canonical, prev_hash)
        vrepo.insert_admitted(
            node_id='node-1',
            seq_num=seq,
            packet_timestamp=f'2026-01-01T00:00:0{seq}+00:00',
            gateway_received_at=f'2026-01-01T00:00:0{seq}+00:00',
            sensor_value=20 + seq,
            sensor_type='temperature',
            unit='C',
            anomaly_flags_json='[]',
            packet_canonical_json=canonical,
            prev_record_hash=prev_hash,
            record_hash=record_hash,
        )
        prev_hash = record_hash


def test_merkle_batch_and_verification_with_anchor(tmp_path, monkeypatch):
    monkeypatch.setenv('AEGIS_DB_PATH', str(tmp_path / 'aegis.db'))
    settings.db_path = str(tmp_path / 'aegis.db')
    settings.solana_anchor_mock_mode = True

    run_sql_file('migrations/0001_initial.sql')

    with transaction() as conn:
        _seed_admitted(conn)

    batch = MerkleAggregationService().run_batch()
    assert batch is not None
    assert batch.leaf_count == 3

    anchor_result = AnchorOrchestrator().anchor_next_pending_batch()
    assert anchor_result.attempted is True
    assert anchor_result.success is True

    verification = VerificationWorkspaceService().verify_record(1)
    assert verification['hash_chain_ok'] is True
    assert verification['merkle_ok'] is True
    assert verification['anchor_ok'] is True

    with transaction() as conn:
        batch_row = MerkleRepository(conn).fetch_batch(batch.batch_id)
        assert batch_row is not None
        assert batch_row['status'] == 'anchored'
