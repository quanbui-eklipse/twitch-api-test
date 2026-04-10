"""
Fetch and display the top games on Twitch right now.

Usage:
    cp .env.example .env   # fill in TWITCH_CLIENT_ID + TWITCH_CLIENT_SECRET
    pip install -r requirements.txt
    python fetch_top_games.py [--count N] [--with-streamers]

Examples:
    python fetch_top_games.py
    python fetch_top_games.py --count 50
    python fetch_top_games.py --count 10 --with-streamers
"""

import argparse
from src.twitch.auth import AppAccessToken
from src.twitch.client import TwitchClient
from src.twitch.api.games import GamesAPI
from src.twitch.api.streams import StreamsAPI
from src.twitch.models import TopGameWithStreamers


def print_top_games(games):
    W = 65
    print("\n" + "═" * W)
    print("  TWITCH — TOP GAMES RIGHT NOW")
    print("═" * W)
    print(f"  {'#':<4} {'Game':<35} {'Game ID'}")
    print("─" * W)
    for i, g in enumerate(games, 1):
        print(f"  {i:<4} {g.name:<35} {g.id}")
    print("═" * W)
    print(f"\n  {len(games)} games returned.\n")


def print_top_games_with_streamers(games):
    W = 65
    print("\n" + "═" * W)
    print("  TWITCH — TOP GAMES WITH LIVE STREAMER COUNT")
    print("═" * W)
    print(f"  {'#':<4} {'Game':<32} {'Live Streamers':>14}")
    print("─" * W)
    for i, g in enumerate(games, 1):
        print(f"  {i:<4} {g.name:<32} {g.streamer_count_display:>14}")
    print("═" * W)
    print(f"\n  {len(games)} games returned.\n")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch the top games on Twitch right now."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=20,
        help="Number of top games to return (default: 20, max: 100).",
    )
    parser.add_argument(
        "--with-streamers",
        action="store_true",
        help="Enrich results with live streamer counts (makes N+1 API calls).",
    )
    args = parser.parse_args()

    count = min(max(args.count, 1), 100)

    auth = AppAccessToken()
    client = TwitchClient(auth=auth)
    games_api = GamesAPI(client)

    if args.with_streamers:
        streams_api = StreamsAPI(client)
        print(f"\nFetching top {count} games with live streamer counts...")
        raw_games = games_api.get_top_games(first=count)
        games = []
        for game in raw_games:
            n, is_capped = streams_api.get_live_stream_count_for_game(game.id)
            games.append(TopGameWithStreamers.from_top_game(game, n, is_capped))
        print_top_games_with_streamers(games)
    else:
        print(f"\nFetching top {count} games from Twitch API...")
        games = games_api.get_top_games(first=count)
        print_top_games(games)


if __name__ == "__main__":
    main()
