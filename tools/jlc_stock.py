#!/usr/bin/env python3
"""Query the JLCPCB assembly-parts pool for LCSC numbers or MPNs.

Usage:
    python tools/jlc_stock.py C16251 C58940 USB2514B-AEZC-TR
    python tools/jlc_stock.py --all INA190      # list every hit, not only exact ones

Prints a Markdown table (query, LCSC number, MPN, brand, package, JLCPCB
assembly stock, part class, check date). Exit status: 0 = every query matched
exactly; 1 = at least one query had no exact match; 2 = the API could not be
reached or answered with an error.

Exact match means: a query of the form ``C<digits>`` must equal the LCSC
number; any other query must equal the MPN, case-insensitively. ``--all``
disables matching and lists the search hits, for discovering candidates.

What this tool sees: the JLCPCB *assembly-parts* catalogue
(``selectSmtComponentList``), the same pool the PCBA order draws from, at the
moment of the query. CLAUDE.md Section 4.1 and easy-stick lesson 14.8: this is
the authoritative pool; LCSC retail stock is a different pool.

What this tool CANNOT see (CLAUDE.md Section 8 — a checker only proves what it
looks at):
- whether a part meets any electrical requirement — that needs the datasheet;
- whether the stock will still be there at upload or payment — recheck then;
- the inventory reserved or shown inside a specific PCBA order or quote;
- whether the footprint, pin numbering, or 3D model in any library is right;
- price breaks, setup fees, or lifecycle (NRND/EOL) status.

Negative test, run before relying on it (2026-11-03):
    python tools/jlc_stock.py C999999999 NOSUCHPART-XYZ123   -> exit 1, "NO EXACT MATCH"
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import random
import re
import sys
import time
import urllib.error
import urllib.request

API = ("https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/"
       "smtGood/selectSmtComponentList")
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"),
}
MAX_ATTEMPTS = 3          # bounded retries; never an immediate retry loop
BASE_BACKOFF_S = 1.0      # exponential backoff with full jitter
REQUEST_SPACING_S = 0.6   # serial requests, spaced, to stay well inside any rate limit
TIMEOUT_S = 30
LCSC_RE = re.compile(r"^C\d+$", re.IGNORECASE)


class ApiError(RuntimeError):
    pass


def _post(keyword: str, page_size: int) -> list[dict]:
    body = json.dumps({"currentPage": 1, "pageSize": page_size,
                       "keyword": keyword}).encode()
    last: Exception | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        req = urllib.request.Request(API, data=body, headers=HEADERS, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            if payload.get("code") != 200:
                raise ApiError(f"API code {payload.get('code')}: {payload.get('message')}")
            info = (payload.get("data") or {}).get("componentPageInfo") or {}
            return info.get("list") or []
        except urllib.error.HTTPError as exc:
            last = exc
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            if exc.code not in (429, 500, 502, 503, 504) or attempt == MAX_ATTEMPTS:
                break
            if retry_after and retry_after.isdigit():
                delay = float(retry_after)
            else:
                delay = random.uniform(0, BASE_BACKOFF_S * 2 ** (attempt - 1))
            time.sleep(delay)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last = exc
            if attempt == MAX_ATTEMPTS:
                break
            time.sleep(random.uniform(0, BASE_BACKOFF_S * 2 ** (attempt - 1)))
    raise ApiError(f"query {keyword!r} failed after {MAX_ATTEMPTS} attempts: {last}")


def part_class(item: dict) -> str:
    if item.get("componentLibraryType") == "base":
        return "Basic"
    if item.get("preferredComponentFlag"):
        return "Preferred Extended"
    return "Extended"


def is_exact(query: str, item: dict) -> bool:
    if LCSC_RE.match(query):
        return (item.get("componentCode") or "").upper() == query.upper()
    return (item.get("componentModelEn") or "").casefold() == query.casefold()


def row(query: str, item: dict, date: str) -> str:
    cells = [query, item.get("componentCode") or "", item.get("componentModelEn") or "",
             item.get("componentBrandEn") or "", item.get("componentSpecificationEn") or "",
             str(item.get("stockCount", "")), part_class(item), date]
    return "| " + " | ".join(c.replace("|", "/") for c in cells) + " |"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("queries", nargs="+", help="LCSC numbers (C1234) or exact MPNs")
    ap.add_argument("--all", action="store_true",
                    help="list every search hit instead of requiring an exact match")
    ap.add_argument("--page-size", type=int, default=25)
    args = ap.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    date = dt.datetime.now(dt.timezone.utc).date().isoformat()
    print("| Query | LCSC | MPN | Brand | Package | JLCPCB stock | Class | Checked (UTC) |")
    print("|---|---|---|---|---|---:|---|---|")

    missing: list[str] = []
    for i, query in enumerate(args.queries):
        if i:
            time.sleep(REQUEST_SPACING_S)
        try:
            items = _post(query, args.page_size)
        except ApiError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        hits = items if args.all else [it for it in items if is_exact(query, it)]
        if not hits:
            missing.append(query)
            print(f"| {query} | — | NO EXACT MATCH | | | | | {date} |")
            continue
        for it in hits:
            print(row(query, it, date))

    if missing:
        print(f"\nNo exact match for: {', '.join(missing)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
