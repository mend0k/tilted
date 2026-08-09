"""Distributor scrapers.

Each scraper module exposes fetch_preorders() -> list[dict] with keys:
sku, name, manufacturer, categories, msrp, price, release_date,
preorder_date, upc, distributor.

Add a new distributor by creating scrapers/<key>.py and registering it here.
"""

from . import gts, phd, universal

SCRAPERS = {
    "phd": phd.fetch_preorders,
    "gts": gts.fetch_preorders,
    "universal": universal.fetch_preorders,
    # "magx": ...,     need site URL from Kevin
    # "acdd": ...,     feasible — RSC HTML parsing, next iteration
    # "southern": ..., feasible — category-page HTML parsing, next iteration
}
