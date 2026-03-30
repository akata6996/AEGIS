import json

from app.core.config import settings
from app.db.bootstrap import run_sql_file
from app.db.repositories import VerificationLogRepository
from app.db.sqlite import transaction
from app.logging.hash_chain import compute_record_hash
from app.workers.pipeline_worker import PipelineWorker


def _seed_admitted(conn):
    conn.execute(
        "INSERT INTO enrollment_registry(node_id, is_active, enrolled_at) VALUES ('node-1',1,datetime('now'))"
    )
    vrepo = VerificationLogRepository(conn)
    prev_hash = None
    for seq in range(2):
        canonical = json.dumps(
            {
                'node_id': 'node-1',
                'seq_num': seq,
                'timestamp': f'2026-01-01T00:00:0{seq}+00:00',
                'sensor_value': str(10 + seq),
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
            sensor_value=10 + seq,
            sensor_type='temperature',
            unit='C',
            anomaly_flags_json='[]',
            packet_canonical_json=canonical,
            prev_record_hash=prev_hash,
            record_hash=record_hash,
        )
        prev_hash = record_hash


def test_pipeline_tick_builds_batch_and_attempts_anchor(tmp_path):
    settings.db_path = str(tmp_path / 'worker.db')
    settings.solana_anchor_mock_mode = True
    run_sql_file('migrations/0001_initial.sql')

    with transaction() as conn:
        _seed_admitted(conn)

    worker = PipelineWorker(poll_seconds=1)
    result = worker.tick_once()

    assert result['batch_created'] is True
    assert result['anchor_attempted'] is True
