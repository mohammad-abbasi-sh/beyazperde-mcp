# beyazperde-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/beyazperde-mcp

سرور MCP غیررسمی و **فقط‌خواندنی** برای Beyazperde (سایت beyazperde.com) — پورتال پیشروی سینما در ترکیه (نسخهٔ ترکی AlloCiné). فیلم‌های در حال اکران را فهرست کنید، بر اساس عنوان جستجو کنید، جزئیات یک فیلم را بگیرید (خلاصه، تاریخ اکران، مدت، ژانرها، کارگردان، بازیگران، امتیاز اعضا/مطبوعات)، سانس‌های امروز یک فیلم را در هر یک از ۸۵ شهر ببینید و تازه‌ترین اخبار سینما را بخوانید.

> ساختهٔ محمد عباسی در چارچوب «کارخانهٔ MCP ترکیه» (خط تولید به سبک سپهر). وابسته به Beyazperde یا Webedia نیست.

**نکته:** سانس‌ها فقط برای **امروز** هستند — پارامتر تاریخ سایت، پاسخ سرور را تغییر نمی‌دهد (فیلتر تاریخ سمت کاربر انجام می‌شود). فیلم‌های جدید هنوز امتیازی ندارند (`ratings: {}`). سایت ترکی‌زبان است؛ عنوان‌ها، ژانرها و خلاصه‌ها به ترکی برگردانده می‌شوند. جستجوی فیلم از نقطهٔ پایانی JSON تکمیل خودکار سایت استفاده می‌کند — صفحهٔ جستجوی خود سایت هیچ نتیجه‌ای در سمت سرور تولید نمی‌کند.

## برای ایجنت‌های هوش مصنوعی

به پیکربندی کلاینت MCP خود اضافه کنید (stdio):

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

یا به‌صورت محلی اجرا کنید: `python -m beyazperde_mcp.server` (نیازمند `mcp<2` و `httpx>=0.27`).

## ابزارها

| ابزار | توضیح |
|------|----------|
| `beyazperde_now_showing` | فیلم‌های در حال اکران — `limit` از ۱ تا ۱۳؛ هر فیلم: film_id، title، release_date، duration_minutes، genres، director، cast (۵ نفر اول)، poster، url |
| `beyazperde_search_movies` | جستجوی فیلم بر اساس عنوان — `query` (مثلاً "dune" یا "Çirko")، `limit` از ۱ تا ۱۰؛ هر نتیجه: film_id، title، original_title، year، director، first_release، last_release، genres، viewcount، poster، url |
| `beyazperde_get_movie` | جزئیات یک فیلم — `film_id` (مثلاً "1000013643" برای Çirko): title، synopsis، release_date، duration_minutes، genres، director، cast، poster، ratings |
| `beyazperde_showtimes` | سانس‌های امروز یک فیلم در یک شهر — `film_id`، نام شهر یا geocode (پیش‌فرض "İstanbul")، `limit_cinemas` از ۱ تا ۲۰؛ هر سینما: cinema_id، name، address، showtimes با [{date, version, time, datetime}] |
| `beyazperde_latest_news` | تازه‌ترین اخبار سینما — `limit` از ۱ تا ۱۰؛ هر خبر: news_id، title، url |
| `beyazperde_list_cities` | ۸۵ شهر دارای سانس — geocode و نام (مثلاً "154167" استانبول)، شامل ۴ شهر قبرس شمالی |
| `beyazperde_health` | بررسی در دسترس بودن Beyazperde (ok / blocked / error) |

خروجی نمونه (`beyazperde_showtimes` / فیلم Çirko، استانبول، ۲۰۲۶-۱۱-۱۴):

```json
{"film_id": "1000013643", "city": "İstanbul", "geocode": "154167",
 "count": 30,
 "cinemas": [{"cinema_id": "T0211", "name": "City’s Nişantaşı – CINEWAM Premium",
  "address": "Tesvikiye Cad. No:192 K:6 34365 Sisli",
  "showtimes": [{"date": "14 Kasım 2026", "version": "Türkçe Dublajlı",
   "time": "11:00", "datetime": "2026-11-14T11:00:00+03:00"}]}]}
```

## نحوهٔ کار

همه‌چیز درخواست‌های سادهٔ HTTP GET به beyazperde.com با User-Agent کروم است (بدون دیوار ربات، بدون ورود، بدون کلید API — تأییدشده در ۲۰۲۶-۱۱-۱۴). فیلم‌های در حال اکران: `/filmler/vizyondakiler/sinema-sayisi/` (کارت‌های `li.mdl > div.card.entity-card`)؛ جستجو: نقطهٔ پایانی JSON تکمیل خودکار `/_/autocomplete/movie/<query>` (فقط `entity_type == "movie"` نگه داشته می‌شود)؛ جزئیات فیلم: `/filmler/film-<id>/` (‏og:title / ‏og:description / ‏og:image، تاریخ/مدت/ژانرها از `.meta-body-info`، امتیازها از بلوک‌های `.rating-item`)؛ سانس‌ها: `/filmler/film-<id>/seanslar/civarinda-<geocode>/` (بلوک‌های `.theater-card`، سه‌تایی‌های تکراری (date, version, time) حذف می‌شوند — صفحه ساعت‌ها را در بلوک‌های تکراری نسخه تکرار می‌کند)؛ اخبار: `/haberler/filmler/` (حذف تکراری بر اساس id)؛ شهرها: پیوندهای منطقه در `/sinemalar/` به‌علاوهٔ ۴ شهر قبرس شمالی از نقشهٔ داخلی ۸۵ شهر (تجزیه‌شده از انتخاب‌گر شهر صفحهٔ سانس‌ها، ۲۰۲۶-۱۱-۱۴). geocode اشتباه صفحهٔ ۴۰۴ سایت را برمی‌گرداند، پس شهرها پیش از درخواست اعتبارسنجی می‌شوند. درخواست‌ها با فاصلهٔ حدود ۰٫۵ ثانیه انجام می‌شوند؛ همه‌چیز فقط‌خواندنی است.

## نصب

```bash
uvx beyazperde-mcp==0.1.0   # اجرای مستقیم (نیازمند uv)
# یا
pip install beyazperde-mcp==0.1.0
beyazperde-mcp    # سرور MCP را روی stdio راه می‌اندازد
```

## آزمون‌ها

```bash
python -m venv .venv && .venv/bin/pip install -e .
.venv/bin/python -m unittest discover -s tests -v
```

آزمون‌های آفلاین روی نمونه‌های ضبط‌شده اجرا می‌شوند (صفحات واقعی در ۲۰۲۶-۱۱-۱۴ گرفته شده‌اند)؛ آزمون‌های زنده به beyazperde.com درخواست می‌زنند (بررسی ساختار/بازه، بدون مقدار دقیق). آزمون‌ها در زمان ساخت سبز هستند (برای شمارش به مخزن نگاه کنید) به‌علاوهٔ یک آزمون دود stdio از نوع MCP.

## نقشهٔ راه

- سانس برای تاریخ انتخاب‌شده (پس از درک فیلتر تاریخ سمت کاربر سایت)
- فیلم‌های به‌زودی در راه (`/filmler/yakinda/`)
- پیوند تریلر / ویدیو برای هر فیلم

## مجوز

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/) — نگاه کنید به [LICENSE](LICENSE).

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
