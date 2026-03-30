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
            failed_batches = conn.execute(
                "SELECT COUNT(*) AS c FROM merkle_batch_metadata WHERE status='anchor_failed'"
            ).fetchone()['c']

        return {
            'status': 'ok',
            'admitted_count': admitted,
            'rejected_count': rejected,
            'pending_anchor_batches': pending_batches,
            'anchored_batches': anchored_batches,
            'failed_anchor_batches': failed_batches,
        }

    def recent_rejections(self, limit: int = 20) -> list[dict]:
        with transaction() as conn:
            rows = conn.execute(
                """
                SELECT node_id, seq_num, reason_code, reason_detail, created_at
                FROM rejection_log
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def recent_anchor_attempts(self, limit: int = 20) -> list[dict]:
        with transaction() as conn:
            rows = conn.execute(
                """
                SELECT merkle_batch_id, attempt_no, status, tx_signature, error_message, attempted_at
                FROM anchor_attempts
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
