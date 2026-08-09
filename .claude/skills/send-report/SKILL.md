---
name: send-report
description: Build (or reuse) the pre-order workbook and email it with a summary in the body. Use when the user asks to send the report, email the summary, or test the email.
---

# Send the Pre-Order Report

1. Unless the user says the current workbook is fine, refresh it first:
   `python3 build_report.py` (preserves Qty Added).
2. Preview: `python3 send_report.py --dry-run --no-build` — show the user
   the subject/recipient/body if they asked for a test or seem unsure.
3. Send: `python3 send_report.py --no-build`.
   - If it exits with missing-config errors, `email_config.json` needs the
     user's SMTP details (Gmail requires an App Password — instructions are
     in the file). Ask them to fill it in; never ask for or enter their
     password yourself.
4. Confirm to the user what was sent and to whom.
