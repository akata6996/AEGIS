from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import timedelta, timezone
import json
import time

from app.core.config import settings
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


@dataclass
class ScenarioResult:
    scenario: str
    expected: str
    actual: str
    affected_layer: str
    detection_success: bool
    latency_ms: float


class ThreatScenarioRunner:
    def __init__(self, db_path: str) -> None:
        settings.db_path = db_path
        run_sql_file('migrations/0001_initial.sql')

    def seed_enrollment(self, node_id: str = 'node-threat') -> None:
        with transaction() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO enrollment_registry(node_id, is_active, enrolled_at) VALUES (?,1,datetime('now'))",
                (node_id,),
            )

    @staticmethod
    def _engine(conn):
        return EnforcementEngine(
            EnrollmentRepository(conn),
            SessionRepository(conn),
            VerificationLogRepository(conn),
            RejectionLogRepository(conn),
        )

    def _run_packet(self, packet: SensorPacket, gateway_received_at):
        t0 = time.perf_counter()
        with transaction() as conn:
            result = self._engine(conn).process_packet(packet, gateway_received_at)
        latency = (time.perf_counter() - t0) * 1000
        return result, latency

    def run(self) -> list[ScenarioResult]:
        self.seed_enrollment()
        now = utc_now().astimezone(timezone.utc)
        node = 'node-threat'
        out: list[ScenarioResult] = []

        # benign normal traffic
        r, l = self._run_packet(
            SensorPacket(node_id=node, seq_num=0, timestamp=now, sensor_value='22.0'), now
        )
        out.append(
            ScenarioResult('benign_normal_traffic', 'ADMITTED', r.reason_code, 'enforcement', r.admitted, l)
        )

        # replay attack (duplicate seq)
        r, l = self._run_packet(
            SensorPacket(node_id=node, seq_num=0, timestamp=now + timedelta(seconds=1), sensor_value='22.1'),
            now + timedelta(seconds=1),
        )
        out.append(
            ScenarioResult(
                'replay_attack',
                'SEQUENCE_CONTINUITY_FAILED',
                r.reason_code,
                'sequence_continuity',
                r.reason_code == 'SEQUENCE_CONTINUITY_FAILED',
                l,
            )
        )

        # delayed injection
        stale_ts = now - timedelta(milliseconds=settings.max_ingest_delay_ms + 200)
        r, l = self._run_packet(SensorPacket(node_id=node, seq_num=1, timestamp=stale_ts, sensor_value='23.0'), now)
        out.append(
            ScenarioResult(
                'delayed_batch_injection',
                'BOUNDED_DELAY_FAILED',
                r.reason_code,
                'bounded_delay',
                r.reason_code == 'BOUNDED_DELAY_FAILED',
                l,
            )
        )

        # sequence discontinuity (skip)
        r, l = self._run_packet(
            SensorPacket(node_id=node, seq_num=3, timestamp=now + timedelta(seconds=2), sensor_value='23.1'),
            now + timedelta(seconds=2),
        )
        out.append(
            ScenarioResult(
                'sequence_discontinuity',
                'SEQUENCE_CONTINUITY_FAILED',
                r.reason_code,
                'sequence_continuity',
                r.reason_code == 'SEQUENCE_CONTINUITY_FAILED',
                l,
            )
        )

        # mqtt session interruption/liveness (force requires_reset)
        with transaction() as conn:
            SessionRepository(conn).set_requires_reset(node)
        r, l = self._run_packet(
            SensorPacket(node_id=node, seq_num=1, timestamp=now + timedelta(seconds=3), sensor_value='23.2'),
            now + timedelta(seconds=3),
        )
        out.append(
            ScenarioResult(
                'mqtt_session_interruption',
                'SESSION_REQUIRES_RESET',
                r.reason_code,
                'session_continuity',
                r.reason_code == 'SESSION_REQUIRES_RESET',
                l,
            )
        )

        # duplicate packet edge case
        with transaction() as conn:
            SessionRepository(conn).operator_reset(node, 1, 'resume for edge-case run', 'tester')
        r1, _ = self._run_packet(
            SensorPacket(node_id=node, seq_num=1, timestamp=now + timedelta(seconds=4), sensor_value='24.0'),
            now + timedelta(seconds=4),
        )
        r2, l = self._run_packet(
            SensorPacket(node_id=node, seq_num=1, timestamp=now + timedelta(seconds=5), sensor_value='24.0'),
            now + timedelta(seconds=5),
        )
        out.append(
            ScenarioResult(
                'duplicate_packet',
                'SEQUENCE_CONTINUITY_FAILED',
                r2.reason_code,
                'sequence_continuity',
                (r1.admitted and r2.reason_code == 'SEQUENCE_CONTINUITY_FAILED'),
                l,
            )
        )

        return out


def main(db_path: str = './data/threat_scenarios.db') -> None:
    results = [asdict(r) for r in ThreatScenarioRunner(db_path=db_path).run()]
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
