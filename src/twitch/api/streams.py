"""
Twitch API — Streams endpoint.

GET /helix/streams : Live stream data, filterable by game_id.
Used here to count how many streamers are live for a given game.
"""

from ..client import TwitchClient


class StreamsAPI:
    def __init__(self, client: TwitchClient):
        self._client = client

    def get_live_stream_count_for_game(self, game_id: str) -> tuple[int, bool]:
        """
        Count the number of live streamers for a game with a single API call.

        Twitch caps results at 100 per page. If the response includes a
        pagination cursor there are more streamers than returned.

        Args:
            game_id: Twitch game ID.

        Returns:
            (count, is_capped) where is_capped=True means the real count
            exceeds 100 and the display value should be shown as "100+".
        """
        raw = self._client.get(
            "/streams",
            params={"game_id": game_id, "first": 100, "type": "live"},
        )
        data = raw.get("data", [])
        is_capped = bool(raw.get("pagination", {}).get("cursor"))
        return len(data), is_capped
