import hashlib


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def compute_record_hash(canonical_packet_json: str, prev_record_hash: str | None) -> str:
    material = f"{prev_record_hash or 'GENESIS'}|{canonical_packet_json}"
    return sha256_hex(material)
