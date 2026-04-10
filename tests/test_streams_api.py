"""Tests for StreamsAPI."""

import pytest
import responses as resp_lib
from unittest.mock import MagicMock

from src.twitch.client import TwitchClient
from src.twitch.api.streams import StreamsAPI

BASE = "https://api.twitch.tv/helix"


def make_api():
    auth = MagicMock()
    auth.token = "tok"
    auth.client_id = "cid"
    return StreamsAPI(TwitchClient(auth=auth))


def _stream(i):
    return {"id": str(i), "user_id": str(i), "game_id": "33214",
            "type": "live", "viewer_count": 100}


@resp_lib.activate
def test_count_exact_when_under_100():
    resp_lib.add(
        resp_lib.GET, BASE + "/streams",
        json={"data": [_stream(i) for i in range(42)], "pagination": {}},
        status=200,
    )
    api = make_api()
    count, is_capped = api.get_live_stream_count_for_game("33214")
    assert count == 42
    assert is_capped is False


@resp_lib.activate
def test_count_capped_when_cursor_present():
    resp_lib.add(
        resp_lib.GET, BASE + "/streams",
        json={"data": [_stream(i) for i in range(100)],
              "pagination": {"cursor": "abc"}},
        status=200,
    )
    api = make_api()
    count, is_capped = api.get_live_stream_count_for_game("33214")
    assert count == 100
    assert is_capped is True


@resp_lib.activate
def test_count_zero_for_game_with_no_streams():
    resp_lib.add(
        resp_lib.GET, BASE + "/streams",
        json={"data": [], "pagination": {}},
        status=200,
    )
    api = make_api()
    count, is_capped = api.get_live_stream_count_for_game("99999")
    assert count == 0
    assert is_capped is False


@resp_lib.activate
def test_requests_live_type_and_100_first():
    resp_lib.add(
        resp_lib.GET, BASE + "/streams",
        json={"data": [], "pagination": {}},
        status=200,
    )
    api = make_api()
    api.get_live_stream_count_for_game("33214")
    url = resp_lib.calls[0].request.url
    assert "first=100" in url
    assert "type=live" in url
