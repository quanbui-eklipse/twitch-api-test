"""
Twitch API — Analytics endpoints.

GET /helix/analytics/games    : Downloadable CSV analytics report URLs for games.
GET /helix/analytics/extensions: (scaffold only, not used in Game Performance feature)

Note: Game analytics reports require a user access token with
analytics:read:games scope — they cannot be fetched with an app access token.
The URL returned by the API can be downloaded directly (it is pre-signed).
"""

from typing import Optional
from ..client import TwitchClient
from ..models import GameAnalyticsReport


class AnalyticsAPI:
    def __init__(self, client: TwitchClient):
        self._client = client

    def get_game_analytics(
        self,
        game_id: Optional[str] = None,
        report_type: str = "overview_v2",
        started_at: Optional[str] = None,
        ended_at: Optional[str] = None,
        first: int = 20,
        max_pages: int = 5,
    ) -> list[GameAnalyticsReport]:
        """
        Retrieve analytics report download URLs for one or all games.

        Each report is a CSV file covering metrics like plays, sessions,
        unique players, and average session length.

        Args:
            game_id: If provided, fetch the report for this specific game only.
                     If omitted, returns reports for all games the authenticated
                     user has extension analytics for.
            report_type: "overview_v2" (default) is the only current type.
            started_at: RFC3339 — start of the date range for the report.
            ended_at: RFC3339 — end of the date range for the report.
            first: Results per page (max 100).
            max_pages: How many pages to fetch when no game_id is given.

        Returns:
            List of GameAnalyticsReport objects containing a pre-signed download URL.

        Note:
            Requires user access token with analytics:read:games scope.
        """
        params: dict = {
            "type": report_type,
            "first": min(first, 100),
        }
        if game_id:
            params["game_id"] = game_id
        if started_at:
            params["started_at"] = started_at
        if ended_at:
            params["ended_at"] = ended_at

        # When fetching a single game, one page is sufficient.
        pages = 1 if game_id else max_pages

        reports: list[GameAnalyticsReport] = []
        for page in self._client.paginate(
            "/analytics/games", params=params, max_pages=pages
        ):
            reports.extend(GameAnalyticsReport.from_dict(r) for r in page)
        return reports
