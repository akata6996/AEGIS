from app.db.sqlite import transaction


class DashboardReadService:
    """Read-only operator queries for observability pages/API."""

    def overview(self) -> dict:
        with transaction() as conn:
            admitted = conn.execute('SELECT COUNT(*) AS c FROM verification_log').fetchone()['c']
            rejected = conn.execute('SELECT COUNT(*) AS c FROM rejection_log').fetchone()['c']
            pending_batches = conn.execute(
                "SELECT COUNT(*) AS c FROM merkle_batch_metadata WHERE status='pending_anchor'"
            ).fetchone()['c']
            anchored_batches = conn.execute(
                "SELECT COUNT(*) AS c FROM merkle_batch_metadata WHERE status='anchored'"
            ).fetchone()['c']

        return {
            'status': 'ok',
            'admitted_count': admitted,
            'rejected_count': rejected,
            'pending_anchor_batches': pending_batches,
            'anchored_batches': anchored_batches,
        }
