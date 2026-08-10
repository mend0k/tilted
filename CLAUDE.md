# Tilted — Distributor Pre-Order Agent Harness

This project is an **agent harness**: Claude (in Claude Desktop / Claude Code)
does the pre-order run itself. The goal of a run:

1. Pull current "pre-orders due" items from every **enabled** distributor.
2. Add the right quantity of each item to the distributor's online cart.
3. Record what was actually added in the spreadsheet (`preorder_report.xlsx`).
4. Email a summary report.

The user starts this with **/start-preorder** (see `.claude/skills/`).

## Ground rules (always apply)

- **Stop at the cart. NEVER check out, place an order, or enter payment
  information.** Carting is reversible; ordering is not. If a site tries to
  force checkout to keep a cart, skip that site and report it.
- **Never enter credentials.** If a site needs a login, ask the user to log
  in themselves in the browser, then continue.
- **The workbook is the source of truth.** `preorder_report.xlsx`, one tab
  per distributor. Record real carted quantities in the yellow **Qty Added**
  column (via `record_qty.py`, not by hand-editing xlsx in Python inline).
  Never produce CSV files. Don't rename sheet tabs.
- **Quantities come from `order_rules.py`** (default 3). The Suggested Qty
  column in the workbook is already computed from it.
- **Install dependencies yourself; never make the user do it.** Before
  running any script, ensure `openpyxl` is present:
  `python3 -c "import openpyxl" 2>/dev/null || pip3 install -r requirements.txt`
  (fallbacks: `python3 -m pip install ...`, then `pip3 install --user ...`).
- Python here may be as old as 3.9 — no `X | Y` union type syntax.

## Key files

- `distributors.json` — registry. Only act on entries with `"disabled": false`.
  Each entry's `method` field documents how to get that site's data.
- `build_report.py` — pulls fresh data from all enabled distributors and
  rebuilds the workbook. Preserves Qty Added across rebuilds (matched by SKU).
- `record_qty.py` — CLI to record a carted quantity:
  `python3 record_qty.py "<sheet name>" <SKU> <qty>`
- `send_report.py` — emails the workbook + summary (`--dry-run` to preview).
  SMTP settings and recipients live in `email_config.json` (git-ignored;
  copy from `email_config.example.json`).
- `order_rules.py` — quantity logic. Edit only when the user asks.
- `scrapers/` — one module per automated distributor (phd, gts, universal).
- `dashboard.py` — optional local web UI (legacy from the app phase; the
  agent flow does not need it).

## Distributor notes (as of Aug 2026)

- **PHD** (portal.phdgames.com): catalog + pre-orders public, no account.
  Data via public JSON API (see scrapers/phd.py). Cart UI exists logged out;
  a real cart likely requires the user's account/login.
- **GTS** (gtsdistribution.com): public CSV export endpoint with wholesale
  prices (see scrapers/gts.py). Cart requires login.
- **Universal** (universaldistribution.ca): public JSON preorders API, no
  prices logged out (scrapers/universal.py). Currently disabled.
- **ACD / Southern**: scrapable (details in distributors.json) but no
  scraper built yet. Currently disabled.
- **MagX**: site URL unknown — ask the user. Currently disabled.

The user has **no distributor accounts yet**. Until accounts exist, cart
steps that require login will be blocked — do what's possible, record the
rest as "not carted", and say so plainly in the summary.
