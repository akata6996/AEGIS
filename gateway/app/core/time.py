from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_iso8601(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).isoformat()
