"""
Twitch OAuth2 App Access Token management (Client Credentials flow).

Requires no user interaction — suitable for reading public data such as
top games, clips, and game analytics.
"""

import time
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN_URL = "https://id.twitch.tv/oauth2/token"


class TwitchAuthError(Exception):
    pass


class AppAccessToken:
    """Fetches and caches a Twitch App Access Token using Client Credentials."""

    def __init__(self, client_id: str = None, client_secret: str = None):
        self.client_id = client_id or os.environ.get("TWITCH_CLIENT_ID")
        self.client_secret = client_secret or os.environ.get("TWITCH_CLIENT_SECRET")

        if not self.client_id or not self.client_secret:
            raise TwitchAuthError(
                "TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET must be set "
                "(via env vars or constructor arguments)."
            )

        self._token: str | None = None
        self._expires_at: float = 0.0

    @property
    def token(self) -> str:
        """Return a valid access token, refreshing if expired."""
        if self._is_expired():
            self._fetch()
        return self._token

    def _is_expired(self) -> bool:
        # Refresh 60 seconds before actual expiry to avoid edge-case failures.
        return time.time() >= self._expires_at - 60

    def _fetch(self) -> None:
        resp = requests.post(
            TOKEN_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            },
            timeout=10,
        )
        if not resp.ok:
            raise TwitchAuthError(
                f"Failed to obtain access token: {resp.status_code} {resp.text}"
            )
        data = resp.json()
        self._token = data["access_token"]
        self._expires_at = time.time() + data["expires_in"]
