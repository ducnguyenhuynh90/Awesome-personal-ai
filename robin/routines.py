"""Routine contracts, validation and run log (Grok Bot routines + OpenAI dots typed schedules).

Proactive runs are read-only: the orchestrator restricts tools to READ_ONLY_TOOLS (no external writes even with
an approval token), replies SILENT unless `notify_if` is met, and logs every run to traces/routines.jsonl.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "routines.yaml"
RUN_LOG = ROOT / "traces" / "routines.jsonl"

REQUIRED = ["enabled", "owner", "trigger", "ask", "notify_if", "deliver_to", "max_runs_per_day", "end_date",
            "on_empty", "on_source_down"]
DELIVER = {"outbox", "brief"}
CRON = re.compile(r"^\S+ \S+ \S+ \S+ \S+$")
# Proactive mode: no writes outside Robin's own drafts and knowledge tools.
READ_ONLY_TOOLS = ["Read", "Grep", "Glob", "WebSearch", "WebFetch", "Skill", "TodoWrite", "Agent",
                   "mcp__kb__query", "mcp__kb__add_gap", "mcp__kb__add_source", "mcp__kb__add_fact"]
SILENT_STREAK_SLOWDOWN = 3


def load(path: Path = CONFIG) -> dict:
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("routines") or {}


def validate(agents: set[str], path: Path = CONFIG) -> list[str]:
    errors = []
    for name, r in load(path).items():
        where = f"routine {name}"
        for f in REQUIRED:
            if f not in r:
                errors.append(f"{where}: '{f}' missing")
        if r.get("owner") and r["owner"] not in agents:
            errors.append(f"{where}: owner '{r['owner']}' is not an agent")
        trig = r.get("trigger") or {}
        if not (("cron" in trig and CRON.match(str(trig["cron"])) and trig.get("tz")) or "event" in trig):
            errors.append(f"{where}: trigger needs {{cron, tz}} or {{event}}")
        if r.get("deliver_to") and r["deliver_to"] not in DELIVER:
            errors.append(f"{where}: deliver_to must be one of {sorted(DELIVER)}")
        if r.get("on_empty") not in (None, "silent"):
            errors.append(f"{where}: on_empty must be 'silent'")
        if r.get("on_source_down") not in (None, "report_failure"):
            errors.append(f"{where}: on_source_down must be 'report_failure' (never use old data)")
        if not isinstance(r.get("max_runs_per_day", 1), int) or not 1 <= r.get("max_runs_per_day", 1) <= 24:
            errors.append(f"{where}: max_runs_per_day must be 1-24")
    return errors


def runs(name: str | None = None, since_hours: float | None = None) -> list[dict]:
    if not RUN_LOG.exists():
        return []
    out = [json.loads(line) for line in RUN_LOG.read_text(encoding="utf-8").splitlines() if line.strip()]
    if name:
        out = [r for r in out if r["routine"] == name]
    if since_hours is not None:
        cutoff = dt.datetime.now() - dt.timedelta(hours=since_hours)
        out = [r for r in out if dt.datetime.fromisoformat(r["ts"]) >= cutoff]
    return out


def log_run(name: str, status: str, reason: str = "", task: str = "", cost_usd: float = 0.0) -> dict:
    """status: succeeded | silent | failed | skipped."""
    RUN_LOG.parent.mkdir(exist_ok=True)
    rec = {"ts": dt.datetime.now().isoformat(timespec="seconds"), "routine": name, "status": status,
           "reason": reason, "task": task, "cost_usd": cost_usd}
    with open(RUN_LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
    return rec


def silent_streak(name: str) -> int:
    n = 0
    for r in reversed(runs(name)):
        if r["status"] != "silent":
            break
        n += 1
    return n


def can_run(name: str, routine: dict, today: dt.date | None = None) -> tuple[bool, str]:
    today = today or dt.date.today()
    if not routine.get("enabled"):
        return False, "disabled"
    end = routine.get("end_date")
    if end and dt.date.fromisoformat(str(end)) < today:
        return False, f"ended {end}"
    todays = [r for r in runs(name) if r["ts"].startswith(today.isoformat()) and r["status"] != "skipped"]
    if len(todays) >= int(routine.get("max_runs_per_day", 1)):
        return False, "max_runs_per_day reached"
    streak = silent_streak(name)
    if streak >= SILENT_STREAK_SLOWDOWN and streak % 2 == 1:
        return False, f"slowed down after {streak} silent runs in a row (runs every other time)"
    return True, "ok"


def proactive_prompt(name: str, routine: dict) -> str:
    return (f"[routine: {name} · proactive, read-only]\n{routine['ask']}\n\n"
            f"Notify only if: {routine['notify_if']}. Otherwise reply exactly `SILENT: <one-line reason>`.\n"
            "If a source you need is down or unreachable, reply `FAILED: <source> unreachable` — never use old data "
            "as if it were current. You cannot send, post or publish anything in this mode; drafts go to outbox/.")
