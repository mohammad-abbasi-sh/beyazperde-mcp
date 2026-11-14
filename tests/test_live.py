"""Live tests for beyazperde_mcp — real requests to beyazperde.com.

Requires network. Run:
    python -m unittest discover -s tests -v

Film listings rotate, so tests assert structure and sane ranges, not
exact listings — except the pinned Çirko checks (a film released
13 Kasım 2026; if it leaves cinemas, the showtimes test will need a
new pinned film from the live now-showing list).
"""
import unittest

from beyazperde_mcp import beyazperde as B
from beyazperde_mcp import http as H

CIRKO = "1000013643"  # Çirko, released 13 Kasım 2026


class TestLiveNowShowing(unittest.TestCase):
    def test_now_showing(self):
        films = B.parse_now_showing(H.fetch_now_showing())
        self.assertGreater(len(films), 0)
        self.assertLessEqual(len(films), 13)
        for film in films:
            self.assertTrue(film["film_id"] and film["title"])
            self.assertTrue(film["url"].endswith("/"))

    def test_search_dune(self):
        results = B.parse_autocomplete(H.search_autocomplete("dune"))
        self.assertGreater(len(results), 0)
        titles = [r["title"] or "" for r in results]
        self.assertTrue(any("Dune" in t for t in titles), titles)
        for r in results:
            self.assertTrue(r["film_id"] and r["title"])

    def test_search_no_results(self):
        results = B.parse_autocomplete(
            H.search_autocomplete("zzzqqqxxyyww"))
        self.assertEqual(results, [])


class TestLiveMovie(unittest.TestCase):
    def test_cirko(self):
        m = B.parse_movie(H.fetch_movie(CIRKO))
        self.assertEqual(m["film_id"], CIRKO)
        self.assertEqual(m["title"], "Çirko")
        self.assertTrue(m["synopsis"])
        self.assertEqual(m["genres"], ["Animasyon"])
        self.assertTrue(m["director"])
        self.assertIsInstance(m["ratings"], dict)

    def test_bogus_film(self):
        # A bogus film id is a real HTTP 404 on the site.
        with self.assertRaises(H.BeyazperdeError):
            H.fetch_movie("99999999999")


class TestLiveShowtimes(unittest.TestCase):
    def test_cirko_istanbul(self):
        cinemas = B.parse_showtimes(
            H.fetch_showtimes(CIRKO, "154167"))
        self.assertGreater(len(cinemas), 0)
        with_times = [c for c in cinemas if c["showtimes"]]
        self.assertGreater(len(with_times), 0)
        for c in with_times:
            for s in c["showtimes"]:
                self.assertRegex(s["time"], r"^\d{2}:\d{2}$")
                self.assertTrue(s["datetime"])

    def test_wrong_geocode_empty(self):
        # A wrong geocode is HTTP 200 live with an empty showtimes
        # page (the fixture seans_ist.html is the site's 404 body).
        html_text = H.fetch_showtimes(CIRKO, "999999")
        self.assertEqual(B.parse_showtimes(html_text), [])


class TestLiveNewsCitiesHealth(unittest.TestCase):
    def test_news(self):
        items = B.parse_news(H.fetch_news())
        self.assertGreater(len(items), 0)
        self.assertTrue(items[0]["news_id"] and items[0]["title"])

    def test_cities(self):
        cities = B.parse_cities(H.fetch_cinemas_page())
        self.assertEqual(len(cities), 85)
        by_code = {c["geocode"]: c["name"] for c in cities}
        self.assertEqual(by_code["154167"], "İstanbul")

    def test_health(self):
        health = H.health_check()
        self.assertEqual(health["status"], "ok", health)
        self.assertEqual(health["http_status"], 200)


if __name__ == "__main__":
    unittest.main()
