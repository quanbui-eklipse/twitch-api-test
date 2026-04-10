"""Tests for GamePerformanceService."""

import pytest
from unittest.mock import MagicMock, patch

from src.twitch.models import Clip, Game, TopGame
from src.twitch.api.games import GamesAPI
from src.twitch.api.clips import ClipsAPI
from src.services.game_performance import GamePerformanceService


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def make_clip(clip_id, game_id, view_count, title="Test Clip", broadcaster_id="999"):
    return Clip(
        id=clip_id,
        broadcaster_id=broadcaster_id,
        broadcaster_name="TestStreamer",
        game_id=game_id,
        title=title,
        view_count=view_count,
        created_at="2024-01-01T00:00:00Z",
        duration=30.0,
        thumbnail_url="",
    )


def make_service(clips=None, games=None, top_games=None):
    games_api = MagicMock(spec=GamesAPI)
    clips_api = MagicMock(spec=ClipsAPI)

    clips_api.get_clips_by_broadcaster.return_value = clips or []
    games_api.get_games_by_id.return_value = games or []
    games_api.get_top_games.return_value = top_games or []

    return GamePerformanceService(games_api=games_api, clips_api=clips_api)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_report_empty_clips():
    svc = make_service(clips=[], games=[], top_games=[])
    report = svc.get_report("999")
    assert report.broadcaster_id == "999"
    assert report.games == []
    assert report.trending_games_not_streamed == []


def test_report_aggregates_clips_by_game():
    clips = [
        make_clip("c1", "33214", 5000, "Fortnite win"),
        make_clip("c2", "33214", 3000, "Nice shot"),
        make_clip("c3", "516575", 8000, "VALORANT ace"),
    ]
    games = [
        Game(id="33214", name="Fortnite", box_art_url=""),
        Game(id="516575", name="VALORANT", box_art_url=""),
    ]
    svc = make_service(clips=clips, games=games, top_games=[])
    report = svc.get_report("999")

    assert len(report.games) == 2
    # Sorted by total_views descending: VALORANT (8000) > Fortnite (8000)
    # Fortnite: 5000+3000 = 8000, VALORANT: 8000 — tie, order may vary
    totals = {g.game_name: g.total_views for g in report.games}
    assert totals["Fortnite"] == 8000
    assert totals["VALORANT"] == 8000


def test_report_avg_views_calculation():
    clips = [
        make_clip("c1", "33214", 1000),
        make_clip("c2", "33214", 3000),
    ]
    games = [Game(id="33214", name="Fortnite", box_art_url="")]
    svc = make_service(clips=clips, games=games, top_games=[])
    report = svc.get_report("999")

    fn = report.games[0]
    assert fn.clip_count == 2
    assert fn.total_views == 4000
    assert fn.avg_views_per_clip == 2000.0


def test_report_top_clip_identified():
    clips = [
        make_clip("c1", "33214", 100, "Low clip"),
        make_clip("c2", "33214", 9999, "Viral clip"),
        make_clip("c3", "33214", 50, "Tiny clip"),
    ]
    games = [Game(id="33214", name="Fortnite", box_art_url="")]
    svc = make_service(clips=clips, games=games, top_games=[])
    report = svc.get_report("999")

    fn = report.games[0]
    assert fn.top_clip_title == "Viral clip"
    assert fn.top_clip_views == 9999


def test_trending_not_streamed_excludes_played_games():
    clips = [make_clip("c1", "33214", 100)]  # streamer has Fortnite clips
    games = [Game(id="33214", name="Fortnite", box_art_url="")]
    top_games = [
        TopGame(id="33214", name="Fortnite", box_art_url=""),    # already streamed
        TopGame(id="516575", name="VALORANT", box_art_url=""),   # not streamed
        TopGame(id="21779", name="League of Legends", box_art_url=""),  # not streamed
    ]
    svc = make_service(clips=clips, games=games, top_games=top_games)
    report = svc.get_report("999")

    not_streamed_names = [g.name for g in report.trending_games_not_streamed]
    assert "Fortnite" not in not_streamed_names
    assert "VALORANT" in not_streamed_names
    assert "League of Legends" in not_streamed_names


def test_get_top_game_by_views():
    clips = [
        make_clip("c1", "33214", 500),
        make_clip("c2", "516575", 9000),
    ]
    games = [
        Game(id="33214", name="Fortnite", box_art_url=""),
        Game(id="516575", name="VALORANT", box_art_url=""),
    ]
    svc = make_service(clips=clips, games=games, top_games=[])
    top = svc.get_top_game_by_views("999")
    assert top.game_name == "VALORANT"


def test_clips_with_no_game_id_are_skipped():
    clips = [
        make_clip("c1", "", 5000, "No game"),
        make_clip("c2", "33214", 1000, "Fortnite"),
    ]
    games = [Game(id="33214", name="Fortnite", box_art_url="")]
    svc = make_service(clips=clips, games=games, top_games=[])
    report = svc.get_report("999")
    assert len(report.games) == 1
    assert report.games[0].game_name == "Fortnite"


def test_get_trending_not_streamed_delegates_to_report():
    clips = []
    top_games = [TopGame(id="999", name="NewGame", box_art_url="")]
    svc = make_service(clips=clips, games=[], top_games=top_games)
    result = svc.get_trending_not_streamed("999")
    assert result[0].name == "NewGame"
