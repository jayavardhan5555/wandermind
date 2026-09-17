from __future__ import annotations

import threading
import time
import httpx

from config import get_settings, Settings
from mcp_server import MissingCredentials, ToolError

AMADEUS_BASE = "https://test.api.amadeus.com"

_TIMEOUT = httpx.Timeout(15.0,connect=5.0)
_USER_AGENT = "WanderMind/0.1 (+https://github.com/wandermind)"

def http_client() -> httpx.Client:
    """Return a configured sync HTTP client"""
    return httpx.Client(timeout=_TIMEOUT,headers={"User-Agent": _USER_AGENT})

def get_json(client:httpx.Client,url:str,*,params=None,headers=None)-> dict:
    try:
        resp = client.get(url,params=params,headers=headers)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as ex:
        raise ToolError(f"{url} returned {ex.response.status_code}") from ex
    except httpx.HTTPError as ex:
        raise ToolError(f"request to {url} failed: {ex}") from ex

class AmadeusAuth:

    _lock = threading.Lock()
    _token:str | None = None
    _expires_at:float = 0.0

    @classmethod
    def token(cls,settings:Settings,client:httpx.Client) -> str:
        """Return a valid Amadeus API token"""

        if not (settings.amadeus_client_id and settings.amadeus_client_secret):
            raise MissingCredentials("amadeus")

        with cls._lock:
            if cls._token and time.time() < cls._expires_at - 30:
                return cls._token
            try:
                resp = client.post(
                    f"{AMADEUS_BASE}/v1/security/oauth2/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": settings.amadeus_client_id,
                        "client_secret": settings.amadeus_client_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                resp.raise_for_status()
            except httpx.HTTPError as ex:
                raise ToolError(f"Amadeus auth request failed: {ex}") from ex

            payload = resp.json()
            cls._token = payload["access_token"]
            cls._expires_at = time.time() + float(payload.get("expires_in", 1800))
            assert cls._token is not None
            return cls._token

    @classmethod
    def auth_header(cls,settings:Settings,client:httpx.Client) -> dict[str,str]:
        return {"Authorization": f"Bearer {cls.token(settings,client)}"}

