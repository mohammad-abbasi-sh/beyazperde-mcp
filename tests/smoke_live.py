"""Daily live smoke for beyazperde_mcp — one fixed probe of
beyazperde.com (health + now showing + cities). Fast GETs only; the
showtimes page is NOT used here.

Run: python tests/smoke_live.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from beyazperde_mcp import beyazperde as B
from beyazperde_mcp import http as H


def main() -> int:
    health = H.health_check()
    print("health:", health)
    assert health["status"] == "ok", health
    films = B.parse_now_showing(H.fetch_now_showing())
    print(f"now showing: {len(films)}, first={films[0]['title']!r}")
    assert len(films) >= 1
    cities = B.parse_cities(H.fetch_cinemas_page())
    print(f"cities: {len(cities)}")
    assert len(cities) == 85, cities
    print("smoke live: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
