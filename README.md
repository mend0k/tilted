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

**Jump to:** [Setup](#step-by-step-setup) · [Running it](#running-it) ·
[Reading the output](#reading-the-output) ·
[Example prompts](#example-prompts) · [Reference](#reference) ·
[Troubleshooting](#troubleshooting)

---

# Step-by-step setup

Do steps 1–4 once per machine. Step 5 (email) is optional but recommended.

### 1. Install Claude

Install **[Claude Desktop](https://claude.ai/download)** (easiest) or
**Claude Code** (terminal). Either works — the harness is the same.

### 2. Get the folder onto the machine

```bash
git clone https://github.com/mend0k/tilted.git
```

Or copy the folder by hand. Any location is fine.

### 3. Check Python and install the one dependency

macOS and Linux already have Python 3.9+. On Windows, install it from
[python.org](https://www.python.org/downloads/) and check "Add Python to
PATH" during setup.

```bash
pip3 install openpyxl
```

Verify it worked — this should print a version, not an error:

```bash
python3 -c "import openpyxl; print(openpyxl.__version__)"
```

### 4. Open the folder as your session's working directory

This is the step that makes `/start-preorder` exist. The skills live in
`.claude/skills/`, and Claude only finds them when this folder is the
session's working directory.

- **Claude Desktop:** open the app and set the project/working folder to
  this `tilted` directory, then start a new chat in it.
- **Claude Code:** `cd` into the folder first, then launch:

```bash
cd tilted && claude
```

Confirm it worked by typing `/` — you should see **start-preorder** and
**send-report** in the list. If they're missing, the working directory
isn't set to this folder; fix that and start a new session.

### 5. Set up email (optional, one time)

Copy the template and fill in your SMTP details:

```bash
cp email_config.example.json email_config.json
```

Open `email_config.json` and set `smtp_host`, `smtp_port`, `username`,
`from_addr`, and `password`. For Gmail: host `smtp.gmail.com`, port `587`,
and an **App Password** from
[myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
— never your real Google password. Recipient is preset to the test address
in `to_addrs`; change it to wherever you want reports sent.

This file is git-ignored, so your credentials never leave the machine. Test
it without sending anything real:

```bash
python3 send_report.py --dry-run
```

Skip this step if you'd rather just have the agent report back in chat.

---

# Running it

### Send the prompt

In a session opened in this folder, type:

```
/start-preorder
```

That's the whole thing. Plain words work too — "start the preorder run".
See [Example prompts](#example-prompts) below for variations.

### What happens, in order

1. **Data refresh** — the agent runs `build_report.py`, which pulls current
   pre-orders due from each enabled distributor and rebuilds the workbook.
   Takes a few seconds.
2. **Carting** — it opens each distributor site in the browser, finds items
   by SKU, sets quantities, and adds them to the cart. If a site needs a
   login it **pauses and asks you to log in yourself** — it never types
   credentials. It stops at the cart and never checks out.
3. **Recording** — after each successful add it writes the real quantity
   into the workbook immediately, so an interrupted run still leaves an
   accurate record.
4. **Reporting** — it rebuilds the summary, emails it if email is
   configured (or shows the summary in chat if not), and tells you what was
   carted, what was skipped, and why.

### Expect to be interrupted at least once

The first run on a new machine will almost certainly pause for a login.
That's by design. Log in yourself in the browser pane, then tell the agent
to continue.

---

# Reading the output

You get output in three places.

### 1. In chat

A plain-language wrap-up per distributor: how many items were carted, how
many were skipped and why, total units, estimated cost, and anything
needing your attention (logins, missing accounts, site errors). This is the
part to read first.

### 2. `preorder_report.xlsx` — the working order sheet

A **Summary** tab plus one tab per distributor.

The **Summary** tab, one row per distributor:

| Column | Means |
|---|---|
| Distributor | Site name |
| Status | `ok` = data pulled fine; `unavailable` = that site failed or has no scraper |
| Items | How many pre-order items are currently due |
| In Cart | How many rows have a recorded *Qty Added* |
| Total Qty | Units — uses your recorded quantities where present, suggestions elsewhere |
| Est. Cost | Total at wholesale price (blank prices count as $0) |
| Notes | Why a site is unavailable, if it is |

Each **distributor tab**, one row per item:

| Column | Means |
|---|---|
| A SKU | The distributor's item number — what the agent searches by |
| B Name | Product name |
| C Manufacturer | Publisher |
| D Categories | Site's category labels |
| E MSRP | Retail price |
| F Price | Your wholesale price (blank where the site hides it without login) |
| G **Suggested Qty** | What `order_rules.py` recommends (default 3) |
| H **Qty Added** (yellow) | **What actually went in the cart.** The real record — yours to trust and to edit |
| I Line Total | `Price ×` Qty Added if filled in, otherwise Suggested Qty |
| J Release Date | When the product ships |
| K Pre-Order Date | **The deadline** — order by this date or you miss it |
| L UPC | Barcode |

The two columns that matter most: **Qty Added** is the system's memory of
what you ordered — it survives every data refresh (matched by SKU), so you
can rebuild anytime without losing it. **Pre-Order Date** is your deadline
clock; items drop off the list once it passes.

An empty Qty Added means "not carted." A filled-in one means the agent
verified that quantity in the site's cart — and it will skip that row on
future runs rather than double-ordering.

### 3. The email

Subject line with the date, the same per-distributor summary in the body,
and the workbook attached.

### A note on fresh clones

A new clone has no `preorder_report.xlsx` — the first run creates it. The
workbook is git-ignored, so **Qty Added history stays on the machine that
ran it** and doesn't travel with the repo.

---

# Example prompts

The skill handles the whole run, so `/start-preorder` alone is enough. Add
a sentence when you want to deviate from the defaults:

**Standard run — everything enabled, quantity 3 each:**

> /start-preorder

**Spell out the quantity explicitly** (matches `DEFAULT_QTY = 3`; the agent
follows your prompt over the default if you name a different number):

> /start-preorder — pull the current pre-orders due for the enabled sites,
> add 3 of each item to the cart, record what actually landed in the
> workbook, and email me the summary. Stop at the cart; don't check out.

**One site only:**

> Start the preorder run for PHD only — skip GTS this time.

**Different quantity for this run, without editing the rules file:**

> Start the preorder run, but use 2 of each item instead of 3.

**Selective carting:**

> Start the preorder run, but only cart MTG and Pokémon items — skip
> everything else, and tell me what you skipped.

**Deadline-driven:**

> Start the preorder run, but only items whose pre-order date is within the
> next 7 days.

**Dry look before committing to anything:**

> Refresh the pre-order data and show me the summary, but don't cart
> anything yet.

**Email only, no new data pull:**

> /send-report

**Preview the email without sending:**

> Show me what the report email would say, but don't send it.

Useful things to mention in a prompt when they apply: which sites, what
quantity, any category/deadline filter, and whether to email or just
report back. If a site needs a login, the agent will pause and ask you —
it never enters credentials itself.

---

# Reference

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
preorder_report.xlsx    THE order sheet (generated, git-ignored; Qty Added persists locally)
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

- **`/start-preorder` not recognized** — the session's working directory
  isn't this folder (skills live in `.claude/skills/`). Point it here and
  start a new session; type `/` to confirm the skills are listed.
- **`ModuleNotFoundError: openpyxl`** — run `pip3 install openpyxl`.
- **Gmail rejects login** — use an App Password, which requires 2-step
  verification on the Google account. A regular password will not work.
- **`email_config.json is missing: ...`** — copy
  `email_config.example.json` to `email_config.json` and fill in the named
  fields.
- **A distributor errors during refresh** — the run continues with the
  others and the summary says which failed; retry later.
- **A site asks to log in and I have no account** — the agent skips carting
  there and still reports that site's items. Get an account, then rerun.
- **Fewer items than last time** — normal. Items drop off once their
  pre-order deadline passes.
- **`Qty Added` looks wrong / I want to redo an item** — edit the cell
  directly in Excel. Clear it to make the agent treat the item as un-carted
  on the next run.
