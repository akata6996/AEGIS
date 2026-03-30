from dataclasses import dataclass
from datetime import datetime, timezone
import sqlite3


@dataclass
class EnrollmentRecord:
    node_id: str
    is_active: bool


class EnrollmentRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def get(self, node_id: str) -> EnrollmentRecord | None:
        row = self.conn.execute(
            'SELECT node_id, is_active FROM enrollment_registry WHERE node_id = ?', (node_id,)
        ).fetchone()
        if not row:
            return None
        return EnrollmentRecord(node_id=row['node_id'], is_active=bool(row['is_active']))


@dataclass
class SessionRecord:
    node_id: str
    expected_next_seq: int
    session_status: str


class SessionRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def get(self, node_id: str) -> SessionRecord | None:
        row = self.conn.execute(
            'SELECT node_id, expected_next_seq, session_status FROM session_state WHERE node_id=?',
            (node_id,),
        ).fetchone()
        if not row:
            return None
        return SessionRecord(
            node_id=row['node_id'],
            expected_next_seq=row['expected_next_seq'],
            session_status=row['session_status'],
        )

    def initialize(self, node_id: str, expected_next_seq: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            """
            INSERT INTO session_state(node_id, expected_next_seq, session_status, updated_at)
            VALUES (?, ?, 'healthy', ?)
            """,
            (node_id, expected_next_seq, now),
        )

    def update_expected_seq(self, node_id: str, expected_next_seq: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            'UPDATE session_state SET expected_next_seq=?, session_status=?, updated_at=? WHERE node_id=?',
            (expected_next_seq, 'healthy', now, node_id),
        )


class VerificationLogRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def fetch_latest_record_hash(self) -> str | None:
        row = self.conn.execute(
            'SELECT record_hash FROM verification_log ORDER BY id DESC LIMIT 1'
        ).fetchone()
        return row['record_hash'] if row else None

    def insert_admitted(
        self,
        node_id: str,
        seq_num: int,
        packet_timestamp: str,
        gateway_received_at: str,
        sensor_value: float,
        sensor_type: str | None,
        unit: str | None,
        anomaly_flags_json: str,
        packet_canonical_json: str,
        prev_record_hash: str | None,
        record_hash: str,
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        cur = self.conn.execute(
            """
            INSERT INTO verification_log(
                node_id, seq_num, packet_timestamp, gateway_received_at,
                sensor_value, sensor_type, unit, anomaly_flags_json,
                packet_canonical_json, prev_record_hash, record_hash, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                node_id,
                seq_num,
                packet_timestamp,
                gateway_received_at,
                sensor_value,
                sensor_type,
                unit,
                anomaly_flags_json,
                packet_canonical_json,
                prev_record_hash,
                record_hash,
                now,
            ),
        )
        return int(cur.lastrowid)


class RejectionLogRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def insert_rejection(
        self,
        node_id: str,
        seq_num: int | None,
        packet_timestamp: str | None,
        gateway_received_at: str,
        reason_code: str,
        reason_detail: str,
        packet_canonical_json: str,
    ) -> int:
        now = datetime.now(timezone.utc).isoformat()
        cur = self.conn.execute(
            """
            INSERT INTO rejection_log(
                node_id, seq_num, packet_timestamp, gateway_received_at,
                reason_code, reason_detail, packet_canonical_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                node_id,
                seq_num,
                packet_timestamp,
                gateway_received_at,
                reason_code,
                reason_detail,
                packet_canonical_json,
                now,
            ),
        )
        return int(cur.lastrowid)
