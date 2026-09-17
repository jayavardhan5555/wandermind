from __future__ import annotations

import httpx

from src.mcp_server import ToolError

_TIMEOUT = httpx.Timeout(15.0, connect=5.0)
_USER_AGENT = "WanderMind/0.1 (+https://github.com/wandermind)"


def http_client() -> httpx.Client:
    """Return a configured sync HTTP client."""
    return httpx.Client(timeout=_TIMEOUT, headers={"User-Agent": _USER_AGENT})


def get_json(client: httpx.Client, url: str, *, params=None, headers=None) -> dict:
    try:
        resp = client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as ex:
        raise ToolError(f"{url} returned {ex.response.status_code}") from ex
    except httpx.HTTPError as ex:
        raise ToolError(f"request to {url} failed: {ex}") from ex

