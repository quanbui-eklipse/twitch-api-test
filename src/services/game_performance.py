"""
Game Performance Intelligence service.

Answers questions like:
  - Which games does this streamer clip the most?
  - Which of their games generate the highest clip view counts?
  - What are the top games trending on Twitch that they haven't clipped yet?

This is the Eklipse "Game Performance Intelligence" feature — it combines
Twitch clip data with live trending game data to give streamers actionable
content strategy insights.
"""

from datetime import datetime, timezone
from collections import defaultdict
from typing import Optional

from ..twitch.api.games import GamesAPI
from ..twitch.api.clips import ClipsAPI
from ..twitch.api.streams import StreamsAPI
from ..twitch.models import (
    Clip,
    Game,
    TopGame,
    TopGameWithStreamers,
    GamePerformanceStats,
    GamePerformanceReport,
)


class GamePerformanceService:
    """
    Orchestrates game + clip API calls to produce a streamer's game
    performance report.

    Args:
        games_api: GamesAPI instance.
        clips_api: ClipsAPI instance.
    """

    def __init__(self, games_api: GamesAPI, clips_api: ClipsAPI, streams_api: StreamsAPI = None):
        self._games = games_api
        self._clips = clips_api
        self._streams = streams_api

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get_report(
        self,
        broadcaster_id: str,
        clips_per_page: int = 100,
        clip_pages: int = 3,
        top_games_count: int = 20,
        started_at: Optional[str] = None,
        ended_at: Optional[str] = None,
    ) -> GamePerformanceReport:
        """
        Build a full game performance report for a broadcaster.

        Steps:
          1. Fetch broadcaster's clips (up to clip_pages × clips_per_page).
          2. Aggregate clip stats per game_id.
          3. Enrich with game names via GamesAPI.
          4. Fetch current top games on Twitch.
          5. Identify trending games the streamer hasn't clipped.

        Args:
            broadcaster_id: Twitch user ID of the streamer.
            clips_per_page: Clips to request per API page (max 100).
            clip_pages: Number of pages to fetch (controls total clip volume).
            top_games_count: How many trending games to check (max 100).
            started_at: RFC3339 — only consider clips after this date.
            ended_at: RFC3339 — only consider clips before this date.

        Returns:
            GamePerformanceReport with per-game stats and trending game suggestions.
        """
        clips = self._clips.get_clips_by_broadcaster(
            broadcaster_id=broadcaster_id,
            first=clips_per_page,
            started_at=started_at,
            ended_at=ended_at,
            max_pages=clip_pages,
        )

        per_game_stats = self._aggregate_by_game(clips)
        enriched = self._enrich_with_game_names(per_game_stats)

        top_games = self._games.get_top_games(first=top_games_count)
        not_streamed = self._find_trending_not_streamed(top_games, per_game_stats)

        return GamePerformanceReport(
            broadcaster_id=broadcaster_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            games=sorted(enriched, key=lambda g: g.total_views, reverse=True),
            trending_games_not_streamed=not_streamed,
        )

    def get_top_game_by_views(self, broadcaster_id: str) -> Optional[GamePerformanceStats]:
        """Return the single game that has generated the most clip views."""
        report = self.get_report(broadcaster_id)
        return report.top_game_by_views()

    def get_top_games_with_streamer_count(
        self, count: int = 10
    ) -> list[TopGameWithStreamers]:
        """
        Return top Twitch games right now, each enriched with a live
        streamer count.

        Makes 1 API call for the game list + 1 per game for stream counts.
        Counts are capped at 100 per Twitch API page; games with more live
        streamers are marked with count_is_capped=True (displayed as "100+").

        Args:
            count: Number of top games to fetch (max 100).

        Returns:
            List of TopGameWithStreamers ordered by Twitch viewer rank.

        Raises:
            RuntimeError: If the service was created without a StreamsAPI.
        """
        if self._streams is None:
            raise RuntimeError(
                "StreamsAPI is required for get_top_games_with_streamer_count(). "
                "Pass streams_api= when constructing GamePerformanceService."
            )

        top_games = self._games.get_top_games(first=min(count, 100))
        result: list[TopGameWithStreamers] = []
        for game in top_games:
            n, is_capped = self._streams.get_live_stream_count_for_game(game.id)
            result.append(TopGameWithStreamers.from_top_game(game, n, is_capped))
        return result

    def get_trending_not_streamed(
        self, broadcaster_id: str, top_games_count: int = 20
    ) -> list[TopGame]:
        """
        Return currently trending games on Twitch that the streamer
        has no clips for — potential content opportunities.
        """
        report = self.get_report(
            broadcaster_id, top_games_count=top_games_count
        )
        return report.trending_games_not_streamed

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _aggregate_by_game(self, clips: list[Clip]) -> dict[str, dict]:
        """
        Group clips by game_id and compute aggregate stats.

        Returns:
            Dict keyed by game_id with keys:
              clip_count, total_views, top_clip_title, top_clip_views, clips
        """
        groups: dict[str, dict] = defaultdict(
            lambda: {
                "clip_count": 0,
                "total_views": 0,
                "top_clip_title": "",
                "top_clip_views": 0,
                "clips": [],
            }
        )

        for clip in clips:
            if not clip.game_id:
                continue
            g = groups[clip.game_id]
            g["clip_count"] += 1
            g["total_views"] += clip.view_count
            g["clips"].append(clip)
            if clip.view_count > g["top_clip_views"]:
                g["top_clip_views"] = clip.view_count
                g["top_clip_title"] = clip.title

        return dict(groups)

    def _enrich_with_game_names(
        self, per_game: dict[str, dict]
    ) -> list[GamePerformanceStats]:
        """
        Fetch game names for all game_ids and build GamePerformanceStats objects.
        """
        if not per_game:
            return []

        game_ids = list(per_game.keys())
        games = self._games.get_games_by_id(game_ids)
        name_map: dict[str, str] = {g.id: g.name for g in games}

        stats: list[GamePerformanceStats] = []
        for game_id, data in per_game.items():
            clip_count = data["clip_count"]
            total_views = data["total_views"]
            avg = round(total_views / clip_count, 1) if clip_count > 0 else 0.0

            stats.append(
                GamePerformanceStats(
                    game_id=game_id,
                    game_name=name_map.get(game_id, f"Unknown ({game_id})"),
                    clip_count=clip_count,
                    total_views=total_views,
                    avg_views_per_clip=avg,
                    top_clip_title=data["top_clip_title"],
                    top_clip_views=data["top_clip_views"],
                    clips=data["clips"],
                )
            )

        return stats

    def _find_trending_not_streamed(
        self,
        top_games: list[TopGame],
        per_game: dict[str, dict],
    ) -> list[TopGame]:
        """
        From the current top Twitch games, return those the broadcaster
        has no clips for.
        """
        streamed_ids = set(per_game.keys())
        return [g for g in top_games if g.id not in streamed_ids]
