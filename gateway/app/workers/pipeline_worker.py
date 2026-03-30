from __future__ import annotations

import logging
import threading
import time

from app.anchor.service import AnchorOrchestrator
from app.core.config import settings
from app.merkle.service import MerkleAggregationService

logger = logging.getLogger(__name__)


class PipelineWorker:
    """Periodic non-gating worker for Merkle batching and anchoring."""

    def __init__(
        self,
        merkle_service: MerkleAggregationService | None = None,
        anchor_orchestrator: AnchorOrchestrator | None = None,
        poll_seconds: int | None = None,
    ) -> None:
        self.merkle_service = merkle_service or MerkleAggregationService()
        self.anchor_orchestrator = anchor_orchestrator or AnchorOrchestrator()
        self.poll_seconds = poll_seconds or settings.pipeline_worker_poll_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name='aegis-pipeline-worker', daemon=True)
        self._thread.start()
        logger.info('pipeline worker started')

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        logger.info('pipeline worker stopped')

    def tick_once(self) -> dict:
        batch = self.merkle_service.run_batch()
        anchor = self.anchor_orchestrator.anchor_next_pending_batch_dict()
        return {
            'batch_created': batch is not None,
            'batch_id': batch.batch_id if batch else None,
            'anchor_attempted': anchor.get('attempted', False),
            'anchor_success': anchor.get('success', False),
            'anchor_error': anchor.get('error'),
        }

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                result = self.tick_once()
                logger.debug('pipeline tick result=%s', result)
            except Exception as exc:
                logger.exception('pipeline worker tick failed: %s', exc)
            time.sleep(self.poll_seconds)
