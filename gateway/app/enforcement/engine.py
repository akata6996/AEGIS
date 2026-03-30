from dataclasses import dataclass
from datetime import datetime, timezone
import json

from app.core.config import settings
from app.db.repositories import (
    EnrollmentRepository,
    RejectionLogRepository,
    SessionRepository,
    VerificationLogRepository,
)
from app.ingestion.contracts import SensorPacket, canonicalize_packet
from app.logging.hash_chain import compute_record_hash


@dataclass
class EnforcementDecision:
    admitted: bool
    reason_code: str
    reason_detail: str
    anomaly_flags: list[str]


class EnforcementEngine:
    def __init__(
        self,
        enrollment_repo: EnrollmentRepository,
        session_repo: SessionRepository,
        verification_repo: VerificationLogRepository,
        rejection_repo: RejectionLogRepository,
    ) -> None:
        self.enrollment_repo = enrollment_repo
        self.session_repo = session_repo
        self.verification_repo = verification_repo
        self.rejection_repo = rejection_repo

    def process_packet(self, packet: SensorPacket, gateway_received_at: datetime) -> EnforcementDecision:
        canonical_packet = canonicalize_packet(packet)

        enrollment = self.enrollment_repo.get(packet.node_id)
        if enrollment is None or not enrollment.is_active:
            self.rejection_repo.insert_rejection(
                node_id=packet.node_id,
                seq_num=packet.seq_num,
                packet_timestamp=packet.timestamp.isoformat(),
                gateway_received_at=gateway_received_at.isoformat(),
                reason_code='ENROLLMENT_FAILED',
                reason_detail='node is not enrolled or inactive',
                packet_canonical_json=canonical_packet,
            )
            return EnforcementDecision(False, 'ENROLLMENT_FAILED', 'Node not enrolled', [])

        delay_ms = (gateway_received_at - packet.timestamp.astimezone(timezone.utc)).total_seconds() * 1000
        if delay_ms > settings.max_ingest_delay_ms or delay_ms < -settings.max_clock_skew_ms:
            self.rejection_repo.insert_rejection(
                node_id=packet.node_id,
                seq_num=packet.seq_num,
                packet_timestamp=packet.timestamp.isoformat(),
                gateway_received_at=gateway_received_at.isoformat(),
                reason_code='BOUNDED_DELAY_FAILED',
                reason_detail=f'delay_ms={delay_ms:.2f}',
                packet_canonical_json=canonical_packet,
            )
            return EnforcementDecision(False, 'BOUNDED_DELAY_FAILED', 'Packet outside bounded delay', [])

        session = self.session_repo.get(packet.node_id)
        if session is None:
            self.session_repo.initialize(packet.node_id, expected_next_seq=packet.seq_num + 1)
        else:
            if session.session_status == 'requires_reset':
                self.rejection_repo.insert_rejection(
                    node_id=packet.node_id,
                    seq_num=packet.seq_num,
                    packet_timestamp=packet.timestamp.isoformat(),
                    gateway_received_at=gateway_received_at.isoformat(),
                    reason_code='SESSION_REQUIRES_RESET',
                    reason_detail='operator reset required',
                    packet_canonical_json=canonical_packet,
                )
                return EnforcementDecision(False, 'SESSION_REQUIRES_RESET', 'Explicit reset required', [])

            if packet.seq_num != session.expected_next_seq:
                self.rejection_repo.insert_rejection(
                    node_id=packet.node_id,
                    seq_num=packet.seq_num,
                    packet_timestamp=packet.timestamp.isoformat(),
                    gateway_received_at=gateway_received_at.isoformat(),
                    reason_code='SEQUENCE_CONTINUITY_FAILED',
                    reason_detail=(
                        f'expected seq {session.expected_next_seq}, got {packet.seq_num}'
                    ),
                    packet_canonical_json=canonical_packet,
                )
                return EnforcementDecision(False, 'SEQUENCE_CONTINUITY_FAILED', 'Sequence mismatch', [])

            self.session_repo.update_expected_seq(packet.node_id, packet.seq_num + 1)

        anomaly_flags = self._compute_anomaly_flags(packet)

        prev_hash = self.verification_repo.fetch_latest_record_hash()
        record_hash = compute_record_hash(canonical_packet, prev_hash)
        self.verification_repo.insert_admitted(
            node_id=packet.node_id,
            seq_num=packet.seq_num,
            packet_timestamp=packet.timestamp.isoformat(),
            gateway_received_at=gateway_received_at.isoformat(),
            sensor_value=float(packet.sensor_value),
            sensor_type=packet.sensor_type,
            unit=packet.unit,
            anomaly_flags_json=json.dumps(anomaly_flags, separators=(',', ':')),
            packet_canonical_json=canonical_packet,
            prev_record_hash=prev_hash,
            record_hash=record_hash,
        )

        return EnforcementDecision(True, 'ADMITTED', 'packet admitted', anomaly_flags)

    @staticmethod
    def _compute_anomaly_flags(packet: SensorPacket) -> list[str]:
        flags: list[str] = []
        value = float(packet.sensor_value)
        if value < -50 or value > 150:
            flags.append('SENSOR_RANGE_OUTLIER')
        return flags
