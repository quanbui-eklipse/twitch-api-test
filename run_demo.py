"""
Demo: Game Performance Intelligence — runs with realistic mocked Twitch data.

To run against the real Twitch API instead:
    export TWITCH_CLIENT_ID=...
    export TWITCH_CLIENT_SECRET=...
    python run_demo.py --live <broadcaster_id>
"""

import sys
import responses as resp_mock

# ── Realistic mock data ────────────────────────────────────────────────────────

TOP_GAMES_RESPONSE = {
    "data": [
        {"id": "33214",  "name": "Fortnite",             "box_art_url": "", "igdb_id": "1905"},
        {"id": "516575", "name": "VALORANT",              "box_art_url": "", "igdb_id": ""},
        {"id": "21779",  "name": "League of Legends",     "box_art_url": "", "igdb_id": "115"},
        {"id": "32982",  "name": "Grand Theft Auto V",    "box_art_url": "", "igdb_id": "1020"},
        {"id": "509658", "name": "Just Chatting",         "box_art_url": "", "igdb_id": ""},
        {"id": "27471",  "name": "Minecraft",             "box_art_url": "", "igdb_id": "2069"},
        {"id": "490422", "name": "Apex Legends",          "box_art_url": "", "igdb_id": ""},
        {"id": "512710", "name": "Call of Duty: Warzone", "box_art_url": "", "igdb_id": ""},
    ],
    "pagination": {}
}

# Simulated streamer stream counts per game (count, has_cursor=is_capped)
STREAM_COUNTS = {
    "33214":  (100, True),   # Fortnite  → 100+ streamers
    "516575": (100, True),   # VALORANT  → 100+
    "21779":  (100, True),   # LoL       → 100+
    "32982":  (100, True),   # GTA V     → 100+
    "509658": (100, True),   # Just Chatting → 100+
    "27471":  (87,  False),  # Minecraft → 87
    "490422": (100, True),   # Apex      → 100+
    "512710": (95,  False),  # Warzone   → 95
}

BROADCASTER_ID = "141981764"  # simulated streamer

CLIPS_RESPONSE = {
    "data": [
        {"id": "AbCdEf1", "broadcaster_id": BROADCASTER_ID, "broadcaster_name": "ProStreamer99",
         "game_id": "33214", "title": "1000 IQ Fortnite Build",        "view_count": 142300,
         "created_at": "2024-03-01T18:00:00Z", "duration": 45.2, "thumbnail_url": "", "creator_name": "v1", "url": ""},
        {"id": "AbCdEf2", "broadcaster_id": BROADCASTER_ID, "broadcaster_name": "ProStreamer99",
         "game_id": "33214", "title": "Fortnite 20 Kill Win",           "view_count": 88500,
         "created_at": "2024-03-05T20:00:00Z", "duration": 60.0, "thumbnail_url": "", "creator_name": "v2", "url": ""},
        {"id": "AbCdEf3", "broadcaster_id": BROADCASTER_ID, "broadcaster_name": "ProStreamer99",
         "game_id": "33214", "title": "Insane Fortnite Snipe",          "view_count": 51200,
         "created_at": "2024-03-10T16:30:00Z", "duration": 30.0, "thumbnail_url": "", "creator_name": "v3", "url": ""},
        {"id": "VaLoRa1", "broadcaster_id": BROADCASTER_ID, "broadcaster_name": "ProStreamer99",
         "game_id": "516575", "title": "VALORANT 5K ACE Pistol Round",  "view_count": 214800,
         "created_at": "2024-02-14T19:00:00Z", "duration": 35.0, "thumbnail_url": "", "creator_name": "v4", "url": ""},
        {"id": "VaLoRa2", "broadcaster_id": BROADCASTER_ID, "broadcaster_name": "ProStreamer99",
         "game_id": "516575", "title": "Clutch 1v5 Valorant",           "view_count": 98700,
         "created_at": "2024-02-20T21:00:00Z", "duration": 40.0, "thumbnail_url": "", "creator_name": "v5", "url": ""},
        {"id": "GtAvV1",  "broadcaster_id": BROADCASTER_ID, "broadcaster_name": "ProStreamer99",
         "game_id": "32982", "title": "GTA RP Funniest Moment",         "view_count": 45600,
         "created_at": "2024-01-20T17:00:00Z", "duration": 58.0, "thumbnail_url": "", "creator_name": "v6", "url": ""},
        {"id": "MiNe1",   "broadcaster_id": BROADCASTER_ID, "broadcaster_name": "ProStreamer99",
         "game_id": "27471", "title": "Minecraft Speedrun WR Attempt",  "view_count": 320000,
         "created_at": "2024-01-05T15:00:00Z", "duration": 60.0, "thumbnail_url": "", "creator_name": "v7", "url": ""},
        {"id": "MiNe2",   "broadcaster_id": BROADCASTER_ID, "broadcaster_name": "ProStreamer99",
         "game_id": "27471", "title": "Found Diamond on Day 1",         "view_count": 61000,
         "created_at": "2024-01-10T14:00:00Z", "duration": 25.0, "thumbnail_url": "", "creator_name": "v8", "url": ""},
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

# ── Helpers ────────────────────────────────────────────────────────────────────

def _streams_response(count, is_capped):
    streams = [{"id": str(i), "user_id": str(i), "type": "live",
                "game_id": "x", "viewer_count": 100} for i in range(count)]
    pagination = {"cursor": "next_page"} if is_capped else {}
    return {"data": streams, "pagination": pagination}


# ── Run with mocks ─────────────────────────────────────────────────────────────

@resp_mock.activate
def run_demo():
    BASE = "https://api.twitch.tv/helix"
    resp_mock.add(resp_mock.POST, "https://id.twitch.tv/oauth2/token",
                  json=TOKEN_RESPONSE, status=200)

    # Top games — used twice (once for report, once for streamer count feature)
    resp_mock.add(resp_mock.GET, f"{BASE}/games/top", json=TOP_GAMES_RESPONSE, status=200)
    resp_mock.add(resp_mock.GET, f"{BASE}/games/top", json=TOP_GAMES_RESPONSE, status=200)

    # Clips for the broadcaster
    resp_mock.add(resp_mock.GET, f"{BASE}/clips", json=CLIPS_RESPONSE, status=200)

    # Game name enrichment
    resp_mock.add(resp_mock.GET, f"{BASE}/games", json=GAMES_ENRICHMENT_RESPONSE, status=200)

    # Stream counts per game (one response queued per game in order)
    for game in TOP_GAMES_RESPONSE["data"]:
        count, is_capped = STREAM_COUNTS[game["id"]]
        resp_mock.add(resp_mock.GET, f"{BASE}/streams",
                      json=_streams_response(count, is_capped), status=200)

    from src.twitch.auth import AppAccessToken
    from src.twitch.client import TwitchClient
    from src.twitch.api.games import GamesAPI
    from src.twitch.api.clips import ClipsAPI
    from src.twitch.api.streams import StreamsAPI
    from src.services.game_performance import GamePerformanceService

    auth = AppAccessToken(client_id="demo_cid", client_secret="demo_csec")
    client = TwitchClient(auth=auth)
    service = GamePerformanceService(
        games_api=GamesAPI(client),
        clips_api=ClipsAPI(client),
        streams_api=StreamsAPI(client),
    )

    report = service.get_report(BROADCASTER_ID, clip_pages=1, top_games_count=8)
    top_games_with_streamers = service.get_top_games_with_streamer_count(count=8)
    return report, top_games_with_streamers


def print_top_games(games):
    W = 65
    print("\n" + "═" * W)
    print("  TWITCH — TOP GAMES WITH LIVE STREAMER COUNT")
    print("═" * W)
    print(f"  {'#':<4} {'Game':<32} {'Live Streamers':>14}")
    print("─" * W)
    for i, g in enumerate(games, 1):
        print(f"  {i:<4} {g.name:<32} {g.streamer_count_display:>14}")
    print("═" * W)


def print_report(report):
    W = 90
    print("\n" + "═" * W)
    print("  EKLIPSE — GAME PERFORMANCE REPORT  (your clips)")
    print(f"  Broadcaster ID : {report.broadcaster_id}")
    print(f"  Generated at   : {report.generated_at}")
    print("═" * W)

    print(f"\n  {'#':<4} {'Game':<28} {'Clips':>6} {'Total Views':>13} {'Avg Views':>11}  Best Clip")
    print("─" * W)
    for rank, g in enumerate(report.games, 1):
        best = g.top_clip_title[:32] + ("…" if len(g.top_clip_title) > 32 else "")
        print(f"  {rank:<4} {g.game_name:<28} {g.clip_count:>6} "
              f"{g.total_views:>13,} {g.avg_views_per_clip:>11,.0f}  {best}")

    top_views = report.top_game_by_views()
    top_clips = report.top_game_by_clips()

    print("\n" + "─" * W)
    print("  INSIGHTS")
    print("─" * W)
    if top_views:
        print(f"  Highest total views  → {top_views.game_name} "
              f"({top_views.total_views:,} views across {top_views.clip_count} clips)")
    if top_clips:
        print(f"  Most clips created   → {top_clips.game_name} ({top_clips.clip_count} clips)")
    if top_views and top_clips and top_views.game_name != top_clips.game_name:
        print(f"  Virality gap         → {top_views.game_name} earns more views "
              f"with fewer clips than {top_clips.game_name}")

    if report.trending_games_not_streamed:
        print(f"\n  TRENDING — NOT YET CLIPPED BY THIS STREAMER")
        print("─" * W)
        for i, g in enumerate(report.trending_games_not_streamed, 1):
            print(f"  {i:2}. {g.name}")

    print("\n" + "═" * W + "\n")


if __name__ == "__main__":
    report, top_games = run_demo()
    print_top_games(top_games)
    print_report(report)
