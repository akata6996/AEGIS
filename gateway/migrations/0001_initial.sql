PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS enrollment_registry (
    node_id TEXT PRIMARY KEY,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
    enrolled_at TEXT NOT NULL,
    revoked_at TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS session_state (
    node_id TEXT PRIMARY KEY,
    expected_next_seq INTEGER NOT NULL CHECK (expected_next_seq >= 0),
    last_seen_packet_ts TEXT,
    last_seen_gateway_ts TEXT,
    last_seen_mqtt_message_id INTEGER,
    session_status TEXT NOT NULL CHECK (session_status IN ('healthy','interrupted','requires_reset')),
    updated_at TEXT NOT NULL,
    FOREIGN KEY(node_id) REFERENCES enrollment_registry(node_id)
);

CREATE TABLE IF NOT EXISTS verification_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT NOT NULL,
    seq_num INTEGER NOT NULL CHECK (seq_num >= 0),
    packet_timestamp TEXT NOT NULL,
    gateway_received_at TEXT NOT NULL,
    sensor_value REAL NOT NULL,
    sensor_type TEXT,
    unit TEXT,
    anomaly_flags_json TEXT NOT NULL,
    packet_canonical_json TEXT NOT NULL,
    prev_record_hash TEXT,
    record_hash TEXT NOT NULL UNIQUE,
    merkle_batch_id INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY(node_id) REFERENCES enrollment_registry(node_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_verification_node_seq ON verification_log(node_id, seq_num);
CREATE INDEX IF NOT EXISTS idx_verification_created_at ON verification_log(created_at);

CREATE TABLE IF NOT EXISTS rejection_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT NOT NULL,
    seq_num INTEGER,
    packet_timestamp TEXT,
    gateway_received_at TEXT NOT NULL,
    reason_code TEXT NOT NULL,
    reason_detail TEXT NOT NULL,
    packet_canonical_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rejection_node_time ON rejection_log(node_id, created_at);

CREATE TABLE IF NOT EXISTS merkle_batch_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_start_ts TEXT NOT NULL,
    batch_end_ts TEXT NOT NULL,
    leaf_count INTEGER NOT NULL CHECK (leaf_count > 0),
    merkle_root TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK (status IN ('pending_anchor','anchored','anchor_failed')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS merkle_leaves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    merkle_batch_id INTEGER NOT NULL,
    verification_log_id INTEGER NOT NULL,
    leaf_index INTEGER NOT NULL CHECK (leaf_index >= 0),
    leaf_hash TEXT NOT NULL,
    FOREIGN KEY(merkle_batch_id) REFERENCES merkle_batch_metadata(id),
    FOREIGN KEY(verification_log_id) REFERENCES verification_log(id),
    UNIQUE(merkle_batch_id, leaf_index),
    UNIQUE(merkle_batch_id, verification_log_id)
);

CREATE TABLE IF NOT EXISTS merkle_proofs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    merkle_batch_id INTEGER NOT NULL,
    verification_log_id INTEGER NOT NULL,
    proof_json TEXT NOT NULL,
    FOREIGN KEY(merkle_batch_id) REFERENCES merkle_batch_metadata(id),
    FOREIGN KEY(verification_log_id) REFERENCES verification_log(id),
    UNIQUE(merkle_batch_id, verification_log_id)
);

CREATE TABLE IF NOT EXISTS anchor_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    merkle_batch_id INTEGER NOT NULL,
    attempt_no INTEGER NOT NULL CHECK (attempt_no > 0),
    rpc_endpoint TEXT NOT NULL,
    request_payload_json TEXT NOT NULL,
    response_payload_json TEXT,
    tx_signature TEXT,
    status TEXT NOT NULL CHECK (status IN ('success','failed')),
    error_message TEXT,
    attempted_at TEXT NOT NULL,
    FOREIGN KEY(merkle_batch_id) REFERENCES merkle_batch_metadata(id),
    UNIQUE(merkle_batch_id, attempt_no)
);

CREATE TABLE IF NOT EXISTS operator_reset_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT NOT NULL,
    previous_expected_seq INTEGER NOT NULL,
    new_expected_seq INTEGER NOT NULL,
    reason TEXT NOT NULL,
    operator_id TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(node_id) REFERENCES enrollment_registry(node_id)
);
