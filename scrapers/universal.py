"""Universal Distribution (Canada portal) — public JSON API, no account.

/api/v1/en/preorderproducts returns all current pre-orders grouped by
category code. Trading Card Games are the 2000-series category codes.
Pricing is not available logged-out (left blank).
"""

import json
import urllib.request
from datetime import date, datetime

BASE = "https://universaldistribution.ca/api/v1/en"
PREORDERS_URL = f"{BASE}/preorderproducts?limit=500"
CATEGORIES_URL = f"{BASE}/itemcategories"
TCG_PARENT_PREFIX = "2"  # 2000-series = Trading Card Games


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def _fmt(iso):
    if not iso:
        return ""
    try:
        return datetime.strptime(iso[:10], "%Y-%m-%d").strftime("%m/%d/%Y")
    except ValueError:
        return ""


def fetch_preorders(tcg_only=True):
    try:
        cat_names = {c.get("code"): c.get("description", "")
                     for c in _get(CATEGORIES_URL)}
    except Exception:
        cat_names = {}

    items = []
    for group in _get(PREORDERS_URL):
        code = str(group.get("category", ""))
        if tcg_only and not code.startswith(TCG_PARENT_PREFIX):
            continue
        for p in group.get("products") or []:
            due = (p.get("customerOrderDue") or "")[:10]
            try:
                if datetime.strptime(due, "%Y-%m-%d").date() < date.today():
                    continue  # deadline already passed
            except ValueError:
                pass  # keep items with no/invalid deadline
            items.append({
                "sku": p.get("itemCode", ""),
                "name": p.get("productName", ""),
                "manufacturer": p.get("manufacturer", ""),
                "categories": cat_names.get(code, code),
                "msrp": None,   # pricing requires dealer login
                "price": None,
                "release_date": _fmt(p.get("releaseDate")),
                "preorder_date": _fmt(p.get("customerOrderDue")),
                "upc": p.get("sku", ""),
                "distributor": "Universal Distribution",
            })
    items.sort(key=lambda i: i["preorder_date"])
    return items
