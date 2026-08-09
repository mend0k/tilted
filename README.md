# Tilted — Distributor Pre-Order Agent Harness

Tilted is a folder you open with **Claude Desktop / Claude Code**. The agent
does the weekly pre-order run for you:

1. Pulls current **pre-orders due** from every enabled distributor (no
   accounts needed for the data).
2. **Adds items to each site's cart** (quantity rules you control; the agent
   always stops at the cart — it never checks out or touches payment).
3. Records what was actually carted in **`preorder_report.xlsx`** — the
   single source of truth (one tab per distributor, yellow *Qty Added*
   column, preserved across data refreshes).
4. Emails a summary with the workbook attached.

Current focus: **Trading Card Games**.

## Setup (any machine)

1. Install [Claude Desktop](https://claude.ai/download) or Claude Code.
2. Get this folder onto the machine (copy, git clone, etc.).
3. Have Python 3.9+ and run once:

```bash
pip3 install openpyxl
```

4. Open this folder as the session's working directory in Claude.

## Use

Start a session in this folder and type:

- **`/start-preorder`** — the full run: refresh data → cart items →
  record in the workbook → email/report the summary.
- **`/send-report`** — just build and email the report.

You can also just say "start preorder" in plain words.

During a run the agent may ask you to **log in** to a distributor site in
the browser pane — it will never type credentials for you. The first time,
copy `email_config.example.json` to `email_config.json` and fill it in so
it can send email (Gmail needs an App Password — instructions are inside
the file). `email_config.json` is git-ignored, so your SMTP details never
leave the machine.

## How the agent behaves (guardrails)

Baked into `CLAUDE.md` and the skills:

- Stops at the cart. **Never checks out, never enters payment details.**
- Never enters credentials; login is always yours to do.
- Records only quantities the site's cart actually shows.
- No CSV files; the workbook is the only record. Don't rename its tabs.

## Controlling quantities — `order_rules.py`

`DEFAULT_QTY = 3`. Add one-line rules that win over the default, checked
top-to-bottom:

```python
RULES = [
    ("Skip organized play kits", lambda i: "Organized Play Kit" in i["name"], 0),
    ("Heavy on MTG boosters",    lambda i: "MTG" in i["name"] and "Booster Display" in i["name"], 6),
]
```

If a row's *Qty Added* is already filled in, the agent treats it as done
and won't re-cart it.

## Distributors — `distributors.json`

Flip `"disabled"` to turn a site on/off. Currently enabled: **PHD, GTS**.

| Distributor | Data access | Status |
|---|---|---|
| PHD | public JSON API (incl. prices) | enabled |
| GTS Distribution | public CSV export (incl. prices) | enabled |
| Universal Distribution | public JSON API (no prices) | disabled |
| ACD Distribution | scrapable, scraper not built | disabled |
| Southern Hobby | scrapable, scraper not built | disabled |
| MagX | site URL unknown | disabled |

### Adding a distributor

1. `scrapers/<key>.py` with `fetch_preorders()` returning item dicts
   (`sku, name, manufacturer, categories, msrp, price, release_date,
   preorder_date, upc, distributor`).
2. Register in `scrapers/__init__.py`.
3. Entry in `distributors.json` with `"disabled": false`.

## Files

```
CLAUDE.md               agent ground rules + distributor notes (read every session)
.claude/skills/         /start-preorder and /send-report workflows
distributors.json       registry + on/off flags
order_rules.py          quantity logic (edit me)
build_report.py         pull data → rebuild preorder_report.xlsx
record_qty.py           record one carted qty: record_qty.py "<sheet>" <SKU> <qty>
send_report.py          email the workbook (--dry-run to preview)
email_config.example.json  SMTP template — copy to email_config.json (git-ignored) and fill in
scrapers/               per-distributor data fetchers
preorder_report.xlsx    THE order sheet (generated; your Qty Added persists)
dashboard.py            optional local web UI from the app phase:
                        python3 dashboard.py → http://localhost:8377
```

## Scripts without the agent

Everything the agent drives can be run by hand:

```bash
python3 build_report.py
```

```bash
python3 send_report.py --dry-run
```

## Troubleshooting

- **`/start-preorder` not recognized** — make sure the session's working
  directory is this folder (skills live in `.claude/skills/`), then start a
  new session.
- **Gmail rejects login** — use an App Password (requires 2-step
  verification on the Google account).
- **A distributor errors during refresh** — the run continues with the
  others; retry later.
