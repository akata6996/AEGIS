from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SensorPacket(BaseModel):
    model_config = ConfigDict(extra='forbid')

    node_id: str = Field(min_length=1, max_length=64)
    seq_num: int = Field(ge=0)
    timestamp: datetime
    sensor_value: Decimal
    sensor_type: str | None = Field(default=None, max_length=64)
    unit: str | None = Field(default=None, max_length=32)
    metadata: dict[str, Any] | None = None

    @field_validator('timestamp')
    @classmethod
    def ensure_timezone(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError('timestamp must include timezone')
        return v.astimezone(timezone.utc)


def canonicalize_packet(packet: SensorPacket) -> str:
    payload = {
        'node_id': packet.node_id,
        'seq_num': packet.seq_num,
        'timestamp': packet.timestamp.astimezone(timezone.utc).isoformat(),
        'sensor_value': str(packet.sensor_value),
        'sensor_type': packet.sensor_type,
        'unit': packet.unit,
        'metadata': packet.metadata or {},
    }
    import json

    return json.dumps(payload, sort_keys=True, separators=(',', ':'))
