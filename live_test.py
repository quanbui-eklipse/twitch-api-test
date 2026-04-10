"""
Live integration test — calls the real Twitch API.

Usage (from project root):
    pip install -r requirements.txt
    python live_test.py

Credentials are loaded from .env automatically.
"""

from src.twitch.auth import AppAccessToken
from src.twitch.client import TwitchClient
from src.twitch.api.games import GamesAPI


def main():
    auth = AppAccessToken()          # reads TWITCH_CLIENT_ID + SECRET from .env
    client = TwitchClient(auth=auth)
    api = GamesAPI(client)

    print("\nFetching top 20 games from Twitch API (LIVE)...\n")
    games = api.get_top_games(first=20)

    W = 65
    print("═" * W)
    print("  TWITCH — TOP GAMES RIGHT NOW")
    print("═" * W)
    print(f"  {'#':<4} {'Game Name':<35} {'Game ID'}")
    print("─" * W)
    for i, g in enumerate(games, 1):
        print(f"  {i:<4} {g.name:<35} {g.id}")
    print("═" * W)
    print(f"\n  {len(games)} games returned.\n")


if __name__ == "__main__":
    main()
