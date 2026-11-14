"""Stdlib parsing for beyazperde.com (Beyazperde — Turkey's leading
cinema portal, the Turkish AlloCiné).

Verified live 2026-11-14 against real pages (fixtures in tests/):
- Now showing: /filmler/vizyondakiler/sinema-sayisi/ — server-rendered
  `li.mdl > div.card.entity-card` cards (13 on the live page): film id
  from /filmler/film-<id>/, title from a.meta-title-link, release date
  from span.date ("13 Kasım 2026"), duration as bare text ("1s 25dk"),
  genres from the dark-grey-link spans inside .meta-body-info, director
  from .meta-body-direction, cast (first 5) from .meta-body-actor,
  poster from img.thumbnail-img (data-src, fallback src).
- Movie search: the site's own /aramak/ search page renders NO
  server-side results — the search mechanism is the autocomplete JSON
  endpoint /_/autocomplete/movie/<url-encoded query> returning
  {"error": false, "results": [...]}; each result has entity_id, label
  (Turkish title), original_label, data {id, year, director_name[],
  first_release, last_release, poster_path/thumbnail}, genres[],
  viewcount. Only entity_type == "movie" is kept.
- Movie detail: /filmler/film-<id>/ — title from og:title, synopsis
  from og:description (leading "Özet: " stripped), director from the
  "Yönetmen" .meta-body-direction block, cast from .meta-body-actor
  dark-grey-link spans plus /sanatcilar/sanatci-<id>/ links, genres /
  duration / release from .meta-body-info, poster from og:image,
  ratings from .rating-item blocks (rating-title + stareval-note
  "2,7" -> 2.7 + .stareval-review text). New films have NO rating
  items — ratings is {} then, never a crash.
- Showtimes: /filmler/film-<id>/seanslar/civarinda-<geocode>/ —
  .theater-card blocks: cinema name from .meta-theater-title a,
  cinema id from /sinemalar/sinema-<id>/, address from
  address.address, versions from .showtimes-version (.text like
  "14 Kasım 2026 - Türkçe Dublajlı" -> date + version label), hours
  from .showtimes-hour-item (visible time + data-showtime-time ISO
  datetime). Identical (date, version, time) triples are deduped —
  the page repeats times across duplicate version blocks. A wrong
  geocode returns an empty showtimes page (the site's 404 page body;
  HTTP 200 live), so callers must validate the city first (see
  city_geocode). Showtimes are TODAY
  only in v1: the ?shwt_date= query param does not change the server
  response (date filtering is client-side GraphQL).
- News: /haberler/filmler/ — links /haberler/filmler/haberler-<id>/
  with the title as link text (HTML entities unescaped), deduped by id.
- Cities: /sinemalar/ lists /sinemalar/bolgeye/<geocode>/ region links
  (79 on the live page); the full 85-city geocode map below was parsed
  from the showtimes page's city selector (seans.html, 2026-11-14) and
  is embedded as the fallback / validation source. It includes the 4
  Northern-Cyprus entries (Girne, Güzelyurt, Lefkoşe, Mağusa).
"""
from __future__ import annotations

import html as _html
import re

BASE = "https://www.beyazperde.com"

_WS = re.compile(r"\s+")

# The 85 showtimes cities, geocode -> name (parsed from the live
# showtimes page city selector, 2026-11-14). İstanbul is 154167.
CITIES = {
    "154136": "Adana",
    "154114": "Adıyaman",
    "154187": "Afyonkarahisar",
    "154173": "Ağrı",
    "154123": "Aksaray",
    "154144": "Amasya",
    "154124": "Ankara",
    "154137": "Antalya",
    "154174": "Ardahan",
    "154145": "Artvin",
    "154188": "Aydın",
    "154162": "Balıkesir",
    "154146": "Bartın",
    "154115": "Batman",
    "154147": "Bayburt",
    "154163": "Bilecik",
    "154175": "Bingöl",
    "154176": "Bitlis",
    "154148": "Bolu",
    "154138": "Burdur",
    "154164": "Bursa",
    "154165": "Çanakkale",
    "154125": "Çankırı",
    "154149": "Çorum",
    "154189": "Denizli",
    "154116": "Diyarbakır",
    "154150": "Düzce",
    "154166": "Edirne",
    "154177": "Elazığ",
    "154178": "Erzincan",
    "154179": "Erzurum",
    "154126": "Eskişehir",
    "154117": "Gaziantep",
    "154151": "Giresun",
    "265185": "Girne",
    "154152": "Gümüşhane",
    "265184": "Güzelyurt",
    "154180": "Hakkari",
    "154139": "Hatay",
    "154181": "İğdir",
    "154140": "Isparta",
    "154167": "İstanbul",
    "154190": "İzmir",
    "154141": "Kahramanmaraş",
    "154153": "Karabük",
    "154127": "Karaman",
    "154182": "Kars",
    "154154": "Kastamonu",
    "154128": "Kayseri",
    "154118": "Kilis",
    "154129": "Kırıkkale",
    "154168": "Kırklareli",
    "154130": "Kırşehir",
    "154169": "Kocaeli",
    "154131": "Konya",
    "154191": "Kütahya",
    "265186": "Lefkoşe",
    "265187": "Mağusa",
    "154183": "Malatya",
    "154192": "Manisa",
    "154119": "Mardin",
    "154142": "Mersin",
    "154193": "Muğla",
    "154184": "Muş",
    "154132": "Nevşehir",
    "154133": "Niğde",
    "154155": "Ordu",
    "154143": "Osmaniye",
    "154156": "Rize",
    "154170": "Sakarya",
    "154157": "Samsun",
    "154120": "Şanlıurfa",
    "154158": "Sinop",
    "154122": "Şırnak",
    "154121": "Siirt",
    "154134": "Sivas",
    "154171": "Tekirdağ",
    "154159": "Tokat",
    "154160": "Trabzon",
    "154185": "Tunceli",
    "154194": "Uşak",
    "154186": "Van",
    "154172": "Yalova",
    "154135": "Yozgat",
    "154161": "Zonguldak",
}

# Northern-Cyprus entries (in the embedded map, but missing from the
# /sinemalar/ regions list — appended by parse_cities if absent).
CYPRUS_CODES = {"265185", "265184", "265186", "265187"}

# Diacritic-insensitive lowercase folding for city-name matching:
# "IZMIR", "Izmir", "İzmir" and "izmir" must all match "İzmir".
_FOLD = str.maketrans({
    "İ": "i", "I": "i", "ı": "i", "Ş": "s", "ş": "s", "Ğ": "g",
    "ğ": "g", "Ü": "u", "ü": "u", "Ö": "o", "ö": "o", "Ç": "c",
    "ç": "c",
})


def _fold(text: str) -> str:
    return text.translate(_FOLD).lower()


def _clean(text: str | None) -> str:
    if not text:
        return ""
    return _WS.sub(" ", _html.unescape(text)).strip()


def _strip_tags(fragment: str) -> str:
    return _clean(re.sub(r"<[^>]+>", " ", fragment))


def _dark_grey_links(fragment: str) -> list[str]:
    """Texts of the dark-grey-link spans in a fragment."""
    return [
        _clean(t)
        for t in re.findall(
            r'dark-grey-link[^>]*>([^<]+)</span>', fragment
        )
        if _clean(t)
    ]


def _meta_block(card: str, marker: str) -> str:
    """The <div class="meta-body-item <marker>">...</div> block, or "".

    The block's inner divs are spans only, so the first </div> closes it.
    """
    m = re.search(
        r'<div class="meta-body-item ' + re.escape(marker) +
        r'[^>]*>(.*?)</div>',
        card, re.S,
    )
    return m.group(1) if m else ""


def _info_block(card: str) -> str:
    """The .meta-body-info block (date, duration, genres)."""
    m = re.search(
        r'<div class="meta-body-item meta-body-info[^>]*>(.*?)</div>\s*'
        r'(?:<div class="meta-body-item meta-body-direction|'
        r'<div class="meta-body-item meta-body-actor|</div>)',
        card, re.S,
    )
    if m:
        return m.group(1)
    # Fallback: everything from meta-body-info up to the direction block.
    start = card.find("meta-body-info")
    if start < 0:
        return ""
    end = card.find("meta-body-direction", start)
    if end < 0:
        end = card.find("meta-body-actor", start)
    return card[start:end] if end > start else card[start:]


def _parse_duration(text: str) -> int | None:
    """'1s 25dk' -> 85 minutes; None when absent."""
    m = re.search(r"(\d+)\s*s\s+(\d+)\s*dk", text)
    if not m:
        return None
    return int(m.group(1)) * 60 + int(m.group(2))


def _parse_date_span(fragment: str) -> str | None:
    m = re.search(
        r'<span[^>]*class="[^"]*\bdate\b[^"]*"[^>]*>([^<]+)</span>',
        fragment,
    )
    return _clean(m.group(1)) if m else None


def _parse_director(card: str) -> list[str]:
    """Director names from the 'Yönetmen' direction block (may be 2)."""
    for m in re.finditer(
        r'<div class="meta-body-item meta-body-direction[^>]*>(.*?)</div>',
        card, re.S,
    ):
        block = m.group(1)
        if "Yönetmen" in block:
            return _dark_grey_links(block)
    return []


def _parse_cast(card: str) -> list[str]:
    """Cast names: .meta-body-actor spans, then /sanatcilar/ links,
    deduped, first 5."""
    names: list[str] = []
    actor = _meta_block(card, "meta-body-actor")
    for name in _dark_grey_links(actor):
        if name not in names:
            names.append(name)
    for name in re.findall(
        r'/sanatcilar/sanatci-\d+/[^>]*>([^<]+)</a>', card
    ):
        name = _clean(name)
        if name and name not in names:
            names.append(name)
    return names[:5]


def city_geocode(city: str) -> str | None:
    """City name (Turkish, any case/diacritics-insensitive) or numeric
    geocode -> geocode, or None when unknown."""
    city = city.strip()
    if not city:
        return None
    if re.fullmatch(r"\d+", city) and city in CITIES:
        return city
    folded = _fold(city)
    for code, name in CITIES.items():
        if _fold(name) == folded:
            return code
    return None


def parse_now_showing(page_html: str) -> list[dict]:
    """Films currently in cinemas, in page order.

    Each film: film_id, title, release_date, duration_minutes,
    genres, director, cast, poster, url."""
    films: list[dict] = []
    starts = [m.start() for m in
              re.finditer(r'<li class="mdl[^"]*"', page_html)]
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(page_html)
        card = page_html[start:end]
        id_m = re.search(r"/filmler/film-(\d+)/", card)
        if not id_m:
            continue
        film_id = id_m.group(1)
        title_m = re.search(
            r'<a class="meta-title-link"[^>]*>([^<]+)</a>', card
        )
        info = _info_block(card)
        poster_m = re.search(
            r'<img class="thumbnail-img"[^>]*>', card
        )
        poster = None
        if poster_m:
            img = poster_m.group(0)
            data_src = re.search(r'data-src="([^"]+)"', img)
            src = re.search(r'(?<!data-)src="([^"]+)"', img)
            candidate = (
                data_src.group(1) if data_src else
                (src.group(1) if src else None)
            )
            if candidate and "data:image/gif" not in candidate:
                poster = candidate
        films.append({
            "film_id": film_id,
            "title": _clean(title_m.group(1)) if title_m else None,
            "release_date": _parse_date_span(info),
            "duration_minutes": _parse_duration(info),
            "genres": _dark_grey_links(info),
            "director": _parse_director(card),
            "cast": _parse_cast(card),
            "poster": poster,
            "url": f"{BASE}/filmler/film-{film_id}/",
        })
    return films


def parse_autocomplete(payload: dict) -> list[dict]:
    """Movie results from the /_/autocomplete/movie/<query> JSON.

    Keeps only entity_type == "movie". Each result: film_id, title,
    original_title, year, director, first_release, last_release,
    genres, viewcount, poster, url."""
    results = []
    if not isinstance(payload, dict) or payload.get("error"):
        return results
    for r in payload.get("results") or []:
        if r.get("entity_type") != "movie":
            continue
        data = r.get("data") or {}
        film_id = str(r.get("entity_id") or data.get("id") or "")
        if not film_id:
            continue
        results.append({
            "film_id": film_id,
            "title": r.get("label"),
            "original_title": r.get("original_label"),
            "year": data.get("year"),
            "director": data.get("director_name") or [],
            "first_release": data.get("first_release"),
            "last_release": data.get("last_release") or r.get("last_release"),
            "genres": r.get("genres") or [],
            "viewcount": r.get("viewcount"),
            "poster": data.get("thumbnail"),
            "url": f"{BASE}/filmler/film-{film_id}/",
        })
    return results


def _og(html_text: str, prop: str) -> str | None:
    m = re.search(
        r'<meta property="og:' + re.escape(prop) +
        r'" content="([^"]*)"',
        html_text,
    )
    return _clean(m.group(1)) if m else None


def parse_movie(page_html: str) -> dict:
    """One film's detail page.

    Returns {film_id, title, synopsis, release_date,
    duration_minutes, genres, director, cast, poster, ratings, url}
    — ratings is {} when the film has no ratings yet. Empty {} when
    the page is not a film page (e.g. a 404)."""
    title = _og(page_html, "title")
    if not title:
        return {}
    synopsis = _og(page_html, "description") or ""
    if synopsis.startswith("Özet: "):
        synopsis = synopsis[len("Özet: "):]
    id_m = re.search(r"/filmler/film-(\d+)/", page_html)
    # The page links other films too (header, recommendations) — the
    # film's own id is by far the most frequent one on its page.
    ids = re.findall(r"/filmler/film-(\d+)/", page_html)
    film_id = (
        max(set(ids), key=ids.count) if ids else None
    )
    info = _info_block(page_html)
    ratings: dict[str, dict] = {}
    for m in re.finditer(r'<div class="rating-item">', page_html):
        block = page_html[m.start():m.start() + 1500]
        title_m = re.search(r'rating-title[^>]*>([^<]*)<', block)
        note_m = re.search(r'stareval-note[^>]*>([^<]*)<', block)
        review_m = re.search(
            r'stareval-review[^>]*>([^<]*)<', block
        )
        if not title_m or not note_m:
            continue
        note_raw = _clean(note_m.group(1))
        if not re.fullmatch(r"\d+,\d+", note_raw):
            continue  # "--" or empty: no rating yet
        ratings[_clean(title_m.group(1))] = {
            "note": float(note_raw.replace(",", ".")),
            "review": _clean(review_m.group(1)) if review_m else None,
        }
    return {
        "film_id": film_id,
        "title": title,
        "synopsis": synopsis or None,
        "release_date": _parse_date_span(info),
        "duration_minutes": _parse_duration(info),
        "genres": _dark_grey_links(info),
        "director": _parse_director(page_html),
        "cast": _parse_cast(page_html),
        "poster": _og(page_html, "image"),
        "ratings": ratings,
        "url": (
            f"{BASE}/filmler/film-{film_id}/" if film_id else None
        ),
    }


def parse_showtimes(page_html: str) -> list[dict]:
    """Showtimes from a film's seanslar page (today only).

    Returns [{cinema_id, name, address, showtimes: [{date, version,
    time, datetime}]}] in page order; identical (date, version,
    time) triples are deduped per cinema. [] when the page has no
    cinemas (e.g. the 404 page for a wrong geocode)."""
    cinemas: list[dict] = []
    starts = [m.start() for m in
              re.finditer(r'<div class="theater-card[\s"]', page_html)]
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(page_html)
        card = page_html[start:end]
        name_m = re.search(
            r'<div class="meta-theater-title">.*?<a[^>]*>([^<]+)</a>',
            card, re.S,
        )
        if not name_m:
            continue
        id_m = re.search(r"/sinemalar/sinema-([A-Za-z0-9]+)/", card)
        addr_m = re.search(
            r'<address class="address[^"]*">(.*?)</address>', card, re.S
        )
        showtimes: list[dict] = []
        seen: set[tuple] = set()
        v_starts = [m.start() for m in
                    re.finditer(r'<div class="showtimes-version">', card)]
        for j, vstart in enumerate(v_starts):
            vend = (v_starts[j + 1] if j + 1 < len(v_starts)
                    else len(card))
            vblock = card[vstart:vend]
            text_m = re.search(
                r'<div class="text">\s*(.*?)\s*</div>', vblock, re.S
            )
            date = version = None
            if text_m:
                text = _clean(text_m.group(1))
                if " - " in text:
                    date, version = (p.strip() for p in
                                     text.split(" - ", 1))
                else:
                    date = text
            for h in re.finditer(
                r'<span[^>]*class="[^"]*showtimes-hour-item[^"]*"[^>]*'
                r'data-showtime-time="([^"]+)"[^>]*>.*?'
                r'<span class="showtimes-hour-item-value">([^<]+)</span>',
                vblock, re.S,
            ):
                key = (date, version, h.group(2).strip())
                if key in seen:
                    continue
                seen.add(key)
                showtimes.append({
                    "date": date,
                    "version": version,
                    "time": h.group(2).strip(),
                    "datetime": h.group(1),
                })
        cinemas.append({
            "cinema_id": id_m.group(1) if id_m else None,
            "name": _clean(name_m.group(1)),
            "address": _strip_tags(addr_m.group(1)) if addr_m else None,
            "showtimes": showtimes,
        })
    return cinemas


def parse_news(page_html: str) -> list[dict]:
    """Latest film news from /haberler/filmler/, deduped by id.

    Each item: news_id, title, url."""
    items: list[dict] = []
    seen: set[str] = set()
    for m in re.finditer(
        r'/haberler/filmler/haberler-(\d+)/"[^>]*>(.*?)</a>',
        page_html, re.S,
    ):
        news_id = m.group(1)
        title = _strip_tags(m.group(2))
        if news_id in seen or not title:
            continue
        seen.add(news_id)
        items.append({
            "news_id": news_id,
            "title": title,
            "url": f"{BASE}/haberler/filmler/haberler-{news_id}/",
        })
    return items


def parse_cities(page_html: str) -> list[dict]:
    """Cities from /sinemalar/ region links, plus any embedded-map
    entries missing from the page (the 4 Northern-Cyprus cities and
    any others the page omits).

    Returns [{geocode, name}] in page order, then the appended ones.
    Falls back to the embedded map when the page carries no links."""
    cities: list[dict] = []
    seen: set[str] = set()
    for code, name in re.findall(
        r'/sinemalar/bolgeye/(\d+)/"[^>]*>([^<]+)<', page_html
    ):
        name = _clean(name)
        if code and name and code not in seen:
            seen.add(code)
            cities.append({"geocode": code, "name": name})
    if not cities:
        return [{"geocode": c, "name": n} for c, n in CITIES.items()]
    for code, name in CITIES.items():
        if code not in seen:
            seen.add(code)
            cities.append({"geocode": code, "name": name})
    return cities
