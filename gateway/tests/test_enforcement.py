from datetime import timedelta, timezone

from app.core.time import utc_now
from app.db.bootstrap import run_sql_file
from app.db.repositories import (
    EnrollmentRepository,
    RejectionLogRepository,
    SessionRepository,
    VerificationLogRepository,
)
from app.db.sqlite import transaction
from app.enforcement.engine import EnforcementEngine
from app.ingestion.contracts import SensorPacket


def _enroll_node(conn, node_id: str = 'node-1'):
    conn.execute(
        "INSERT INTO enrollment_registry(node_id, is_active, enrolled_at) VALUES (?, 1, datetime('now'))",
        (node_id,),
    )


def test_enforcement_admit_and_reject_sequence(tmp_path, monkeypatch):
    monkeypatch.setenv('AEGIS_DB_PATH', str(tmp_path / 'aegis.db'))
    from app.core.config import settings

    settings.db_path = str(tmp_path / 'aegis.db')
    run_sql_file('migrations/0001_initial.sql')

    now = utc_now().astimezone(timezone.utc)

    with transaction() as conn:
        _enroll_node(conn)
        engine = EnforcementEngine(
            EnrollmentRepository(conn),
            SessionRepository(conn),
            VerificationLogRepository(conn),
            RejectionLogRepository(conn),
        )
        admitted = engine.process_packet(
            SensorPacket(
                node_id='node-1',
                seq_num=0,
                timestamp=now,
                sensor_value='25.1',
                sensor_type='temperature',
                unit='C',
            ),
            gateway_received_at=now,
        )
        assert admitted.admitted is True

    with transaction() as conn:
        engine = EnforcementEngine(
            EnrollmentRepository(conn),
            SessionRepository(conn),
            VerificationLogRepository(conn),
            RejectionLogRepository(conn),
        )
        rejected = engine.process_packet(
            SensorPacket(
                node_id='node-1',
                seq_num=2,
                timestamp=now + timedelta(seconds=1),
                sensor_value='25.2',
                sensor_type='temperature',
                unit='C',
            ),
            gateway_received_at=now + timedelta(seconds=1),
        )
        assert rejected.admitted is False
        assert rejected.reason_code == 'SEQUENCE_CONTINUITY_FAILED'
