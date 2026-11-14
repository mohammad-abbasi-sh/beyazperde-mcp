# beyazperde-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/beyazperde-mcp

Unofficial **read-only** MCP server for Beyazperde (beyazperde.com) — Turkey's leading cinema portal (the Turkish AlloCiné). List the films currently in cinemas, search films by title, get one film's detail (synopsis, release date, duration, genres, director, cast, member/press ratings), list today's showtimes for a film in any of 85 cities, and read the latest film news.

> Built by Mohammad Abbasi as part of the "Turkey MCP factory" (Sepehr-style pipeline). Not affiliated with Beyazperde or Webedia.

**Note:** showtimes are for **today only** — the site's date parameter does not change the server response (date filtering is client-side). New films have no ratings yet (`ratings: {}`). The site is Turkish-language; titles, genres and synopses are returned in Turkish. Movie search uses the site's autocomplete JSON endpoint — the site's own search page renders no server-side results.

## For AI agents

Add to your MCP client config (stdio):

```json
{
  "mcpServers": {
    "beyazperde": {
      "command": "uvx",
      "args": ["beyazperde-mcp==0.1.0"]
    }
  }
}
```

Or run locally: `python -m beyazperde_mcp.server` (needs `mcp<2`, `httpx>=0.27`).

## Tools

| Tool | Description |
|------|-------------|
| `beyazperde_now_showing` | Films currently in cinemas — `limit` 1..13; each film: film_id, title, release_date, duration_minutes, genres, director, cast (first 5), poster, url |
| `beyazperde_search_movies` | Search films by title — `query` (e.g. "dune", "Çirko"), `limit` 1..10; each result: film_id, title, original_title, year, director, first_release, last_release, genres, viewcount, poster, url |
| `beyazperde_get_movie` | Detail of one film — `film_id` (e.g. "1000013643" for Çirko): title, synopsis, release_date, duration_minutes, genres, director, cast, poster, ratings |
| `beyazperde_showtimes` | Today's showtimes for one film in a city — `film_id`, `city` name or geocode (default "İstanbul"), `limit_cinemas` 1..20; each cinema: cinema_id, name, address, showtimes [{date, version, time, datetime}] |
| `beyazperde_latest_news` | Latest film news — `limit` 1..10; each item: news_id, title, url |
| `beyazperde_list_cities` | The 85 showtimes cities — geocode + name (e.g. "154167" İstanbul), including the 4 Northern-Cyprus cities |
| `beyazperde_health` | Check whether Beyazperde is reachable (ok / blocked / error) |

Example output (`beyazperde_showtimes` / Çirko, İstanbul, 2026-11-14):

```json
{"film_id": "1000013643", "city": "İstanbul", "geocode": "154167",
 "count": 30,
 "cinemas": [{"cinema_id": "T0211", "name": "City’s Nişantaşı – CINEWAM Premium",
  "address": "Tesvikiye Cad. No:192 K:6 34365 Sisli",
  "showtimes": [{"date": "14 Kasım 2026", "version": "Türkçe Dublajlı",
   "time": "11:00", "datetime": "2026-11-14T11:00:00+03:00"}]}]}
```

## How it works

Everything is plain HTTP GETs against beyazperde.com with a Chrome user-agent (no bot wall, no login, no API key — verified 2026-11-14). Now showing is `/filmler/vizyondakiler/sinema-sayisi/` (`li.mdl > div.card.entity-card` cards); search is the autocomplete JSON endpoint `/_/autocomplete/movie/<query>` (only `entity_type == "movie"` kept); film detail is `/filmler/film-<id>/` (og:title / og:description / og:image, `.meta-body-info` for date/duration/genres, `.rating-item` blocks for ratings); showtimes are `/filmler/film-<id>/seanslar/civarinda-<geocode>/` (`.theater-card` blocks, identical (date, version, time) triples deduped — the page repeats times across duplicate version blocks); news is `/haberler/filmler/` (deduplicated by id); cities are `/sinemalar/` region links plus the 4 Northern-Cyprus entries from the embedded 85-city geocode map (parsed from the showtimes page's city selector, 2026-11-14). A wrong geocode returns the site's 404 page, so cities are validated before fetching. Requests are spaced ~0.5s apart; everything is read-only.

## Install

```bash
uvx beyazperde-mcp==0.1.0   # run directly (needs uv)
# or
pip install beyazperde-mcp==0.1.0
beyazperde-mcp    # starts the MCP server on stdio
```

## Tests

```bash
python -m venv .venv && .venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests -v
```

Offline tests run on recorded fixtures (real pages fetched 2026-11-14); live tests hit beyazperde.com (structure/range assertions, no exact values). Tests green at build time (see repo for counts) plus an MCP stdio smoke test.

## Roadmap

- Showtimes for a chosen date (once the site's client-side date filtering is understood)
- Coming-soon films (`/filmler/yakinda/`)
- Trailer / video links per film

## License

MIT — see [LICENSE](LICENSE).

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
