"""
Dataclasses representing Twitch API response objects.

All fields map directly to Twitch Helix API field names where possible.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Game:
    id: str
    name: str
    box_art_url: str

    @classmethod
    def from_dict(cls, data: dict) -> "Game":
        return cls(
            id=data["id"],
            name=data["name"],
            box_art_url=data.get("box_art_url", ""),
        )


@dataclass
class TopGame:
    """A game entry from GET /helix/games/top, includes live viewer count."""

    id: str
    name: str
    box_art_url: str
    igdb_id: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "TopGame":
        return cls(
            id=data["id"],
            name=data["name"],
            box_art_url=data.get("box_art_url", ""),
            igdb_id=data.get("igdb_id", ""),
        )


@dataclass
class Clip:
    id: str
    broadcaster_id: str
    broadcaster_name: str
    game_id: str
    title: str
    view_count: int
    created_at: str
    duration: float
    thumbnail_url: str
    creator_name: str = ""
    url: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "Clip":
        return cls(
            id=data["id"],
            broadcaster_id=data.get("broadcaster_id", ""),
            broadcaster_name=data.get("broadcaster_name", ""),
            game_id=data.get("game_id", ""),
            title=data.get("title", ""),
            view_count=data.get("view_count", 0),
            created_at=data.get("created_at", ""),
            duration=data.get("duration", 0.0),
            thumbnail_url=data.get("thumbnail_url", ""),
            creator_name=data.get("creator_name", ""),
            url=data.get("url", ""),
        )


@dataclass
class DateRange:
    started_at: str
    ended_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "DateRange":
        return cls(
            started_at=data.get("started_at", ""),
            ended_at=data.get("ended_at", ""),
        )


@dataclass
class GameAnalyticsReport:
    """A downloadable analytics CSV report for a specific game."""

    game_id: str
    url: str
    type: str
    date_range: DateRange

    @classmethod
    def from_dict(cls, data: dict) -> "GameAnalyticsReport":
        return cls(
            game_id=data.get("game_id", ""),
            url=data.get("URL", ""),
            type=data.get("type", ""),
            date_range=DateRange.from_dict(data.get("date_range", {})),
        )


@dataclass
class GamePerformanceStats:
    """Aggregated clip performance for a single game on a broadcaster's channel."""

    game_id: str
    game_name: str
    clip_count: int
    total_views: int
    avg_views_per_clip: float
    top_clip_title: str
    top_clip_views: int
    clips: list = field(default_factory=list)

    @property
    def box_art_url(self) -> str:
        if self.clips and hasattr(self.clips[0], "thumbnail_url"):
            return ""
        return ""


@dataclass
class GamePerformanceReport:
    """Full report comparing game performance for a broadcaster."""

    broadcaster_id: str
    generated_at: str
    games: list[GamePerformanceStats] = field(default_factory=list)
    trending_games_not_streamed: list[TopGame] = field(default_factory=list)

    def top_game_by_views(self) -> Optional[GamePerformanceStats]:
        if not self.games:
            return None
        return max(self.games, key=lambda g: g.total_views)

    def top_game_by_clips(self) -> Optional[GamePerformanceStats]:
        if not self.games:
            return None
        return max(self.games, key=lambda g: g.clip_count)
