"""
Demo: Game Performance Intelligence — runs with realistic mocked Twitch data.

To run against the real Twitch API instead:
    export TWITCH_CLIENT_ID=...
    export TWITCH_CLIENT_SECRET=...
    python run_demo.py --live <broadcaster_id>
"""

import sys
import responses as resp_mock
import requests
import json

# ── Realistic mock data ────────────────────────────────────────────────────────

TOP_GAMES_RESPONSE = {
    "data": [
        {"id": "33214",  "name": "Fortnite",             "box_art_url": "https://static-cdn.jtvnw.net/ttv-boxart/33214-{width}x{height}.jpg", "igdb_id": "1905"},
        {"id": "516575", "name": "VALORANT",              "box_art_url": "https://static-cdn.jtvnw.net/ttv-boxart/516575-{width}x{height}.jpg", "igdb_id": ""},
        {"id": "21779",  "name": "League of Legends",     "box_art_url": "https://static-cdn.jtvnw.net/ttv-boxart/21779-{width}x{height}.jpg",  "igdb_id": "115"},
        {"id": "32982",  "name": "Grand Theft Auto V",    "box_art_url": "https://static-cdn.jtvnw.net/ttv-boxart/32982-{width}x{height}.jpg",  "igdb_id": "1020"},
        {"id": "509658", "name": "Just Chatting",         "box_art_url": "https://static-cdn.jtvnw.net/ttv-boxart/509658-{width}x{height}.jpg", "igdb_id": ""},
        {"id": "27471",  "name": "Minecraft",             "box_art_url": "https://static-cdn.jtvnw.net/ttv-boxart/27471-{width}x{height}.jpg",  "igdb_id": "2069"},
        {"id": "490422", "name": "Apex Legends",          "box_art_url": "https://static-cdn.jtvnw.net/ttv-boxart/490422-{width}x{height}.jpg", "igdb_id": ""},
        {"id": "512710", "name": "Call of Duty: Warzone", "box_art_url": "https://static-cdn.jtvnw.net/ttv-boxart/512710-{width}x{height}.jpg", "igdb_id": ""},
    ],
    "pagination": {}
}

BROADCASTER_ID = "141981764"  # simulated streamer

CLIPS_RESPONSE_PAGE1 = {
    "data": [
        # Fortnite clips (streamer's best game)
        {"id": "AbCdEf1", "broadcaster_id": BROADCASTER_ID, "broadcaster_name": "ProStreamer99",
         "game_id": "33214", "title": "1000 IQ Fortnite Build",   "view_count": 142300,
         "created_at": "2024-03-01T18:00:00Z", "duration": 45.2, "thumbnail_url": "", "creator_name": "viewer1", "url": ""},
        {"id": "AbCdEf2", "broadcaster_id": BROADCASTER_ID, "broadcaster_name": "ProStreamer99",
         "game_id": "33214", "title": "Fortnite 20 Kill Win",     "view_count": 88500,
         "created_at": "2024-03-05T20:00:00Z", "duration": 60.0, "thumbnail_url": "", "creator_name": "viewer2", "url": ""},
        {"id": "AbCdEf3", "broadcaster_id": BROADCASTER_ID, "broadcaster_name": "ProStreamer99",
         "game_id": "33214", "title": "Insane Fortnite Snipe",    "view_count": 51200,
         "created_at": "2024-03-10T16:30:00Z", "duration": 30.0, "thumbnail_url": "", "creator_name": "viewer3", "url": ""},
        {"id": "AbCdEf4", "broadcaster_id": BROADCASTER_ID, "broadcaster_name": "ProStreamer99",
         "game_id": "33214", "title": "Fortnite Lucky Escape",    "view_count": 29800,
         "created_at": "2024-03-12T22:00:00Z", "duration": 55.0, "thumbnail_url": "", "creator_name": "viewer4", "url": ""},
        # VALORANT clips
        {"id": "VaLoRa1", "broadcaster_id": BROADCASTER_ID, "broadcaster_name": "ProStreamer99",
         "game_id": "516575", "title": "VALORANT 5K ACE Pistol",  "view_count": 214800,
         "created_at": "2024-02-14T19:00:00Z", "duration": 35.0, "thumbnail_url": "", "creator_name": "viewer5", "url": ""},
        {"id": "VaLoRa2", "broadcaster_id": BROADCASTER_ID, "broadcaster_name": "ProStreamer99",
         "game_id": "516575", "title": "Clutch 1v5 Valorant",     "view_count": 98700,
         "created_at": "2024-02-20T21:00:00Z", "duration": 40.0, "thumbnail_url": "", "creator_name": "viewer6", "url": ""},
        # GTA V clips
        {"id": "GtAvV1",  "broadcaster_id": BROADCASTER_ID, "broadcaster_name": "ProStreamer99",
         "game_id": "32982", "title": "GTA RP Funniest Moment",   "view_count": 45600,
         "created_at": "2024-01-20T17:00:00Z", "duration": 58.0, "thumbnail_url": "", "creator_name": "viewer7", "url": ""},
        # Minecraft clips
        {"id": "MiNe1",   "broadcaster_id": BROADCASTER_ID, "broadcaster_name": "ProStreamer99",
         "game_id": "27471", "title": "Minecraft Speedrun WR Attempt", "view_count": 320000,
         "created_at": "2024-01-05T15:00:00Z", "duration": 60.0, "thumbnail_url": "", "creator_name": "viewer8", "url": ""},
        {"id": "MiNe2",   "broadcaster_id": BROADCASTER_ID, "broadcaster_name": "ProStreamer99",
         "game_id": "27471", "title": "Found Diamond on Day 1",   "view_count": 61000,
         "created_at": "2024-01-10T14:00:00Z", "duration": 25.0, "thumbnail_url": "", "creator_name": "viewer9", "url": ""},
    ],
    "pagination": {}
}

GAMES_ENRICHMENT_RESPONSE = {
    "data": [
        {"id": "33214",  "name": "Fortnite",          "box_art_url": ""},
        {"id": "516575", "name": "VALORANT",           "box_art_url": ""},
        {"id": "32982",  "name": "Grand Theft Auto V", "box_art_url": ""},
        {"id": "27471",  "name": "Minecraft",          "box_art_url": ""},
    ]
}

TOKEN_RESPONSE = {"access_token": "mock_token_xyz", "expires_in": 3600}

# ── Run with mocks ─────────────────────────────────────────────────────────────

@resp_mock.activate
def run_demo():
    # Auth
    resp_mock.add(resp_mock.POST, "https://id.twitch.tv/oauth2/token",
                  json=TOKEN_RESPONSE, status=200)
    # Top games
    resp_mock.add(resp_mock.GET, "https://api.twitch.tv/helix/games/top",
                  json=TOP_GAMES_RESPONSE, status=200)
    # Clips (broadcaster)
    resp_mock.add(resp_mock.GET, "https://api.twitch.tv/helix/clips",
                  json=CLIPS_RESPONSE_PAGE1, status=200)
    # Game name enrichment
    resp_mock.add(resp_mock.GET, "https://api.twitch.tv/helix/games",
                  json=GAMES_ENRICHMENT_RESPONSE, status=200)

    from src.twitch.auth import AppAccessToken
    from src.twitch.client import TwitchClient
    from src.twitch.api.games import GamesAPI
    from src.twitch.api.clips import ClipsAPI
    from src.services.game_performance import GamePerformanceService

    auth = AppAccessToken(client_id="demo_cid", client_secret="demo_csec")
    client = TwitchClient(auth=auth)
    service = GamePerformanceService(
        games_api=GamesAPI(client),
        clips_api=ClipsAPI(client),
    )

    report = service.get_report(BROADCASTER_ID, clip_pages=1, top_games_count=8)
    return report


def print_report(report):
    W = 90
    print("\n" + "═" * W)
    print(f"  EKLIPSE — GAME PERFORMANCE REPORT")
    print(f"  Broadcaster ID : {report.broadcaster_id}")
    print(f"  Generated at   : {report.generated_at}")
    print("═" * W)

    print(f"\n{'#':<4} {'Game':<28} {'Clips':>6} {'Total Views':>13} {'Avg Views':>11}  Best Clip")
    print("─" * W)
    for rank, g in enumerate(report.games, 1):
        best = g.top_clip_title[:32] + ("…" if len(g.top_clip_title) > 32 else "")
        print(
            f"{rank:<4} {g.game_name:<28} {g.clip_count:>6} "
            f"{g.total_views:>13,} {g.avg_views_per_clip:>11,.0f}  {best}"
        )

    top_views = report.top_game_by_views()
    top_clips = report.top_game_by_clips()

    print("\n" + "─" * W)
    print("  INSIGHTS")
    print("─" * W)
    if top_views:
        print(f"  Highest total views  → {top_views.game_name} ({top_views.total_views:,} views across {top_views.clip_count} clips)")
    if top_clips:
        print(f"  Most clips created   → {top_clips.game_name} ({top_clips.clip_count} clips)")
    if top_views and top_clips and top_views.game_name != top_clips.game_name:
        print(f"  Virality gap         → {top_views.game_name} earns more views with fewer clips than {top_clips.game_name}")

    if report.trending_games_not_streamed:
        print(f"\n  TRENDING ON TWITCH — NOT YET CLIPPED BY THIS STREAMER")
        print("─" * W)
        for i, g in enumerate(report.trending_games_not_streamed, 1):
            print(f"  {i:2}. {g.name}")

    print("\n" + "═" * W + "\n")


if __name__ == "__main__":
    report = run_demo()
    print_report(report)
