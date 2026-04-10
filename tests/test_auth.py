"""Tests for TwitchAuth — App Access Token fetching and caching."""

import time
import pytest
import responses as resp_lib

from src.twitch.auth import AppAccessToken, TwitchAuthError

TOKEN_URL = "https://id.twitch.tv/oauth2/token"


@resp_lib.activate
def test_fetch_token_on_first_access():
    resp_lib.add(
        resp_lib.POST,
        TOKEN_URL,
        json={"access_token": "test_token_123", "expires_in": 3600},
        status=200,
    )
    auth = AppAccessToken(client_id="cid", client_secret="csec")
    assert auth.token == "test_token_123"
    assert len(resp_lib.calls) == 1


@resp_lib.activate
def test_token_cached_on_second_access():
    resp_lib.add(
        resp_lib.POST,
        TOKEN_URL,
        json={"access_token": "cached_token", "expires_in": 3600},
        status=200,
    )
    auth = AppAccessToken(client_id="cid", client_secret="csec")
    _ = auth.token
    _ = auth.token  # second access — should not re-fetch
    assert len(resp_lib.calls) == 1


@resp_lib.activate
def test_token_refreshed_when_expired():
    resp_lib.add(
        resp_lib.POST,
        TOKEN_URL,
        json={"access_token": "first_token", "expires_in": 0},
        status=200,
    )
    resp_lib.add(
        resp_lib.POST,
        TOKEN_URL,
        json={"access_token": "second_token", "expires_in": 3600},
        status=200,
    )
    auth = AppAccessToken(client_id="cid", client_secret="csec")
    _ = auth.token           # fetch first token (expires immediately)
    token2 = auth.token      # should detect expiry and re-fetch
    assert token2 == "second_token"
    assert len(resp_lib.calls) == 2


@resp_lib.activate
def test_raises_on_auth_failure():
    resp_lib.add(
        resp_lib.POST,
        TOKEN_URL,
        json={"error": "invalid_client"},
        status=401,
    )
    auth = AppAccessToken(client_id="bad_id", client_secret="bad_sec")
    with pytest.raises(TwitchAuthError):
        _ = auth.token


def test_raises_when_credentials_missing():
    with pytest.raises(TwitchAuthError):
        AppAccessToken(client_id=None, client_secret=None)
