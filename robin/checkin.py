"""Check-in gate (Grok Bot pattern): build the digest in code, then send ONE message or stay silent.

No model call: if nothing needs David, the check-in costs zero tokens. Skips while David is active
(asked something in the last 20 minutes). Every check-in is logged to traces/checkins.jsonl.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from robin import routines, trace

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "traces" / "checkins.jsonl"
ACTIVE_MINUTES = 20


def _last_owner_activity() -> dt.datetime | None:
    last = None
    for f in sorted(trace.TRACES.glob("*.jsonl")):
        if f.name in ("routines.jsonl", "checkins.jsonl"):
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            if rec.get("event") == "intake" and not str(rec.get("request", "")).startswith("[routine:"):
                ts = dt.datetime.fromisoformat(rec["ts"])
                last = ts if last is None or ts > last else last
    return last


def digest() -> list[str]:
    items = []
    props = [p for p in sorted((ROOT / "docs" / "proposals").glob("*.md"))
             if "awaiting David" in p.read_text(encoding="utf-8")]
    if props:
        items.append(f"{len(props)} proposal(s) need your go: " + ", ".join(p.stem for p in props[:3]))
    failed = [r for r in routines.runs(since_hours=12) if r["status"] == "failed"]
    if failed:
        items.append(f"{len(failed)} routine run(s) failed in 12h: " +
                     "; ".join(f"{r['routine']} ({r['reason'] or 'no reason'})" for r in failed[:3]))
    approvals = ROOT / "approvals"
    pending = sorted(approvals.glob("*.pending.json")) if approvals.exists() else []
    if pending:
        items.append(f"{len(pending)} draft(s) waiting for your 'go': " + ", ".join(p.stem.split('.')[0] for p in pending[:3]))
    try:
        from robin.kb.query import stale
        n = len(stale())
        if n:
            items.append(f"{n} knowledge node(s) stale or in conflict (robin kb stale)")
    except Exception:  # noqa: BLE001 - a broken KB must not break the check-in
        pass
    return items


def run(now: dt.datetime | None = None) -> dict:
    now = now or dt.datetime.now()
    last = _last_owner_activity()
    if last and now - last < dt.timedelta(minutes=ACTIVE_MINUTES):
        result = {"status": "skipped", "reason": f"David active {int((now - last).seconds / 60)} min ago"}
    else:
        items = digest()
        result = {"status": "message", "message": "\n".join(f"- {i}" for i in items)} if items else \
                 {"status": "silent", "reason": "nothing needs David"}
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"ts": now.isoformat(timespec="seconds"), **result}) + "\n")
    return result
