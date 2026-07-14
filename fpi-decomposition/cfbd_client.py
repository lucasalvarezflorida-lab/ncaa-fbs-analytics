"""Fetch layer for the CollegeFootballData API.

Reads the API key from the CFBD_API_KEY environment variable (never logged
or printed) and caches raw JSON responses under ./data so repeated runs
don't hammer the API.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

import requests

BASE_URL = "https://api.collegefootballdata.com"
DATA_DIR = Path(__file__).parent / "data"

RETRY_STATUSES = {429, 500, 502, 503, 504}
MAX_RETRIES = 3


class CFBDError(RuntimeError):
    """Raised when the CFBD API cannot be reached or returns an error."""


def _auth_headers() -> dict:
    key = os.environ.get("CFBD_API_KEY")
    if not key:
        raise CFBDError(
            "CFBD_API_KEY environment variable is not set. "
            "Get a free key at https://collegefootballdata.com/key and set it "
            "before running (the key is read from the environment only)."
        )
    return {"Authorization": f"Bearer {key}"}


def _cache_path(endpoint: str, params: dict) -> Path:
    slug = endpoint.strip("/").replace("/", "_")
    if params:
        parts = "_".join(f"{k}-{params[k]}" for k in sorted(params))
        slug = f"{slug}_{parts}"
    slug = re.sub(r"[^A-Za-z0-9_.-]", "-", slug)
    return DATA_DIR / f"{slug}.json"


def get(endpoint: str, params: dict | None = None, refresh: bool = False) -> list:
    """GET a CFBD endpoint, returning parsed JSON (cached on disk)."""
    params = params or {}
    cache = _cache_path(endpoint, params)
    if cache.exists() and not refresh:
        with open(cache, encoding="utf-8") as f:
            return json.load(f)

    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(
                BASE_URL + endpoint,
                params=params,
                headers=_auth_headers(),
                timeout=30,
            )
        except requests.RequestException as exc:
            last_err = f"network error: {exc}"
            time.sleep(2 ** attempt)
            continue

        if resp.status_code == 200:
            payload = resp.json()
            DATA_DIR.mkdir(exist_ok=True)
            with open(cache, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            return payload
        if resp.status_code == 401:
            raise CFBDError(
                f"CFBD returned 401 Unauthorized for {endpoint} — check that "
                "CFBD_API_KEY holds a valid key."
            )
        if resp.status_code in RETRY_STATUSES:
            last_err = f"HTTP {resp.status_code}"
            time.sleep(2 ** attempt)
            continue
        raise CFBDError(f"CFBD request to {endpoint} failed: HTTP {resp.status_code}")

    raise CFBDError(
        f"CFBD request to {endpoint} failed after {MAX_RETRIES} attempts ({last_err})"
    )


def fetch_fpi(year: int, refresh: bool = False) -> list:
    return get("/ratings/fpi", {"year": year}, refresh)


def fetch_sp(year: int, refresh: bool = False) -> list:
    return get("/ratings/sp", {"year": year}, refresh)


def fetch_returning(year: int, refresh: bool = False) -> list:
    return get("/player/returning", {"year": year}, refresh)


def fetch_talent(year: int, refresh: bool = False) -> list:
    return get("/talent", {"year": year}, refresh)


def fetch_recruiting(year: int, refresh: bool = False) -> list:
    return get("/recruiting/teams", {"year": year}, refresh)


def fetch_portal(year: int, refresh: bool = False) -> list:
    return get("/player/portal", {"year": year}, refresh)
