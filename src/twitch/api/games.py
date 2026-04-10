"""
Twitch API — Games endpoints.

GET /helix/games/top  : Top games currently being streamed on Twitch.
GET /helix/games      : Game metadata by ID or name.
"""

from typing import Optional
from ..client import TwitchClient
from ..models import Game, TopGame


class GamesAPI:
    def __init__(self, client: TwitchClient):
        self._client = client

    def get_top_games(self, first: int = 20) -> list[TopGame]:
        """
        Fetch the most-watched games on Twitch right now, sorted by viewer count.

        Args:
            first: Number of games to return (max 100).

        Returns:
            List of TopGame objects ordered by descending viewer count.
        """
        first = min(first, 100)
        raw = self._client.get("/games/top", params={"first": first})
        return [TopGame.from_dict(g) for g in raw.get("data", [])]

    def get_games_by_id(self, game_ids: list[str]) -> list[Game]:
        """
        Fetch game metadata for one or more game IDs.

        Args:
            game_ids: Up to 100 Twitch game IDs.

        Returns:
            List of Game objects (order matches Twitch response, not input order).
        """
        if not game_ids:
            return []
        # Twitch accepts repeated `id` params; pass as list to requests.
        raw = self._client.get("/games", params={"id": game_ids})
        return [Game.from_dict(g) for g in raw.get("data", [])]

    def get_games_by_name(self, names: list[str]) -> list[Game]:
        """
        Fetch game metadata by name (case-insensitive on Twitch's end).

        Args:
            names: Up to 100 game names.

        Returns:
            List of Game objects.
        """
        if not names:
            return []
        raw = self._client.get("/games", params={"name": names})
        return [Game.from_dict(g) for g in raw.get("data", [])]
