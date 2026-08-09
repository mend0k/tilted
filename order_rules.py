"""Rules for deciding how many of each item to add to the cart.

Edit this file to tune ordering logic. Rules are checked top-to-bottom;
the first rule whose `match` returns True wins. If nothing matches,
DEFAULT_QTY is used.

Each item dict has: sku, name, manufacturer, categories, msrp, price,
release_date, preorder_date, upc, distributor.
"""

DEFAULT_QTY = 3

# Each rule: (label, match_function, quantity)
# Examples are commented out — uncomment/add as the logic evolves.
RULES = [
    # ("Skip organized play kits", lambda i: "Organized Play Kit" in i["name"], 0),
    # ("Heavy on MTG boosters",    lambda i: "MTG" in i["name"] and "Booster Display" in i["name"], 6),
    # ("Light on big-ticket",      lambda i: (i["price"] or 0) > 200, 1),
]


def decide_qty(item):
    """Return the cart quantity for one item."""
    for label, match, qty in RULES:
        try:
            if match(item):
                return qty
        except Exception:
            continue
    return DEFAULT_QTY
