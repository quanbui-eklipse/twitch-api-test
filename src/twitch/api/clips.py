"""
Twitch API — Clips endpoints.

GET /helix/clips : Fetch clips by broadcaster, game, or specific clip IDs.
"""

from typing import Optional
from ..client import TwitchClient
from ..models import Clip


class ClipsAPI:
    def __init__(self, client: TwitchClient):
        self._client = client

    def get_clips_by_broadcaster(
        self,
        broadcaster_id: str,
        first: int = 20,
        started_at: Optional[str] = None,
        ended_at: Optional[str] = None,
        max_pages: int = 1,
    ) -> list[Clip]:
        """
        Fetch clips from a specific broadcaster's channel.

        Args:
            broadcaster_id: Twitch user ID of the broadcaster.
            first: Results per page (max 100).
            started_at: RFC3339 timestamp — only clips after this time.
            ended_at: RFC3339 timestamp — only clips before this time.
            max_pages: How many pages of results to fetch.

        Returns:
            List of Clip objects sorted by view_count descending (Twitch default).
        """
        params: dict = {
            "broadcaster_id": broadcaster_id,
            "first": min(first, 100),
        }
        if started_at:
            params["started_at"] = started_at
        if ended_at:
            params["ended_at"] = ended_at

        clips: list[Clip] = []
        for page in self._client.paginate("/clips", params=params, max_pages=max_pages):
            clips.extend(Clip.from_dict(c) for c in page)
        return clips

    def get_clips_by_game(
        self,
        game_id: str,
        first: int = 20,
        started_at: Optional[str] = None,
        ended_at: Optional[str] = None,
        max_pages: int = 1,
    ) -> list[Clip]:
        """
        Fetch the most-viewed clips for a specific game across all channels.

        Args:
            game_id: Twitch game ID.
            first: Results per page (max 100).
            started_at: RFC3339 filter — clips created after this time.
            ended_at: RFC3339 filter — clips created before this time.
            max_pages: How many pages to fetch.

        Returns:
            List of Clip objects.
        """
        params: dict = {
            "game_id": game_id,
            "first": min(first, 100),
        }
        if started_at:
            params["started_at"] = started_at
        if ended_at:
            params["ended_at"] = ended_at

        clips: list[Clip] = []
        for page in self._client.paginate("/clips", params=params, max_pages=max_pages):
            clips.extend(Clip.from_dict(c) for c in page)
        return clips

    def get_clips_by_ids(self, clip_ids: list[str]) -> list[Clip]:
        """
        Fetch specific clips by their IDs.

        Args:
            clip_ids: Up to 100 clip IDs.

        Returns:
            List of Clip objects.
        """
        if not clip_ids:
            return []
        raw = self._client.get("/clips", params={"id": clip_ids})
        return [Clip.from_dict(c) for c in raw.get("data", [])]
