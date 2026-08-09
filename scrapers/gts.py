"""GTS Distribution — public CSV export, no account needed.

The catalog search page exposes a CSV download (downloadsearch=1) that
includes wholesale price (cust_price), SRP, order_due_date and release
date, all without login. We pull the Card Games category and keep items
whose order-due date is today or later ("pre-orders due").
"""

import csv
import io
import urllib.request
from datetime import date, datetime

CARD_GAMES_FACET = "04552AD14A72447B95ECFC368E1CB6BD"
CSV_URL = ("https://www.gtsdistribution.com/pc_combined_results.asp"
           "?pc_id=&search_keyword=&opts="
           f"&faceted_search_terms=Category~{CARD_GAMES_FACET}"
           "&downloadsearch=1")


def _date(s):
    s = (s or "").strip()
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def _fmt(d):
    return d.strftime("%m/%d/%Y") if d else ""


def _num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def fetch_preorders():
    req = urllib.request.Request(CSV_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        text = resp.read().decode("utf-8", errors="replace")

    today = date.today()
    items = []
    for row in csv.DictReader(io.StringIO(text)):
        due = _date(row.get("order_due_date"))
        if due is None or due < today:
            continue
        items.append({
            "sku": (row.get("sku") or "").strip(),
            "name": (row.get("name") or "").strip(),
            "manufacturer": (row.get("Manufacturer") or "").strip(),
            "categories": (row.get("product_line") or "Card Games").strip(),
            "msrp": _num(row.get("SRP")),
            "price": _num(row.get("cust_price")),
            "release_date": _fmt(_date(row.get("release_date"))),
            "preorder_date": _fmt(due),
            "upc": (row.get("BARCODE1") or "").strip(),
            "distributor": "GTS Distribution",
        })
    items.sort(key=lambda i: i["preorder_date"])
    return items
