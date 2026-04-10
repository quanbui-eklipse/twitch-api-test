"""Tests for TwitchClient — base HTTP client with rate limiting and pagination."""

import pytest
import responses as resp_lib
from unittest.mock import MagicMock

from src.twitch.client import TwitchClient, TwitchAPIError

BASE = "https://api.twitch.tv/helix"


def make_client():
    auth = MagicMock()
    auth.token = "fake_token"
    auth.client_id = "fake_client_id"
    return TwitchClient(auth=auth)


@resp_lib.activate
def test_get_returns_parsed_json():
    resp_lib.add(
        resp_lib.GET,
        BASE + "/games/top",
        json={"data": [{"id": "1", "name": "Fortnite", "box_art_url": ""}]},
        status=200,
    )
    client = make_client()
    result = client.get("/games/top", params={"first": 1})
    assert result["data"][0]["name"] == "Fortnite"


@resp_lib.activate
def test_get_includes_auth_headers():
    resp_lib.add(
        resp_lib.GET,
        BASE + "/games/top",
        json={"data": []},
        status=200,
    )
    client = make_client()
    client.get("/games/top")
    request = resp_lib.calls[0].request
    assert request.headers["Authorization"] == "Bearer fake_token"
    assert request.headers["Client-Id"] == "fake_client_id"


@resp_lib.activate
def test_get_raises_on_error():
    resp_lib.add(
        resp_lib.GET,
        BASE + "/games/top",
        json={"error": "Unauthorized"},
        status=401,
    )
    client = make_client()
    with pytest.raises(TwitchAPIError) as exc_info:
        client.get("/games/top")
    assert exc_info.value.status == 401


@resp_lib.activate
def test_get_retries_on_rate_limit():
    # First call returns 429, second returns 200
    resp_lib.add(
        resp_lib.GET,
        BASE + "/games/top",
        status=429,
        headers={"Retry-After": "0"},
    )
    resp_lib.add(
        resp_lib.GET,
        BASE + "/games/top",
        json={"data": []},
        status=200,
    )
    client = make_client()
    result = client.get("/games/top")
    assert result == {"data": []}
    assert len(resp_lib.calls) == 2


@resp_lib.activate
def test_paginate_yields_all_pages():
    resp_lib.add(
        resp_lib.GET,
        BASE + "/clips",
        json={
            "data": [{"id": "clip1"}],
            "pagination": {"cursor": "abc"},
        },
        status=200,
    )
    resp_lib.add(
        resp_lib.GET,
        BASE + "/clips",
        json={
            "data": [{"id": "clip2"}],
            "pagination": {},
        },
        status=200,
    )
    client = make_client()
    pages = list(client.paginate("/clips", params={"broadcaster_id": "123"}))
    assert len(pages) == 2
    assert pages[0][0]["id"] == "clip1"
    assert pages[1][0]["id"] == "clip2"


@resp_lib.activate
def test_paginate_stops_at_max_pages():
    for _ in range(5):
        resp_lib.add(
            resp_lib.GET,
            BASE + "/clips",
            json={"data": [{"id": "x"}], "pagination": {"cursor": "next"}},
            status=200,
        )
    client = make_client()
    pages = list(client.paginate("/clips", params={}, max_pages=2))
    assert len(pages) == 2


@resp_lib.activate
def test_paginate_stops_on_empty_page():
    resp_lib.add(
        resp_lib.GET,
        BASE + "/clips",
        json={"data": [], "pagination": {"cursor": "abc"}},
        status=200,
    )
    client = make_client()
    pages = list(client.paginate("/clips", params={}))
    assert len(pages) == 1
