---
name: start-preorder
description: Run the full pre-order workflow — pull fresh pre-orders-due data from enabled distributors, add items to each site's cart, record carted quantities in preorder_report.xlsx, and send/report the summary. Use when the user says "start preorder", "do the preorder run", or similar.
---

# Pre-Order Run

Follow CLAUDE.md ground rules at all times: **stop at cart (never checkout,
never payment), never enter credentials, record everything in the workbook,
no CSVs.**

## 1. Refresh data

```bash
python3 build_report.py
```

- If `openpyxl` is missing, `pip3 install openpyxl` first.
- This pulls live data for every distributor with `"disabled": false` in
  `distributors.json` and rebuilds `preorder_report.xlsx` (one tab per
  distributor). Existing Qty Added entries are preserved automatically.
- Read the printed per-distributor summary. If a distributor errored, note
  it for the final report and continue with the others.

## 2. Cart the items, one distributor at a time

For each **enabled** distributor tab in the workbook:

1. Decide the target quantity per item: **Qty Added if already filled in
   (someone carted it before — skip those rows), otherwise Suggested Qty.**
   Skip rows whose target is 0.
2. Open the distributor's portal (URL in `distributors.json`) in the
   browser tool.
3. **Login check:** if carting requires an account and the user isn't
   logged in, pause and ask the user to log in in the browser pane, then
   continue. If they have no account for that site, skip carting for it
   (data still counts in the report) and note it.
4. For each item: find it on the site (search by SKU is most reliable),
   set the quantity, add to cart. Verify the cart actually shows the item
   and quantity before counting it as done.
5. **Immediately after each successful add**, record it:

   ```bash
   python3 record_qty.py "<sheet name>" <SKU> <qty>
   ```

   Record only what the site's cart really shows. If an item can't be
   found / is out of stock / fails, do NOT record a quantity — keep a note
   for the summary instead.
6. Batch sensibly: after every ~10 items, glance at the cart total to
   confirm nothing was silently dropped.

Site-specific tips live in each entry's `method` field in
`distributors.json` and in `CLAUDE.md` → Distributor notes.

## 3. Report

1. Rebuild the summary so it reflects recorded quantities:

   ```bash
   python3 build_report.py
   ```

2. Email it. If `email_config.json` is filled in:

   ```bash
   python3 send_report.py --no-build
   ```

   If SMTP isn't configured, run `python3 send_report.py --dry-run
   --no-build` and give the user the summary inline instead, noting that
   email isn't configured yet.

3. Tell the user, per distributor: items carted vs. skipped (and why),
   total units and estimated cost, and anything needing their action
   (logins, missing accounts, site errors). Plain sentences, not logs.
