import json
from datetime import timezone

import paho.mqtt.client as mqtt

from app.core.config import settings
from app.core.time import utc_now
from app.db.repositories import (
    EnrollmentRepository,
    RejectionLogRepository,
    SessionRepository,
    VerificationLogRepository,
)
from app.db.sqlite import transaction
from app.enforcement.engine import EnforcementEngine
from app.ingestion.contracts import SensorPacket


class MqttIngestionService:
    def __init__(self) -> None:
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if settings.mqtt_username:
            self.client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def start(self) -> None:
        self.client.connect(settings.mqtt_host, settings.mqtt_port, 60)
        self.client.loop_start()

    def stop(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        client.subscribe(settings.mqtt_topic_template, qos=settings.mqtt_qos)

    def _on_message(self, client, userdata, msg):
        gateway_received_at = utc_now().astimezone(timezone.utc)
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            packet = SensorPacket(**payload)
        except Exception:
            return

        with transaction() as conn:
            engine = EnforcementEngine(
                enrollment_repo=EnrollmentRepository(conn),
                session_repo=SessionRepository(conn),
                verification_repo=VerificationLogRepository(conn),
                rejection_repo=RejectionLogRepository(conn),
            )
            engine.process_packet(packet, gateway_received_at=gateway_received_at)
