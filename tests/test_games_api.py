"""Tests for GamesAPI."""

import pytest
import responses as resp_lib
from unittest.mock import MagicMock

from src.twitch.client import TwitchClient
from src.twitch.api.games import GamesAPI

BASE = "https://api.twitch.tv/helix"

FORTNITE = {"id": "33214", "name": "Fortnite", "box_art_url": "https://example.com/fn.jpg", "igdb_id": ""}
VALORANT = {"id": "516575", "name": "VALORANT", "box_art_url": "https://example.com/val.jpg", "igdb_id": ""}


def make_api():
    auth = MagicMock()
    auth.token = "tok"
    auth.client_id = "cid"
    return GamesAPI(TwitchClient(auth=auth))


@resp_lib.activate
def test_get_top_games_returns_list():
    resp_lib.add(
        resp_lib.GET,
        BASE + "/games/top",
        json={"data": [FORTNITE, VALORANT], "pagination": {}},
        status=200,
    )
    api = make_api()
    games = api.get_top_games(first=2)
    assert len(games) == 2
    assert games[0].name == "Fortnite"
    assert games[1].id == "516575"


@resp_lib.activate
def test_get_top_games_caps_at_100():
    resp_lib.add(
        resp_lib.GET,
        BASE + "/games/top",
        json={"data": [], "pagination": {}},
        status=200,
    )
    api = make_api()
    api.get_top_games(first=200)
    qs = resp_lib.calls[0].request.url
    assert "first=100" in qs


@resp_lib.activate
def test_get_games_by_id():
    resp_lib.add(
        resp_lib.GET,
        BASE + "/games",
        json={"data": [FORTNITE]},
        status=200,
    )
    api = make_api()
    games = api.get_games_by_id(["33214"])
    assert games[0].name == "Fortnite"


def test_get_games_by_id_empty_returns_empty():
    api = make_api()
    assert api.get_games_by_id([]) == []


@resp_lib.activate
def test_get_games_by_name():
    resp_lib.add(
        resp_lib.GET,
        BASE + "/games",
        json={"data": [VALORANT]},
        status=200,
    )
    api = make_api()
    games = api.get_games_by_name(["VALORANT"])
    assert games[0].id == "516575"
