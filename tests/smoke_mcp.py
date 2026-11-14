"""MCP stdio smoke: spawn the server as a real MCP client would and
call all seven tools live (fast GETs only).

Run: python tests/smoke_mcp.py

The MCP stdio client spawns the server with a MINIMAL environment
(HOME, LOGNAME, PATH, SHELL, TERM, USER only). On this VM, outbound
HTTPS goes through an egress proxy, so the proxy/CA variables must
be passed explicitly or the server's requests are reset mid-TLS
(curl 35). This script forwards just those variables from the
current process environment (values are never written to the repo);
on a normal machine with direct internet they are simply absent
and the server works without them.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

_PROXY_VARS = (
    "https_proxy", "HTTPS_PROXY", "http_proxy", "HTTP_PROXY",
    "CURL_CA_BUNDLE", "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE",
    "no_proxy", "NO_PROXY",
)

CIRKO = "1000013643"


async def main() -> int:
    env = {k: os.environ[k] for k in _PROXY_VARS if k in os.environ}
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "beyazperde_mcp.server"],
        env=env or None,
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as s:
            await s.initialize()
            tools = await s.list_tools()
            names = [t.name for t in tools.tools]
            print("tools:", names)
            for expected in (
                "beyazperde_now_showing", "beyazperde_search_movies",
                "beyazperde_get_movie", "beyazperde_showtimes",
                "beyazperde_latest_news", "beyazperde_list_cities",
                "beyazperde_health",
            ):
                assert expected in names, expected

            async def call(name, args):
                r = await s.call_tool(name, args)
                d = json.loads(r.content[0].text)
                assert "error" not in d, (name, d)
                return d

            d = await call("beyazperde_now_showing", {"limit": 3})
            print(f"now_showing: {d['count']}, "
                  f"first={d['films'][0]['title']!r}")
            assert d["count"] >= 1
            d = await call("beyazperde_search_movies",
                           {"query": "dune", "limit": 3})
            print(f"search 'dune': {d['count']}, "
                  f"first={d['results'][0]['title']!r}")
            assert d["count"] >= 1
            d = await call("beyazperde_get_movie", {"film_id": CIRKO})
            print(f"get_movie {CIRKO}: {d['title']!r}, "
                  f"genres={d['genres']}")
            assert d["title"] == "Çirko"
            d = await call("beyazperde_showtimes",
                           {"film_id": CIRKO, "city": "İstanbul",
                            "limit_cinemas": 2})
            with_times = [c for c in d["cinemas"] if c["showtimes"]]
            print(f"showtimes {CIRKO} İstanbul: {d['count']} cinemas, "
                  f"{len(with_times)} with times, "
                  f"first={with_times[0]['name']!r} "
                  f"{[t['time'] for t in with_times[0]['showtimes'][:3]]}")
            assert with_times
            d = await call("beyazperde_latest_news", {"limit": 2})
            print(f"news: {d['count']}, first={d['news'][0]['title']!r}")
            assert d["count"] >= 1
            d = await call("beyazperde_list_cities", {})
            print(f"cities: {d['count']}")
            assert d["count"] == 85, d
            d = await call("beyazperde_health", {})
            print("health:", d["status"])
            assert d["status"] == "ok", d
    print("MCP stdio smoke: OK")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
