"""Tilted management dashboard — local web UI for the pre-order system.

Stdlib only (no installs). Run:

    python3 dashboard.py

then open http://localhost:8377. Buttons: build the report, preview the
email (dry run), and send the test email. Shows the distributor registry
and the latest run summary.
"""

import json
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = 8377


def registry():
    with open(ROOT / "distributors.json") as f:
        return json.load(f)["distributors"]


def summary():
    p = ROOT / "report_summary.json"
    return json.loads(p.read_text()) if p.exists() else None


def email_ready():
    try:
        cfg = json.loads((ROOT / "email_config.json").read_text())
    except Exception:
        return False
    import os
    pw = os.environ.get("TILTED_SMTP_PASSWORD") or cfg.get("password")
    return bool(cfg.get("smtp_host") and cfg.get("username")
                and cfg.get("from_addr") and pw)


def run_script(args, timeout=300):
    proc = subprocess.run([sys.executable] + args, cwd=ROOT, timeout=timeout,
                          capture_output=True, text=True)
    return {"ok": proc.returncode == 0,
            "output": (proc.stdout + proc.stderr).strip()}


PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Tilted — Pre-Order Control</title>
<style>
 body{font:15px -apple-system,Helvetica,Arial,sans-serif;margin:0;background:#f4f6f7;color:#1f2a2e}
 header{background:#00838f;color:#fff;padding:16px 28px;font-size:20px;font-weight:600}
 main{max-width:960px;margin:24px auto;padding:0 20px}
 .card{background:#fff;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,.08);padding:18px 22px;margin-bottom:18px}
 h2{font-size:15px;text-transform:uppercase;letter-spacing:.05em;color:#00838f;margin:0 0 12px}
 table{border-collapse:collapse;width:100%}
 th,td{text-align:left;padding:7px 10px;border-bottom:1px solid #eceff1;font-size:14px}
 th{color:#607d8b;font-weight:600}
 .pill{display:inline-block;padding:2px 10px;border-radius:999px;font-size:12px;font-weight:600}
 .ok{background:#e0f2f1;color:#00695c}.warn{background:#fff3e0;color:#e65100}.err{background:#ffebee;color:#b71c1c}
 button{background:#00838f;color:#fff;border:0;border-radius:8px;padding:10px 18px;font-size:14px;font-weight:600;cursor:pointer;margin-right:10px}
 button:disabled{opacity:.5;cursor:wait}
 button.secondary{background:#eceff1;color:#37474f}
 pre{background:#263238;color:#eceff1;padding:14px;border-radius:8px;font-size:12.5px;overflow-x:auto;white-space:pre-wrap;min-height:20px}
 .muted{color:#78909c;font-size:13px}
</style></head><body>
<header>Tilted — Pre-Order Control</header>
<main>
 <div class="card">
  <h2>Actions</h2>
  <button id="build">Build report</button>
  <button id="preview" class="secondary">Preview email (dry run)</button>
  <button id="send">Send test email</button>
  <div class="muted" id="emailcfg" style="margin-top:10px"></div>
  <pre id="log">Ready.</pre>
 </div>
 <div class="card"><h2>Last run</h2><div id="lastrun" class="muted">No report built yet.</div></div>
 <div class="card"><h2>Distributors</h2><table id="dists"><tr><th>Name</th><th>Automation</th><th>Site</th><th>Notes</th></tr></table></div>
</main>
<script>
const log = m => document.getElementById('log').textContent = m;
async function refresh(){
  const s = await (await fetch('/api/status')).json();
  document.getElementById('emailcfg').textContent = s.email_ready
    ? 'Email config: ready.'
    : 'Email config: incomplete — fill in email_config.json (see _instructions) before sending.';
  document.getElementById('send').disabled = !s.email_ready;
  const t = document.getElementById('dists');
  t.innerHTML = '<tr><th>Name</th><th>Automation</th><th>Site</th><th>Notes</th></tr>';
  const cls = a => a==='working' ? 'ok' : (a==='feasible' ? 'warn' : 'err');
  for(const d of s.distributors){
    const pill = d.disabled ? '<span class="pill" style="background:#eceff1;color:#78909c">disabled</span>'
                            : `<span class="pill ${cls(d.automation)}">${d.automation}</span>`;
    t.innerHTML += `<tr style="${d.disabled?'opacity:.55':''}"><td><b>${d.name}</b></td><td>${pill}</td>
      <td>${d.website?`<a href="${d.website}" target="_blank">site</a>`:'—'}</td><td class="muted">${d.method||''}</td></tr>`;
  }
  const lr = document.getElementById('lastrun');
  if(s.summary){
    let rows = s.summary.distributors.map(d =>
      `<tr><td>${d.name}</td><td><span class="pill ${d.status==='ok'?'ok':'err'}">${d.status}</span></td>
       <td>${d.items}</td><td>${d.total_qty}</td><td>$${d.est_cost.toLocaleString()}</td></tr>`).join('');
    lr.innerHTML = `Generated ${s.summary.generated}<table><tr><th>Distributor</th><th>Status</th><th>Items</th><th>Qty</th><th>Est. cost</th></tr>${rows}</table>`;
  }
}
async function act(btn, url, msg){
  const b = document.getElementById(btn); b.disabled = true; log(msg + '...');
  try{ const r = await (await fetch(url, {method:'POST'})).json();
       log(r.output || (r.ok ? 'Done.' : 'Failed.')); }
  catch(e){ log('Error: ' + e); }
  b.disabled = false; refresh();
}
document.getElementById('build').onclick  = () => act('build', '/api/build', 'Building report (pulls live data)');
document.getElementById('preview').onclick= () => act('preview', '/api/preview', 'Composing email preview');
document.getElementById('send').onclick   = () => {
  if(confirm('Send the test email with the current report attached?'))
    act('send', '/api/send', 'Sending email');
};
refresh();
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            body = PAGE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/status":
            self._json({"distributors": registry(), "summary": summary(),
                        "email_ready": email_ready()})
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/build":
            self._json(run_script(["build_report.py"]))
        elif self.path == "/api/preview":
            self._json(run_script(["send_report.py", "--dry-run", "--no-build"]))
        elif self.path == "/api/send":
            self._json(run_script(["send_report.py", "--no-build"]))
        else:
            self.send_error(404)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print(f"Tilted dashboard: http://localhost:{PORT}")
    HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
