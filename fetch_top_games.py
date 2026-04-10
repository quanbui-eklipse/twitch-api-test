"""
Fetch and display the top games on Twitch right now.

Usage:
    cp .env.example .env   # fill in TWITCH_CLIENT_ID + TWITCH_CLIENT_SECRET
    pip install -r requirements.txt
    python fetch_top_games.py [--count N] [--with-streamers] [--list-streamers [N]]

Examples:
    python fetch_top_games.py
    python fetch_top_games.py --count 50
    python fetch_top_games.py --count 10 --with-streamers
    python fetch_top_games.py --count 5 --list-streamers
    python fetch_top_games.py --count 5 --list-streamers 5
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


def print_streamers_per_game(games, streams_api, streamers_per_game):
    W = 75
    for i, game in enumerate(games, 1):
        streams = streams_api.get_streams_for_game(game.id, first=streamers_per_game)
        print("\n" + "═" * W)
        print(f"  #{i}  {game.name}")
        print("═" * W)
        if not streams:
            print("  (no live streams found)")
        else:
            print(f"  {'Streamer':<25} {'Viewers':>8}  Title")
            print("─" * W)
            for s in streams:
                title = s.title[:38] + ("…" if len(s.title) > 38 else "")
                print(f"  {s.user_name:<25} {s.viewer_count:>8,}  {title}")
    print("\n" + "═" * W + "\n")


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
    parser.add_argument(
        "--list-streamers",
        nargs="?",
        const=3,
        type=int,
        metavar="N",
        help="List top N streamers per game (default: 3).",
    )
    args = parser.parse_args()

    count = min(max(args.count, 1), 100)

    auth = AppAccessToken()
    client = TwitchClient(auth=auth)
    games_api = GamesAPI(client)
    streams_api = StreamsAPI(client)

    games = games_api.get_top_games(first=count)

    if args.list_streamers is not None:
        streamers_per_game = min(max(args.list_streamers, 1), 100)
        print(f"\nFetching top {count} games with top {streamers_per_game} streamer(s) each...")
        print_streamers_per_game(games, streams_api, streamers_per_game)
    elif args.with_streamers:
        print(f"\nFetching top {count} games with live streamer counts...")
        enriched = []
        for game in games:
            n, is_capped = streams_api.get_live_stream_count_for_game(game.id)
            enriched.append(TopGameWithStreamers.from_top_game(game, n, is_capped))
        print_top_games_with_streamers(enriched)
    else:
        print(f"\nFetching top {count} games from Twitch API...")
        print_top_games(games)


if __name__ == "__main__":
    main()
