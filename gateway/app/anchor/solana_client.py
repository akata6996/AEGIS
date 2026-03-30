from dataclasses import dataclass
import hashlib
import json

import httpx

from app.core.config import settings


@dataclass
class AnchorResult:
    success: bool
    tx_signature: str | None
    error: str | None
    request_payload_json: str
    response_payload_json: str | None


class SolanaDevnetAnchorClient:
    """Solana Devnet JSON-RPC client.

    Note: Production-grade anchoring requires signed transactions and dedicated RPC.
    This prototype defaults to mock mode to avoid blocking ingestion.
    """

    def anchor_merkle_root(self, merkle_root: str) -> AnchorResult:
        if settings.solana_anchor_mock_mode:
            pseudo_sig = hashlib.sha256(f'mock:{merkle_root}'.encode('utf-8')).hexdigest()[:64]
            payload = {'mode': 'mock', 'merkle_root': merkle_root}
            response = {'signature': pseudo_sig}
            return AnchorResult(
                success=True,
                tx_signature=pseudo_sig,
                error=None,
                request_payload_json=json.dumps(payload, separators=(',', ':')),
                response_payload_json=json.dumps(response, separators=(',', ':')),
            )

        payload = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'getHealth',
            'params': [],
        }
        request_payload = json.dumps(payload, separators=(',', ':'))
        try:
            response = httpx.post(settings.solana_devnet_rpc, content=request_payload, timeout=10.0)
            response_payload = response.text
            if response.is_success:
                return AnchorResult(
                    success=False,
                    tx_signature=None,
                    error='wallet signing not configured; Devnet reachability confirmed only',
                    request_payload_json=request_payload,
                    response_payload_json=response_payload,
                )
            return AnchorResult(
                success=False,
                tx_signature=None,
                error=f'RPC failure status={response.status_code}',
                request_payload_json=request_payload,
                response_payload_json=response_payload,
            )
        except Exception as exc:
            return AnchorResult(
                success=False,
                tx_signature=None,
                error=str(exc),
                request_payload_json=request_payload,
                response_payload_json=None,
            )
