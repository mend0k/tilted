"""PHD Games — public JSON API, no account needed.

Pulls the "Pre-Orders Due" list filtered to Trading Card Games.
"""

import json
import urllib.request
from datetime import datetime

API = ("https://api.phdgames.com/api/Product/FilterProducts"
       "?page={page}&limit=100&sortField=preOrderDate&sortOrder=asc"
       "&specialsOnly=false&listName=PreOrdersDue&searchType=null")
CATEGORIES_API = "https://api.phdgames.com/api/Category/ListSidenavItems"
CATEGORY = "Trading Card Games"


def _api(url, body=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode() if body is not None else None,
        method="POST" if body is not None else "GET",
        headers={"Content-Type": "application/json",
                 "User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def _attr(product, name):
    for a in product.get("attributes") or []:
        if a.get("name") == name:
            return a.get("formattedValue") or a.get("value") or ""
    return ""


def _date(iso):
    return datetime.fromisoformat(iso).strftime("%m/%d/%Y") if iso else ""


def fetch_preorders(category=CATEGORY):
    body = {}
    if category:
        cats = {c["name"].lower(): c for c in _api(CATEGORIES_API)}
        cat = cats[category.lower()]
        body = {"CategoryFilter": [{"id": cat["id"], "name": cat["name"],
                                    "value": None, "filterType": "category",
                                    "checked": True, "isSystem": False}]}
    items, page, total = [], 1, None
    while total is None or len(items) < total:
        data = _api(API.format(page=page), body)
        total = data["totalRecords"]
        batch = data.get("ProductViewModels") or []
        if not batch:
            break
        for p in batch:
            items.append({
                "sku": p.get("id", ""),
                "name": p.get("name", ""),
                "manufacturer": _attr(p, "Manufacturer"),
                "categories": p.get("categoryDelimitedList") or "",
                "msrp": p.get("msrpPrice"),
                "price": p.get("newPrice"),
                "release_date": _date(p.get("releaseDate") or ""),
                "preorder_date": _date(p.get("preOrderDate") or ""),
                "upc": _attr(p, "UPC Code"),
                "distributor": "PHD",
            })
        page += 1
    return items
