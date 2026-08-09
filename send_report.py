"""Email the pre-order report workbook with a summary in the body.

Reads SMTP settings from email_config.json (password can instead come from
the TILTED_SMTP_PASSWORD environment variable). Builds a fresh report
first unless --no-build is passed.

Usage:
    python3 send_report.py            # rebuild report, then send
    python3 send_report.py --no-build # send the existing workbook
    python3 send_report.py --dry-run  # print the email instead of sending
"""

import argparse
import json
import os
import smtplib
import sys
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
REPORT_XLSX = OUT_DIR / "preorder_report.xlsx"
SUMMARY_JSON = OUT_DIR / "report_summary.json"
CONFIG = OUT_DIR / "email_config.json"


def load_config():
    with open(CONFIG) as f:
        cfg = json.load(f)
    cfg["password"] = os.environ.get("TILTED_SMTP_PASSWORD") or cfg.get("password", "")
    missing = [k for k in ("smtp_host", "username", "password", "from_addr")
               if not cfg.get(k)]
    return cfg, missing


def compose(cfg, summary):
    lines = [f"Pre-order report generated {summary['generated']}.", ""]
    total_items = total_qty = 0
    total_cost = 0.0
    for d in summary["distributors"]:
        if d["status"] == "ok":
            cart = (f", {d['in_cart']} already in cart"
                    if d.get("in_cart") else "")
            lines.append(f"  • {d['name']}: {d['items']} items{cart}, "
                         f"order qty {d['total_qty']}, est. ${d['est_cost']:,.2f}")
            total_items += d["items"]
            total_qty += d["total_qty"]
            total_cost += d["est_cost"]
        else:
            lines.append(f"  • {d['name']}: unavailable — {d['detail']}")
    lines += ["", f"Totals: {total_items} items, {total_qty} units, "
                  f"est. ${total_cost:,.2f}",
              "", "Full detail per distributor is in the attached workbook "
                  "(one tab per site)."]
    body = "\n".join(lines)

    msg = EmailMessage()
    msg["Subject"] = (f"{cfg.get('subject_prefix', '[Tilted] Pre-Order Report')} "
                      f"— {datetime.now():%m/%d/%Y}")
    msg["From"] = cfg["from_addr"]
    msg["To"] = ", ".join(cfg["to_addrs"])
    msg.set_content(body)
    msg.add_attachment(
        REPORT_XLSX.read_bytes(),
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=REPORT_XLSX.name)
    return msg, body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-build", action="store_true",
                    help="skip rebuilding the report first")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the email instead of sending")
    args = ap.parse_args()

    if not args.no_build:
        import build_report
        build_report.build()

    with open(SUMMARY_JSON) as f:
        summary = json.load(f)

    cfg, missing = load_config()
    msg, body = compose(cfg, summary)

    if args.dry_run:
        print(f"Subject: {msg['Subject']}\nTo: {msg['To']}\n\n{body}")
        return

    if missing:
        sys.exit(f"email_config.json is missing: {', '.join(missing)}. "
                 "Fill it in (see _instructions) and retry.")

    with smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"], timeout=30) as s:
        s.starttls()
        s.login(cfg["username"], cfg["password"])
        s.send_message(msg)
    print(f"Sent to {msg['To']} with {REPORT_XLSX.name} attached.")


if __name__ == "__main__":
    main()
