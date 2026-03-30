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

    def set_requires_reset(self, node_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "UPDATE session_state SET session_status='requires_reset', updated_at=? WHERE node_id=?",
            (now, node_id),
        )

    def operator_reset(self, node_id: str, new_expected_seq: int, reason: str, operator_id: str) -> bool:
        row = self.conn.execute(
            'SELECT expected_next_seq FROM session_state WHERE node_id=?', (node_id,)
        ).fetchone()
        if row is None:
            return False
        previous_expected = int(row['expected_next_seq'])
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            """
            INSERT INTO operator_reset_events(
                node_id, previous_expected_seq, new_expected_seq, reason, operator_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (node_id, previous_expected, new_expected_seq, reason, operator_id, now),
        )
        self.conn.execute(
            "UPDATE session_state SET expected_next_seq=?, session_status='healthy', updated_at=? WHERE node_id=?",
            (new_expected_seq, now, node_id),
        )
        return True


class VerificationLogRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def fetch_latest_record_hash(self) -> str | None:
        row = self.conn.execute(
            'SELECT record_hash FROM verification_log ORDER BY id DESC LIMIT 1'
        ).fetchone()
        return row['record_hash'] if row else None

    def fetch_by_id(self, record_id: int) -> sqlite3.Row | None:
        return self.conn.execute('SELECT * FROM verification_log WHERE id=?', (record_id,)).fetchone()

    def fetch_unbatched(self) -> list[sqlite3.Row]:
        rows = self.conn.execute(
            'SELECT * FROM verification_log WHERE merkle_batch_id IS NULL ORDER BY id ASC'
        ).fetchall()
        return list(rows)

    def fetch_by_batch(self, merkle_batch_id: int) -> list[sqlite3.Row]:
        rows = self.conn.execute(
            'SELECT * FROM verification_log WHERE merkle_batch_id=? ORDER BY id ASC', (merkle_batch_id,)
        ).fetchall()
        return list(rows)

    def mark_batch(self, verification_log_id: int, merkle_batch_id: int) -> None:
        self.conn.execute(
            'UPDATE verification_log SET merkle_batch_id=? WHERE id=?',
            (merkle_batch_id, verification_log_id),
        )

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


class MerkleRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create_batch(self, batch_start_ts: str, batch_end_ts: str, leaf_count: int, merkle_root: str) -> int:
        now = datetime.now(timezone.utc).isoformat()
        cur = self.conn.execute(
            """
            INSERT INTO merkle_batch_metadata(
                batch_start_ts, batch_end_ts, leaf_count, merkle_root, status, created_at
            ) VALUES (?, ?, ?, ?, 'pending_anchor', ?)
            """,
            (batch_start_ts, batch_end_ts, leaf_count, merkle_root, now),
        )
        return int(cur.lastrowid)

    def insert_leaf(self, merkle_batch_id: int, verification_log_id: int, leaf_index: int, leaf_hash: str) -> None:
        self.conn.execute(
            """
            INSERT INTO merkle_leaves(merkle_batch_id, verification_log_id, leaf_index, leaf_hash)
            VALUES (?, ?, ?, ?)
            """,
            (merkle_batch_id, verification_log_id, leaf_index, leaf_hash),
        )

    def insert_proof(self, merkle_batch_id: int, verification_log_id: int, proof_json: str) -> None:
        self.conn.execute(
            """
            INSERT INTO merkle_proofs(merkle_batch_id, verification_log_id, proof_json)
            VALUES (?, ?, ?)
            """,
            (merkle_batch_id, verification_log_id, proof_json),
        )

    def fetch_batch(self, merkle_batch_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            'SELECT * FROM merkle_batch_metadata WHERE id=?', (merkle_batch_id,)
        ).fetchone()

    def fetch_latest_pending_batch(self) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM merkle_batch_metadata WHERE status='pending_anchor' ORDER BY id ASC LIMIT 1"
        ).fetchone()

    def fetch_leaf_by_record(self, verification_log_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            'SELECT * FROM merkle_leaves WHERE verification_log_id=?', (verification_log_id,)
        ).fetchone()

    def fetch_proof(self, merkle_batch_id: int, verification_log_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            'SELECT * FROM merkle_proofs WHERE merkle_batch_id=? AND verification_log_id=?',
            (merkle_batch_id, verification_log_id),
        ).fetchone()

    def update_batch_status(self, merkle_batch_id: int, status: str) -> None:
        self.conn.execute(
            'UPDATE merkle_batch_metadata SET status=? WHERE id=?',
            (status, merkle_batch_id),
        )


class AnchorAttemptsRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def next_attempt_no(self, merkle_batch_id: int) -> int:
        row = self.conn.execute(
            'SELECT COALESCE(MAX(attempt_no), 0) AS last_no FROM anchor_attempts WHERE merkle_batch_id=?',
            (merkle_batch_id,),
        ).fetchone()
        return int(row['last_no']) + 1

    def insert_attempt(
        self,
        merkle_batch_id: int,
        attempt_no: int,
        rpc_endpoint: str,
        request_payload_json: str,
        response_payload_json: str | None,
        tx_signature: str | None,
        status: str,
        error_message: str | None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            """
            INSERT INTO anchor_attempts(
                merkle_batch_id, attempt_no, rpc_endpoint, request_payload_json,
                response_payload_json, tx_signature, status, error_message, attempted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                merkle_batch_id,
                attempt_no,
                rpc_endpoint,
                request_payload_json,
                response_payload_json,
                tx_signature,
                status,
                error_message,
                now,
            ),
        )

    def fetch_success_for_batch(self, merkle_batch_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM anchor_attempts WHERE merkle_batch_id=? AND status='success' ORDER BY id DESC LIMIT 1",
            (merkle_batch_id,),
        ).fetchone()
