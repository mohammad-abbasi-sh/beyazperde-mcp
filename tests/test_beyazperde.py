"""Offline tests for beyazperde_mcp — recorded fixtures (real pages
fetched 2026-11-14). No network.

Run: python -m unittest discover -s tests -v

Note: viz.html carries 13 <li class="mdl"> elements, but one is an
empty placeholder (<li class="mdl"> </li>), so 12 real films parse.
"""
import json
import unittest
from pathlib import Path

from beyazperde_mcp import beyazperde as B

FIX = Path(__file__).resolve().parent / "fixtures"


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8", errors="ignore")


class TestCities(unittest.TestCase):
    def test_embedded_map_85(self):
        self.assertEqual(len(B.CITIES), 85)
        self.assertEqual(B.CITIES["154167"], "İstanbul")
        self.assertEqual(B.CITIES["265185"], "Girne")
        self.assertEqual(B.CITIES["265187"], "Mağusa")

    def test_city_geocode(self):
        self.assertEqual(B.city_geocode("İstanbul"), "154167")
        self.assertEqual(B.city_geocode("154167"), "154167")
        self.assertEqual(B.city_geocode("istanbul"), "154167")
        self.assertEqual(B.city_geocode("IZMIR"), "154190")
        self.assertEqual(B.city_geocode("Izmir"), "154190")
        self.assertEqual(B.city_geocode("Ankara"), "154124")
        self.assertEqual(B.city_geocode("Girne"), "265185")
        self.assertIsNone(B.city_geocode("bogus"))
        self.assertIsNone(B.city_geocode(""))
        self.assertIsNone(B.city_geocode("999999"))


class TestDuration(unittest.TestCase):
    def test_parse_duration(self):
        self.assertEqual(B._parse_duration("1s 25dk"), 85)
        self.assertEqual(B._parse_duration("2s 5dk"), 125)
        self.assertIsNone(B._parse_duration("Komedi"))


class TestNowShowing(unittest.TestCase):
    def test_viz_12_films(self):
        films = B.parse_now_showing(_read("viz.html"))
        self.assertEqual(len(films), 12)
        first = films[0]
        self.assertEqual(first["film_id"], "1000048391")
        self.assertEqual(
            first["title"], "Çakallarla Dans 8: Şututgart Çıkarması"
        )
        self.assertEqual(first["release_date"], "6 Kasım 2026")
        self.assertEqual(first["duration_minutes"], 108)
        self.assertEqual(first["genres"], ["Komedi"])
        self.assertEqual(first["director"], ["Murat Şeker"])
        self.assertEqual(
            first["cast"],
            ["Şevket Çoruh", "Murat Akkoyunlu", "Didem Balçın"],
        )
        self.assertTrue(first["poster"].startswith("https://"))
        self.assertEqual(
            first["url"],
            "https://www.beyazperde.com/filmler/film-1000048391/",
        )
        for film in films:
            self.assertTrue(film["film_id"] and film["title"])
            self.assertLessEqual(len(film["cast"]), 5)

    def test_cirko_in_list(self):
        films = B.parse_now_showing(_read("viz.html"))
        cirko = [f for f in films if f["film_id"] == "1000013643"]
        self.assertEqual(len(cirko), 1)
        self.assertEqual(cirko[0]["title"], "Çirko")
        self.assertEqual(cirko[0]["duration_minutes"], 85)

    def test_empty_html(self):
        self.assertEqual(B.parse_now_showing(""), [])


class TestAutocomplete(unittest.TestCase):
    def test_dune(self):
        payload = json.loads(_read("ac_movie.json"))
        results = B.parse_autocomplete(payload)
        self.assertEqual(len(results), 10)
        first = results[0]
        self.assertEqual(first["film_id"], "133392")
        self.assertEqual(first["title"], "Dune:Çöl Gezegeni")
        self.assertEqual(first["original_title"], "Dune")
        self.assertEqual(first["year"], "2021")
        self.assertEqual(first["director"], ["Denis Villeneuve"])
        self.assertEqual(first["genres"], ["ScienceFiction", "Drama"])
        self.assertEqual(first["viewcount"], 616305)
        self.assertTrue(first["poster"].startswith("https://"))
        for r in results:
            self.assertTrue(r["film_id"] and r["title"])

    def test_error_payload(self):
        self.assertEqual(B.parse_autocomplete({"error": True}), [])
        self.assertEqual(B.parse_autocomplete({}), [])
        self.assertEqual(
            B.parse_autocomplete(
                {"error": False, "results": [
                    {"entity_type": "person", "entity_id": "1",
                     "label": "Someone"},
                    {"entity_type": "movie", "entity_id": "9",
                     "label": "Film", "data": {}},
                ]}
            ),
            [{
                "film_id": "9", "title": "Film", "original_title": None,
                "year": None, "director": [], "first_release": None,
                "last_release": None, "genres": [], "viewcount": None,
                "poster": None,
                "url": "https://www.beyazperde.com/filmler/film-9/",
            }],
        )


class TestMovie(unittest.TestCase):
    def test_cirko_no_ratings(self):
        m = B.parse_movie(_read("film.html"))
        self.assertEqual(m["film_id"], "1000013643")
        self.assertEqual(m["title"], "Çirko")
        self.assertTrue(m["synopsis"].startswith(
            "Tanıştığınız en sevimli köpeğin hikayesi"))
        self.assertNotIn("Özet:", m["synopsis"])
        self.assertEqual(m["release_date"], "13 Kasım 2026")
        self.assertEqual(m["duration_minutes"], 85)
        self.assertEqual(m["genres"], ["Animasyon"])
        self.assertEqual(m["director"], ["Jérémie Degruson", "Yanis Belaid"])
        self.assertEqual(
            m["cast"],
            ["Axel Auriant", "Washim Abdul Gafoor", "Olivier Chauvel"],
        )
        self.assertTrue(m["poster"].startswith("https://"))
        self.assertEqual(m["ratings"], {})

    def test_old_film_with_ratings(self):
        m = B.parse_movie(_read("film_old.html"))
        self.assertEqual(m["film_id"], "269691")
        self.assertEqual(m["title"], "Dijital Esaret")
        self.assertEqual(m["release_date"], "27 Mayıs 2022")
        self.assertIsNone(m["duration_minutes"])  # no duration on page
        self.assertEqual(m["genres"], ["Komedi"])
        self.assertEqual(m["director"], ["Emre Kavuk"])
        self.assertEqual(
            m["cast"],
            ["Rasim Öztekin", "Özgün Çoban", "Kaan Sevi", "Simay Barlas"],
        )
        self.assertEqual(m["ratings"], {
            "Üyeler": {"note": 2.7, "review": "14 Puanlama, 6 Eleştiri"},
        })

    def test_not_a_film_page(self):
        self.assertEqual(B.parse_movie("<html></html>"), {})
        self.assertEqual(B.parse_movie(""), {})


class TestShowtimes(unittest.TestCase):
    def test_place_deduped(self):
        cinemas = B.parse_showtimes(_read("seans_place.html"))
        self.assertEqual(len(cinemas), 30)
        first = cinemas[0]
        self.assertEqual(first["cinema_id"], "T0211")
        self.assertEqual(
            first["name"], "City’s Nişantaşı – CINEWAM Premium"
        )
        self.assertTrue(first["address"].startswith("Tesvikiye Cad."))
        # The page repeats 11:00/13:00/15:00/17:00 twice — deduped.
        self.assertEqual(
            [(s["date"], s["version"], s["time"])
             for s in first["showtimes"]],
            [("14 Kasım 2026", "Türkçe Dublajlı", "11:00"),
             ("14 Kasım 2026", "Türkçe Dublajlı", "13:00"),
             ("14 Kasım 2026", "Türkçe Dublajlı", "15:00"),
             ("14 Kasım 2026", "Türkçe Dublajlı", "17:00")],
        )
        self.assertEqual(
            first["showtimes"][0]["datetime"],
            "2026-11-14T11:00:00+03:00",
        )
        for c in cinemas:
            self.assertTrue(c["name"] and c["cinema_id"])

    def test_404_page_empty(self):
        self.assertEqual(B.parse_showtimes(_read("seans_ist.html")), [])
        self.assertEqual(B.parse_showtimes(""), [])


class TestNews(unittest.TestCase):
    def test_haber(self):
        items = B.parse_news(_read("haber.html"))
        self.assertEqual(len(items), 19)
        self.assertEqual(items[0]["news_id"], "1000232327")
        self.assertTrue(items[0]["title"].startswith(
            "Crystal Lake'de Kâbus Yeniden Başlıyor"))
        self.assertNotIn("&#039;", items[0]["title"])
        self.assertEqual(
            items[0]["url"],
            "https://www.beyazperde.com/haberler/filmler/haberler-1000232327/",
        )
        ids = [i["news_id"] for i in items]
        self.assertEqual(len(ids), len(set(ids)))  # deduped

    def test_empty(self):
        self.assertEqual(B.parse_news(""), [])


class TestCitiesPage(unittest.TestCase):
    def test_sinemalar_85(self):
        cities = B.parse_cities(_read("sinemalar.html"))
        self.assertEqual(len(cities), 85)
        by_code = {c["geocode"]: c["name"] for c in cities}
        self.assertEqual(by_code["154167"], "İstanbul")
        # The regions page omits the 4 Cyprus cities + Bingöl, İğdir,
        # Trabzon — appended from the embedded map.
        for name in ("Girne", "Güzelyurt", "Lefkoşe", "Mağusa",
                     "Bingöl", "İğdir", "Trabzon"):
            self.assertIn(name, by_code.values(), name)

    def test_fallback(self):
        cities = B.parse_cities("")
        self.assertEqual(len(cities), 85)


if __name__ == "__main__":
    unittest.main()
