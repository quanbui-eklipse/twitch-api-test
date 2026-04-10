"""
Demo entry point for the Game Performance Intelligence feature.

Usage:
    cp .env.example .env        # fill in TWITCH_CLIENT_ID + TWITCH_CLIENT_SECRET
    pip install -r requirements.txt
    python main.py <broadcaster_id>

Example:
    python main.py 141981764    # xQc's broadcaster ID
"""

import sys
from src.twitch.auth import AppAccessToken
from src.twitch.client import TwitchClient
from src.twitch.api.games import GamesAPI
from src.twitch.api.clips import ClipsAPI
from src.services.game_performance import GamePerformanceService


def main(broadcaster_id: str) -> None:
    auth = AppAccessToken()
    client = TwitchClient(auth=auth)

    service = GamePerformanceService(
        games_api=GamesAPI(client),
        clips_api=ClipsAPI(client),
    )

    print(f"\nFetching game performance report for broadcaster {broadcaster_id}...")
    report = service.get_report(broadcaster_id, clip_pages=2, top_games_count=20)

    print(f"\n=== Game Performance Report ===")
    print(f"Generated at: {report.generated_at}\n")

    if not report.games:
        print("No clips found for this broadcaster.")
    else:
        print(f"{'Game':<30} {'Clips':>6} {'Total Views':>12} {'Avg Views':>10} {'Best Clip'}")
        print("-" * 85)
        for g in report.games:
            print(
                f"{g.game_name:<30} {g.clip_count:>6} {g.total_views:>12,} "
                f"{g.avg_views_per_clip:>10,.0f}  {g.top_clip_title[:30]}"
            )

    if report.trending_games_not_streamed:
        print(f"\n=== Trending Games You Haven't Clipped ===")
        for i, game in enumerate(report.trending_games_not_streamed[:10], 1):
            print(f"  {i:2}. {game.name}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <broadcaster_id>")
        sys.exit(1)
    main(sys.argv[1])
