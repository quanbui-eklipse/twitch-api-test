"""
Base Twitch Helix API HTTP client.

Handles:
- Auth headers (Bearer token + Client-Id)
- Cursor-based pagination
- Rate limit handling (HTTP 429 with Retry-After)
- Request timeouts
"""

import time
from typing import Generator, Optional
import requests

from .auth import AppAccessToken

BASE_URL = "https://api.twitch.tv/helix"


class TwitchAPIError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(f"Twitch API error {status}: {message}")


class TwitchClient:
    """
    Thin wrapper around the Twitch Helix REST API.

    Usage:
        client = TwitchClient(auth_token)
        data = client.get("/games/top", params={"first": 20})
    """

    def __init__(self, auth: AppAccessToken, timeout: int = 10):
        self._auth = auth
        self._timeout = timeout
        self._session = requests.Session()

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._auth.token}",
            "Client-Id": self._auth.client_id,
        }

    def get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """
        Perform a single GET request to the Helix API.

        Args:
            endpoint: Path relative to BASE_URL, e.g. "/games/top"
            params: Query parameters dict

        Returns:
            Parsed JSON response body as a dict.

        Raises:
            TwitchAPIError: On non-2xx responses (after retry on 429).
        """
        url = BASE_URL + endpoint
        for attempt in range(3):
            resp = self._session.get(
                url,
                headers=self._headers(),
                params=params,
                timeout=self._timeout,
            )
            if resp.status_code == 429:
                retry_after = float(resp.headers.get("Retry-After", 1))
                time.sleep(retry_after)
                continue
            if not resp.ok:
                raise TwitchAPIError(resp.status_code, resp.text)
            return resp.json()
        raise TwitchAPIError(429, "Rate limit exceeded after retries.")

    def paginate(
        self,
        endpoint: str,
        params: Optional[dict] = None,
        max_pages: int = 10,
    ) -> Generator[list, None, None]:
        """
        Yield pages of results from a paginated Helix endpoint.

        Each yielded value is the raw list under the "data" key.
        Stops when there is no next cursor or max_pages is reached.

        Args:
            endpoint: Path relative to BASE_URL.
            params: Query parameters (will be copied; do not mutate original).
            max_pages: Hard cap on how many pages to fetch.
        """
        params = dict(params or {})
        cursor: Optional[str] = None
        pages_fetched = 0

        while pages_fetched < max_pages:
            if cursor:
                params["after"] = cursor
            elif "after" in params:
                del params["after"]

            body = self.get(endpoint, params=params)
            data = body.get("data", [])
            yield data

            pages_fetched += 1
            pagination = body.get("pagination", {})
            cursor = pagination.get("cursor")
            if not cursor or not data:
                break
