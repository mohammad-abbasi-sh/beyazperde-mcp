"""MCP server: unofficial read-only access to Beyazperde
(beyazperde.com) — Turkey's leading cinema portal (the Turkish
AlloCiné): films now showing, movie search, film details, showtimes
by city, film news, and the 85 showtimes cities."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

from . import beyazperde as _B
from . import http as _http

mcp = FastMCP("beyazperde-mcp")

INSTRUCTIONS = """\
Unofficial read-only MCP server for Beyazperde (beyazperde.com) —
Turkey's leading cinema portal. beyazperde_now_showing lists the
films currently in cinemas (title, release date, duration, genres,
director, cast, poster); beyazperde_search_movies searches films by
title via the site's autocomplete endpoint (the site's own search
page renders no server-side results); beyazperde_get_movie returns
one film's detail (synopsis, release date, duration, genres,
director, cast, poster, member/press ratings — new films have no
ratings yet); beyazperde_showtimes lists today's showtimes for one
film in a city (city name or geocode, default İstanbul — use
beyazperde_list_cities for the 85 cities); beyazperde_latest_news
lists the latest film news; beyazperde_list_cities lists the 85
showtimes cities (geocode + name, including Northern Cyprus).
Showtimes are TODAY only — the site's date parameter does not change
the server response. Data comes from the site's own pages — no login,
no API key. Read-only; requests are spaced ~0.5s apart. The site is
Turkish-language; titles, genres and synopses are returned in
Turkish.
Built by Mohammad Abbasi (mohammad-abbasi-sh) — https://almanibama.ir · https://mabbasi.ir — Turkey MCP
factory.\
"""


_SOURCE = "beyazperde.com"
_DISCLAIMER = "Unofficial read-only data from Beyazperde (beyazperde.com); showtimes are for today only and change during the day — verify on the site before going to the cinema."


def _envelope() -> dict:
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": _SOURCE,
        "disclaimer": _DISCLAIMER,
    }


def _ok(payload: dict) -> str:
    return json.dumps({**_envelope(), **payload}, ensure_ascii=False)


def _limit(limit: int, cap: int) -> int:
    return max(1, min(int(limit), cap))


@mcp.tool()
def beyazperde_now_showing(limit: int = 13) -> str:
    """Films currently showing in Turkish cinemas.

    limit: 1..13 films returned (the site lists ~13). Each film:
    film_id, title, release_date ("13 Kasım 2026"), duration_minutes,
    genres, director, cast (first 5), poster, url."""
    try:
        films = _B.parse_now_showing(_http.fetch_now_showing())
    except _http.BeyazperdeError as e:
        return _ok({"error": str(e)})
    films = films[:_limit(limit, 13)]
    return _ok({"count": len(films), "films": films})


@mcp.tool()
def beyazperde_search_movies(query: str, limit: int = 10) -> str:
    """Search Beyazperde films by title.

    query: Turkish (or original) film title, e.g. "dune", "Çirko".
    limit: 1..10 results returned. Each result: film_id, title,
    original_title, year, director, first_release, last_release,
    genres, viewcount, poster, url. Searches the site's autocomplete
    endpoint — the site's own search page renders no results."""
    query = query.strip()
    if not query:
        return _ok({"error": "query must not be empty", "query": query})
    try:
        results = _B.parse_autocomplete(_http.search_autocomplete(query))
    except _http.BeyazperdeError as e:
        return _ok({"error": str(e), "query": query})
    except ValueError as e:
        return _ok({"error": f"bad autocomplete response: {e}",
                    "query": query})
    results = results[:_limit(limit, 10)]
    return _ok({"query": query, "count": len(results),
                "results": results})


@mcp.tool()
def beyazperde_get_movie(film_id: str) -> str:
    """Detail of one Beyazperde film.

    film_id: the numeric film id (e.g. "1000013643" for Çirko).
    Returns title, synopsis, release_date, duration_minutes, genres,
    director, cast, poster, ratings (member/press scores — {} when
    the film has no ratings yet), url."""
    film_id = film_id.strip()
    if not re.fullmatch(r"\d+", film_id):
        return _ok({"error": f"film_id must be numeric, got {film_id!r}",
                    "film_id": film_id})
    try:
        detail = _B.parse_movie(_http.fetch_movie(film_id))
    except _http.BeyazperdeError as e:
        return _ok({"error": str(e), "film_id": film_id})
    if not detail:
        return _ok({"error": f"no film found for id {film_id!r} — "
                    "unknown film id or the page moved",
                    "film_id": film_id})
    return _ok(detail)


@mcp.tool()
def beyazperde_showtimes(film_id: str, city: str = "İstanbul",
                         limit_cinemas: int = 20) -> str:
    """Today's showtimes for one film in one city.

    film_id: the numeric film id (e.g. "1000013643"). city: city
    name (e.g. "İstanbul", "Ankara", "İzmir") or geocode (e.g.
    "154167") — default İstanbul; use beyazperde_list_cities for the
    85 cities. limit_cinemas: 1..20 cinemas returned. Each cinema:
    cinema_id, name, address, showtimes [{date, version, time,
    datetime}]. Showtimes are TODAY only — the site serves no other
    date from this endpoint."""
    film_id = film_id.strip()
    if not re.fullmatch(r"\d+", film_id):
        return _ok({"error": f"film_id must be numeric, got {film_id!r}",
                    "film_id": film_id})
    geocode = _B.city_geocode(city)
    if geocode is None:
        return _ok({"error": f"unknown city {city!r} — try "
                    "beyazperde_list_cities for city names/geocodes",
                    "film_id": film_id, "city": city})
    try:
        cinemas = _B.parse_showtimes(
            _http.fetch_showtimes(film_id, geocode))
    except _http.BeyazperdeError as e:
        return _ok({"error": str(e), "film_id": film_id, "city": city})
    if not cinemas:
        return _ok({"error": f"no showtimes found for film {film_id!r} "
                    f"in {city} — the film may not be showing there today",
                    "film_id": film_id, "city": city})
    cinemas = cinemas[:_limit(limit_cinemas, 20)]
    return _ok({"film_id": film_id, "city": city, "geocode": geocode,
                "count": len(cinemas), "cinemas": cinemas})


@mcp.tool()
def beyazperde_latest_news(limit: int = 10) -> str:
    """Beyazperde's latest film news (haberler).

    limit: 1..10 news items returned. Each item: news_id, title,
    url. Titles are in Turkish."""
    try:
        items = _B.parse_news(_http.fetch_news())
    except _http.BeyazperdeError as e:
        return _ok({"error": str(e)})
    items = items[:_limit(limit, 10)]
    return _ok({"count": len(items), "news": items})


@mcp.tool()
def beyazperde_list_cities() -> str:
    """The 85 cities Beyazperde lists showtimes for — geocode + name.

    Use the name (e.g. "İstanbul") or the geocode (e.g. "154167") in
    beyazperde_showtimes. Includes the 4 Northern-Cyprus cities
    (Girne, Güzelyurt, Lefkoşe, Mağusa). Parsed live from
    /sinemalar/; falls back to the built-in list if the page cannot
    be read."""
    try:
        cities = _B.parse_cities(_http.fetch_cinemas_page())
    except _http.BeyazperdeError as e:
        return _ok({"error": str(e)})
    return _ok({"count": len(cities), "cities": cities})


@mcp.tool()
def beyazperde_health() -> str:
    """Check whether Beyazperde is reachable right now.

    Returns status ok (HTTP 200), blocked (HTTP 403/429 — bot wall or
    rate limit) or error, plus the HTTP status and the probed URL.
    One polite request; it does not fetch any data."""
    return _ok(_http.health_check())


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    import sys

    sys.exit(main())
