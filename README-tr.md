# beyazperde-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/beyazperde-mcp

Beyazperde (beyazperde.com) için resmi olmayan, **salt okunur** MCP sunucusu — Türkiye'nin önde gelen sinema portalı (Türkiye'nin AlloCiné'si). Vizyondaki filmleri listeleyin, başlığa göre film arayın, bir filmin ayrıntısını alın (özet, vizyon tarihi, süre, türler, yönetmen, oyuncular, üye/basın puanları), 85 şehirden birinde bir filmin bugünkü seanslarını listeleyin ve en son sinema haberlerini okuyun.

> Mohammad Abbasi tarafından "Turkey MCP factory" (Sepehr tarzı hat) kapsamında geliştirildi. Beyazperde veya Webedia ile bağlantısı yoktur.

**Not:** seanslar yalnızca **bugün** içindir — sitenin tarih parametresi sunucu yanıtını değiştirmez (tarih filtreleme istemci tarafında yapılır). Yeni filmlerin henüz puanı yoktur (`ratings: {}`). Site Türkçedir; başlıklar, türler ve özetler Türkçe döner. Film araması, sitenin otomatik tamamlama JSON uç noktasını kullanır — sitenin kendi arama sayfası sunucu tarafında sonuç üretmez.

## Yapay zekâ ajanları için

MCP istemci yapılandırmanıza ekleyin (stdio):

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

Ya da yerel çalıştırın: `python -m beyazperde_mcp.server` (`mcp<2`, `httpx>=0.27` gerekir).

## Araçlar

| Araç | Açıklama |
|------|----------|
| `beyazperde_now_showing` | Vizyondaki filmler — `limit` 1..13; her film: film_id, title, release_date, duration_minutes, genres, director, cast (ilk 5), poster, url |
| `beyazperde_search_movies` | Başlığa göre film arama — `query` (örn. "dune", "Çirko"), `limit` 1..10; her sonuç: film_id, title, original_title, year, director, first_release, last_release, genres, viewcount, poster, url |
| `beyazperde_get_movie` | Bir filmin ayrıntısı — `film_id` (örn. Çirko için "1000013643"): title, synopsis, release_date, duration_minutes, genres, director, cast, poster, ratings |
| `beyazperde_showtimes` | Bir filmin bir şehirdeki bugünkü seansları — `film_id`, `city` adı veya geocode (varsayılan "İstanbul"), `limit_cinemas` 1..20; her sinema: cinema_id, name, address, showtimes [{date, version, time, datetime}] |
| `beyazperde_latest_news` | En son sinema haberleri — `limit` 1..10; her haber: news_id, title, url |
| `beyazperde_list_cities` | Seans listelenen 85 şehir — geocode + ad (örn. "154167" İstanbul), 4 Kuzey Kıbrıs şehri dahil |
| `beyazperde_health` | Beyazperde'ye erişilip erişilemediğini kontrol eder (ok / blocked / error) |

Örnek çıktı (`beyazperde_showtimes` / Çirko, İstanbul, 2026-11-14):

```json
{"film_id": "1000013643", "city": "İstanbul", "geocode": "154167",
 "count": 30,
 "cinemas": [{"cinema_id": "T0211", "name": "City’s Nişantaşı – CINEWAM Premium",
  "address": "Tesvikiye Cad. No:192 K:6 34365 Sisli",
  "showtimes": [{"date": "14 Kasım 2026", "version": "Türkçe Dublajlı",
   "time": "11:00", "datetime": "2026-11-14T11:00:00+03:00"}]}]}
```

## Nasıl çalışır

Her şey, Chrome kullanıcı aracısıyla beyazperde.com'a düz HTTP GET istekleridir (bot duvarı yok, giriş yok, API anahtarı yok — 2026-11-14'te doğrulandı). Vizyondakiler: `/filmler/vizyondakiler/sinema-sayisi/` (`li.mdl > div.card.entity-card` kartları); arama: `/_/autocomplete/movie/<sorgu>` otomatik tamamlama JSON uç noktası (yalnızca `entity_type == "movie"` tutulur); film ayrıntısı: `/filmler/film-<id>/` (og:title / og:description / og:image, tarih/süre/türler için `.meta-body-info`, puanlar için `.rating-item` blokları); seanslar: `/filmler/film-<id>/seanslar/civarinda-<geocode>/` (`.theater-card` blokları, aynı (date, version, time) üçlüleri tekilleştirilir — sayfa saatleri yinelenen sürüm bloklarında tekrarlar); haberler: `/haberler/filmler/` (id'ye göre tekilleştirilir); şehirler: `/sinemalar/` bölge bağlantıları + gömülü 85 şehirlik geocode haritasından 4 Kuzey Kıbrıs kaydı (seans sayfasının şehir seçicisinden ayrıştırıldı, 2026-11-14). Yanlış geocode sitenin 404 sayfasını döndürür, bu yüzden şehirler istekten önce doğrulanır. İstekler ~0,5 sn arayla yapılır; her şey salt okunurdur.

## Kurulum

```bash
uvx beyazperde-mcp==0.1.0   # doğrudan çalıştır (uv gerekir)
# veya
pip install beyazperde-mcp==0.1.0
beyazperde-mcp    # MCP sunucusunu stdio üzerinde başlatır
```

## Testler

```bash
python -m venv .venv && .venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests -v
```

Çevrimdışı testler kaydedilmiş örneklerle çalışır (gerçek sayfalar 2026-11-14'te alındı); canlı testler beyazperde.com'a istek atar (yapı/aralık doğrulamaları, kesin değer yok). Derleme anında testler yeşildir (sayılar için repoya bakın) ve bir MCP stdio duman testi vardır.

## Yol haritası

- Seçilen bir tarih için seanslar (sitenin istemci tarafı tarih filtrelemesi anlaşılınca)
- Yakında vizyona girecek filmler (`/filmler/yakinda/`)
- Film başına fragman / video bağlantıları

## Lisans

MIT — bkz. [LICENSE](LICENSE).

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
