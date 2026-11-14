"""HTTP layer for beyazperde_mcp.

Beyazperde (beyazperde.com) answers plain HTTP 200 with a Chrome
user-agent — no bot wall, no login, no API key (verified live
2026-11-14, ~15 requests). Transport is plain httpx with a Chrome UA
and one retry on transport failure; requests are read-only GETs
spaced ~0.5s apart. If the site ever starts 403ing, switch to
curl-cffi chrome131 impersonation (see iskur-mcp's http.py).

VM note: on this VM outbound HTTPS goes through an egress proxy; the
MCP stdio client spawns servers with a minimal environment (no proxy
variables), so client-spawned runs here need the proxy variables
forwarded (see tests/smoke_mcp.py) or requests die mid-TLS. On a
normal machine with direct internet this does not apply.
"""
from __future__ import annotations

import json
import os
import time
from urllib.parse import quote

import httpx

from . import beyazperde as _B

BASE = "https://www.beyazperde.com"

TIMEOUT = 30.0
MIN_INTERVAL = 0.5  # seconds between requests — be polite
_MAX_ATTEMPTS = 3
_RETRY_BACKOFF = 1.0

# httpx's env-proxy parsing chokes on this VM's NO_PROXY entries
# ("[::1]" -> InvalidURL "Invalid port: ':1]'"), so the proxy is
# read explicitly and trust_env is off. On a machine without proxy
# variables this is just a direct connection.
_PROXY = (
    os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    or None
)

# TLS trust: the egress proxy MITMs with its own CA, which lives in
# the system bundle (/etc/ssl/certs/ca-certificates.crt) but NOT in
# httpx's bundled certifi store — certifi-only verification fails
# with CERTIFICATE_VERIFY_FAILED from this VM. Prefer an explicit
# CA-bundle env var, then the system bundle, then certifi default.
_VERIFY: str | bool = (
    os.environ.get("SSL_CERT_FILE")
    or os.environ.get("CURL_CA_BUNDLE")
    or os.environ.get("REQUESTS_CA_BUNDLE")
    or (
        "/etc/ssl/certs/ca-certificates.crt"
        if os.path.exists("/etc/ssl/certs/ca-certificates.crt")
        else True
    )
)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
}

_last_fetch = 0.0


class BeyazperdeError(RuntimeError):
    pass


def _get(url: str, timeout: float = TIMEOUT) -> str:
    global _last_fetch
    wait = MIN_INTERVAL - (time.monotonic() - _last_fetch)
    if wait > 0:
        time.sleep(wait)
    last_exc: Exception | None = None
    try:
        for attempt in range(_MAX_ATTEMPTS):
            try:
                resp = httpx.get(url, headers=_HEADERS, timeout=timeout,
                                 follow_redirects=True, trust_env=False,
                                 proxy=_PROXY, verify=_VERIFY)
            except httpx.HTTPError as e:
                last_exc = e
                if attempt + 1 < _MAX_ATTEMPTS:
                    time.sleep(_RETRY_BACKOFF)
                    continue
                raise BeyazperdeError(
                    f"network error fetching {url}: {e}"
                ) from e
            if resp.status_code in (403, 429):
                if attempt + 1 < _MAX_ATTEMPTS:
                    time.sleep(_RETRY_BACKOFF)
                    continue
                raise BeyazperdeError(
                    "beyazperde.com refused the request "
                    f"(HTTP {resp.status_code}, bot wall/rate limit) — "
                    "try again later"
                )
            if resp.status_code == 404:
                raise BeyazperdeError(
                    f"beyazperde.com returned HTTP 404 for {url}"
                )
            if resp.status_code != 200:
                raise BeyazperdeError(
                    f"beyazperde.com returned HTTP {resp.status_code} "
                    f"for {url}"
                )
            return resp.text
    finally:
        _last_fetch = time.monotonic()
    raise BeyazperdeError(f"network error fetching {url}: {last_exc}")


def fetch_now_showing() -> str:
    """The now-showing page HTML."""
    return _get(f"{BASE}/filmler/vizyondakiler/sinema-sayisi/")


def search_autocomplete(query: str) -> dict:
    """The movie autocomplete JSON for a query string."""
    url = f"{BASE}/_/autocomplete/movie/{quote(query)}"
    return json.loads(_get(url))


def fetch_movie(film_id: str) -> str:
    """One film's detail page HTML."""
    return _get(f"{BASE}/filmler/film-{film_id}/")


def fetch_showtimes(film_id: str, geocode: str) -> str:
    """One film's showtimes page HTML for a city geocode."""
    return _get(
        f"{BASE}/filmler/film-{film_id}/seanslar/civarinda-{geocode}/"
    )


def fetch_news() -> str:
    """The film-news list page HTML."""
    return _get(f"{BASE}/haberler/filmler/")


def fetch_cinemas_page() -> str:
    """The /sinemalar/ regions page HTML."""
    return _get(f"{BASE}/sinemalar/")


def fetch_home() -> str:
    """The homepage HTML (health probe)."""
    return _get(f"{BASE}/")


def health_check() -> dict:
    """One polite probe of the Beyazperde homepage.

    Returns {"status": "ok"|"blocked"|"error", "http_status": int|None,
    "url": ..., "detail": ...}. Used by the `beyazperde_health` tool
    and the daily smoke CI.
    """
    url = BASE + "/"
    try:
        _get(url)
    except BeyazperdeError as e:
        msg = str(e)
        if "403" in msg:
            return {"status": "blocked", "http_status": 403, "url": url, "detail": msg}
        if "429" in msg:
            return {"status": "blocked", "http_status": 429, "url": url, "detail": msg}
        return {"status": "error", "http_status": None, "url": url, "detail": msg}
    return {"status": "ok", "http_status": 200, "url": url}
