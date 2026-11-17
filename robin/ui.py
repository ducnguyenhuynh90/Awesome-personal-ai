"""`robin ui` — a small local web page to set Robin up and use it. Standard library only.

Security:
- binds to 127.0.0.1 by default; every request needs the one-time token printed at start (cookie after first visit)
- keys are written to .env (gitignored) and are never shown back — the page only says "set" or "missing"
- only variable names listed in .env.example can be written
- every answer passes the secret scanner before it is shown
"""
from __future__ import annotations

import asyncio
import html
import json
import re
import secrets
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"
ORG = ROOT / "config" / "org.yaml"
DEPARTMENTS = ["product", "market-research", "data", "marketing", "executive", "sales-bd", "customer-support",
               "operations", "engineering", "finance", "people", "legal-compliance"]
NETWORK_DOMAINS = ["bsp.gov.ph", "pagcor.ph", "mb.com.ph", "inquirer.net", "bworldonline.com", "agbrief.com"]
RUNNING: dict[str, str] = {}  # task id -> request, for tasks started from the page


# ---------- settings helpers (pure, tested) ----------

def allowed_keys() -> list[str]:
    if not ENV_EXAMPLE.exists():
        return []
    return [ln.split("=", 1)[0].strip() for ln in ENV_EXAMPLE.read_text().splitlines()
            if re.match(r"^[A-Z][A-Z0-9_]*=", ln.strip())]


def key_status(path: Path | None = None) -> dict[str, bool]:
    path = path or ENV_FILE
    have = {}
    if path.exists():
        for ln in path.read_text().splitlines():
            if "=" in ln and not ln.strip().startswith("#"):
                k, v = ln.split("=", 1)
                have[k.strip()] = bool(v.strip())
    return {k: have.get(k, False) for k in allowed_keys()}


def set_key(name: str, value: str, path: Path | None = None) -> str:
    """Write one KEY=value into .env (replace or append). Refuses names not in .env.example."""
    path = path or ENV_FILE
    if name not in allowed_keys():
        raise ValueError(f"{name} is not a known setting (see .env.example)")
    value = value.strip().replace("\n", "")
    lines = path.read_text().splitlines() if path.exists() else ["# Local keys for Robin — gitignored, never commit."]
    out, done = [], False
    for ln in lines:
        if ln.split("=", 1)[0].strip() == name:
            if value:
                out.append(f"{name}={value}")
            done = True
        else:
            out.append(ln)
    if not done and value:
        out.append(f"{name}={value}")
    path.write_text("\n".join(out) + "\n")
    path.chmod(0o600)
    return f"{name} {'saved' if value else 'removed'}"


def set_departments(active: list[str], path: Path | None = None) -> str:
    path = path or ORG
    active = [d for d in DEPARTMENTS if d in active] or ["product"]
    text = path.read_text() if path.exists() else ""
    head = "".join(ln + "\n" for ln in text.splitlines() if ln.startswith("#"))
    path.write_text(head + yaml.safe_dump({"active_departments": active}, sort_keys=False))
    return f"active departments: {', '.join(active)}"


def active_departments() -> list[str]:
    return list((yaml.safe_load(ORG.read_text()) or {}).get("active_departments") or []) if ORG.exists() else []


# ---------- page ----------

CSS = """
:root{--bg:#f7f6f3;--card:#fff;--ink:#1f1e1c;--muted:#6b6a66;--line:#e4e2dc;--ok:#1d7a4f;--warn:#a15c07;--bad:#b42318;--acc:#2f5bd3}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--card:#1f1f1d;--ink:#ecebe7;--muted:#a3a29d;--line:#33322f;--ok:#4cc38a;--warn:#e3a34a;--bad:#f07a6e;--acc:#7f9cf5}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:920px;margin:0 auto;padding:20px 16px 60px}h1{font-size:22px;margin:4px 0 2px}h2{font-size:16px;margin:0 0 10px}
.sub{color:var(--muted);margin:0 0 18px}.grid{display:grid;gap:14px}.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px}
.row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.pill{font-size:12px;padding:2px 8px;border-radius:99px;border:1px solid var(--line)}
.ok{color:var(--ok)}.warn{color:var(--warn)}.bad{color:var(--bad)}.muted{color:var(--muted)}
input[type=text],input[type=password],textarea,select{width:100%;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink);font:inherit}
textarea{min-height:70px}button{padding:8px 14px;border-radius:8px;border:1px solid var(--acc);background:var(--acc);color:#fff;font:inherit;cursor:pointer}
button.ghost{background:transparent;color:var(--acc)}table{width:100%;border-collapse:collapse;font-size:14px}td,th{text-align:left;padding:6px 4px;border-bottom:1px solid var(--line);vertical-align:top}
ol{margin:0;padding-left:20px}pre{white-space:pre-wrap;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:10px;margin:8px 0;font:13px/1.45 ui-monospace,monospace}
.flash{background:var(--card);border-left:4px solid var(--acc);padding:8px 12px;border-radius:6px;margin-bottom:14px}
@media (min-width:760px){.two{grid-template-columns:1fr 1fr}}
"""


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def form(action: str, token: str, inner: str, extra: str = "") -> str:
    return f'<form method="post" action="{action}" {extra}><input type="hidden" name="t" value="{esc(token)}">{inner}</form>'


def page(token: str, flash: str = "") -> str:
    from robin import checkin, integrations, routines, trace
    integrations.load_env_file()
    model_ok = integrations.model_status().ready
    keys = key_status()
    sts = {s.name: s for s in integrations.statuses()}
    act = active_departments()

    steps = [
        ("Model access", model_ok, "Paste ANTHROPIC_API_KEY below (or run <code>claude</code> once on this machine to log in)."),
        ("Departments", bool(act), "Pick which teams Robin works for."),
        ("Network (claude.ai setting)", None,
         "Scheduled runs on claude.ai need these sites allowed in the environment's network settings: "
         + ", ".join(f"<code>{d}</code>" for d in NETWORK_DOMAINS) + ". This page cannot change that setting."),
        ("Tools (optional)", any(s.ready for s in sts.values() if s.kind == "mcp"),
         "Add a tool's keys below, then switch it on. Everything works without them."),
    ]
    step_html = "".join(
        f'<li><b>{esc(n)}</b> — <span class="{"ok" if ok else ("muted" if ok is None else "warn")}">'
        f'{"done" if ok else ("check on claude.ai" if ok is None else "to do")}</span><br><span class="muted">{h}</span></li>'
        for n, ok, h in steps)

    def key_row(k: str, v: bool) -> str:
        inner = ('<div class="row"><input type="password" name="value" autocomplete="off" placeholder="paste value" '
                 f'style="flex:1"><input type="hidden" name="name" value="{esc(k)}"><button>Save</button></div>')
        state = '<td class="ok">set</td>' if v else '<td class="muted">missing</td>'
        return f"<tr><td><code>{esc(k)}</code></td>{state}<td>{form('/key', token, inner)}</td></tr>"

    def toggle(action: str, name: str, enabled: bool) -> str:
        inner = (f'<input type="hidden" name="name" value="{esc(name)}"><input type="hidden" name="on" '
                 f'value="{0 if enabled else 1}"><button class="ghost">{"Turn off" if enabled else "Turn on"}</button>')
        return form(action, token, inner)

    def tool_row(s) -> str:
        if s.ready:
            state = '<td class="ok">ready</td>'
        elif s.enabled:
            state = f'<td class="warn">on, missing {esc(", ".join(s.missing))}</td>'
        else:
            state = '<td class="muted">off</td>'
        return f"<tr><td>{esc(s.name)}</td>{state}<td>{toggle('/toggle', s.name, s.enabled)}</td></tr>"

    def routine_row(n: str, r: dict) -> str:
        on = bool(r.get("enabled"))
        last = (routines.runs(n) or [{}])[-1].get("status", "-")
        return (f'<tr><td>{esc(n)}</td><td>{esc(r["owner"])}</td><td class="{"ok" if on else "muted"}">'
                f'{"on" if on else "off"}</td><td class="muted">{esc(last)}</td><td>{toggle("/routine", n, on)}</td></tr>')

    required = ("ANTHROPIC_API_KEY",)
    key_rows = "".join(key_row(k, v) for k, v in keys.items() if k in required)
    tool_key_rows = "".join(key_row(k, v) for k, v in keys.items() if k not in required)
    tool_rows = "".join(tool_row(s) for s in sts.values() if s.kind in ("mcp", "context"))
    dept_boxes = "".join(
        f'<label class="pill"><input type="checkbox" name="d" value="{d}" {"checked" if d in act else ""}> {d}</label>'
        for d in DEPARTMENTS)
    routine_rows = "".join(routine_row(n, r) for n, r in routines.load().items())

    digest = checkin.digest()
    digest_html = "<ol>" + "".join(f"<li>{esc(i)}</li>" for i in digest) + "</ol>" if digest else '<p class="muted">Nothing needs you.</p>'

    tasks = []
    for f in sorted(trace.TRACES.glob("*.jsonl"))[-3:] if trace.TRACES.exists() else []:
        if f.name in ("routines.jsonl", "checkins.jsonl"):
            continue
        for ln in f.read_text().splitlines():
            r = json.loads(ln)
            if r.get("event") == "intake":
                tasks.append(r)
    task_rows = "".join(f'<tr><td><a href="/task/{esc(r["task"])}">{esc(r["task"])}</a></td><td>{esc(r.get("request", "")[:80])}</td>'
                        f'<td class="muted">{esc((r.get("route") or {}).get("agent", ""))}</td></tr>' for r in reversed(tasks[-8:]))

    ask_note = "" if model_ok else '<p class="warn">Model access missing: you can preview routing, but not get an answer yet.</p>'
    flash_html = f'<div class="flash">{esc(flash)}</div>' if flash else ""

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Robin setup</title><style>{CSS}</style></head><body><main>
<h1>Robin</h1><p class="sub">Set up and use your agent org. Keys stay on this machine in <code>.env</code> and are never shown again.</p>
{flash_html}
<div class="grid">
<section class="card"><h2>Setup checklist</h2><ol>{step_html}</ol></section>
<section class="card"><h2>Ask Robin</h2>{ask_note}
{form("/ask", token, '<textarea name="q" placeholder="e.g. Write 5 push variants to win back lapsed depositors" required></textarea><div class="row" style="margin-top:8px"><button name="mode" value="run">Ask</button><button class="ghost" name="mode" value="preview">Preview routing only</button></div>')}
</section>
<div class="grid two">
<section class="card"><h2>Needs you today</h2>{digest_html}</section>
<section class="card"><h2>Recent tasks</h2><table>{task_rows or '<tr><td class="muted">None yet.</td></tr>'}</table></section>
</div>
<section class="card"><h2>Departments</h2>{form("/departments", token, f'<div class="row">{dept_boxes}</div><div style="margin-top:10px"><button>Save departments</button></div>')}</section>
<section class="card"><h2>Keys</h2><table>{key_rows}</table>
<details style="margin-top:10px"><summary>Tool keys (optional)</summary><table>{tool_key_rows}</table></details>
<p class="muted">Leave a value empty and Save to remove it.</p></section>
<div class="grid two">
<section class="card"><h2>Tools</h2><table>{tool_rows}</table></section>
<section class="card"><h2>Routines</h2><table><tr><th>Routine</th><th>Owner</th><th></th><th>Last</th><th></th></tr>{routine_rows}</table></section>
</div>
</div></main></body></html>"""


def task_page(token: str, task_id: str) -> str:
    from guard import secret_scanner
    from robin import trace
    recs = trace.read(task_id)
    intake = next((r for r in recs if r.get("event") == "intake"), {})
    result = next((r for r in reversed(recs) if r.get("event") == "result"), None)
    if result is None:
        body = '<p class="muted">Working… this page refreshes every 5 seconds.</p>'
        refresh = '<meta http-equiv="refresh" content="5">'
    else:
        out, _ = secret_scanner.redact(str(result.get("output", "")))
        state = "silent" if result.get("silent") else ("failed" if result.get("failed") else "answer")
        body = (f'<p class="muted">{state} · ${float(result.get("cost_usd") or 0):.3f} · {esc(result.get("words", ""))} words</p>'
                f'<pre>{esc(out) or "(no reply)"}</pre>'
                + form("/feedback", token,
                       f'<input type=hidden name=task value="{esc(task_id)}"><input type=text name=why placeholder="Reason (needed for Reject)">'
                       '<div class="row" style="margin-top:8px"><button name="kind" value="accept">Accept</button>'
                       '<button class="ghost" name="kind" value="reject">Reject</button></div>'))
        refresh = ""
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'{refresh}<title>Robin task</title><style>{CSS}</style></head><body><main><p><a href="/">← back</a></p>'
            f'<h1>{esc(intake.get("request", task_id))}</h1><p class="sub">{esc(task_id)} · '
            f'{esc((intake.get("route") or {}).get("agent", ""))}</p><section class="card">{body}</section></main></body></html>')


def preview_page(token: str, q: str) -> str:
    from robin.orchestrator import build_prompt
    from robin.router import Router
    prompt, meta = build_prompt(q, Router())
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Robin preview</title><style>{CSS}</style></head><body><main><p><a href="/">← back</a></p><h1>Routing preview</h1>'
            f'<section class="card"><p><b>{esc(meta["agent"])}</b> · skills {esc(", ".join(meta["skills"][:3]))}</p>'
            f'<pre>{esc(prompt)}</pre><p class="muted">No model call, no cost.</p></section></main></body></html>')


def start_task(q: str) -> str:
    from robin import orchestrator, trace
    tid = trace.new_task_id()
    RUNNING[tid] = q

    def work():
        try:
            asyncio.run(orchestrator.run(q, task_id=tid))
        except Exception as e:  # noqa: BLE001 - shown on the task page instead of crashing the server
            trace.log(tid, "result", output=f"FAILED: {type(e).__name__}: {e}", failed=True, cost_usd=0)
        finally:
            RUNNING.pop(tid, None)

    threading.Thread(target=work, daemon=True).start()
    return tid


# ---------- server ----------

def make_handler(token: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):  # quiet
            pass

        def _authed(self, form_token: str = "") -> bool:
            cookie = self.headers.get("Cookie", "")
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            return secrets.compare_digest(form_token or q.get("t", [""])[0] or
                                          dict(c.strip().split("=", 1) for c in cookie.split(";") if "=" in c).get("robin_t", ""),
                                          token)

        def _send(self, body: str, code: int = 200, set_cookie: bool = False):
            data = body.encode()
            self.send_response(code)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Frame-Options", "SAMEORIGIN")
            self.send_header("Referrer-Policy", "no-referrer")
            if set_cookie:
                self.send_header("Set-Cookie", f"robin_t={token}; HttpOnly; SameSite=Strict; Path=/")
            self.end_headers()
            self.wfile.write(data)

        def _redirect(self, to: str):
            sep = "&" if "?" in to else "?"
            self.send_response(303)
            self.send_header("Location", f"{to}{sep}t={token}")
            self.send_header("Set-Cookie", f"robin_t={token}; HttpOnly; SameSite=Strict; Path=/")
            self.end_headers()

        def do_GET(self):
            if not self._authed():
                return self._send("<p>Open the link printed by <code>robin ui</code> (it carries a one-time token).</p>", 403)
            path = urllib.parse.urlparse(self.path)
            flash = urllib.parse.parse_qs(path.query).get("m", [""])[0]
            if path.path.startswith("/task/"):
                return self._send(task_page(token, path.path.split("/", 2)[2]), set_cookie=True)
            return self._send(page(token, flash), set_cookie=True)

        def do_POST(self):
            length = min(int(self.headers.get("Content-Length") or 0), 100_000)
            data = urllib.parse.parse_qs(self.rfile.read(length).decode(), keep_blank_values=True)
            f = {k: v[0] for k, v in data.items()}
            if not self._authed(f.get("t", "")):
                return self._send("forbidden", 403)
            msg = ""
            try:
                if self.path == "/key":
                    msg = set_key(f.get("name", ""), f.get("value", ""))
                elif self.path == "/departments":
                    msg = set_departments(data.get("d", []))
                elif self.path == "/toggle":
                    from robin import integrations
                    msg = integrations.set_enabled(f["name"], f.get("on") == "1")
                elif self.path == "/routine":
                    from robin import integrations, routines
                    msg = integrations.set_enabled(f["name"], f.get("on") == "1", routines.CONFIG)
                elif self.path == "/ask":
                    q = f.get("q", "").strip()
                    if not q:
                        msg = "Type a question first."
                    elif f.get("mode") == "preview":
                        return self._send(preview_page(token, q))
                    else:
                        from robin import integrations
                        integrations.load_env_file()
                        if not integrations.model_status().ready:
                            msg = "Add ANTHROPIC_API_KEY first (Keys section)."
                        else:
                            return self._redirect(f"/task/{start_task(q)}")
                elif self.path == "/feedback":
                    from robin import learn
                    kind = "accept" if f.get("kind") == "accept" else "reject"
                    learn.record(f["task"], kind, note=f.get("why", ""))
                    msg = f"Saved: {kind}"
            except (ValueError, KeyError) as e:
                msg = f"Not saved: {e}"
            self._redirect("/?m=" + urllib.parse.quote(msg))

    return Handler


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    token = secrets.token_urlsafe(16)
    server = ThreadingHTTPServer((host, port), make_handler(token))
    print(f"Robin UI: http://{'localhost' if host in ('127.0.0.1', '0.0.0.0') else host}:{port}/?t={token}")
    print("Keep this link private: it carries the access token. Ctrl+C to stop.")
    server.serve_forever()
