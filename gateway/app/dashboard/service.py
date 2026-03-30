class DashboardReadService:
    """Read-only operator queries for observability pages/API."""

    def overview(self) -> dict:
        return {'status': 'ok'}
