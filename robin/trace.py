"""JSONL traces: one line per event, one file per day. Bodies of tool results are not stored."""
from __future__ import annotations

import datetime as dt
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACES = ROOT / "traces"


def new_task_id() -> str:
    return f"t-{dt.datetime.now().strftime('%y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}"


def log(task_id: str, event: str, **data) -> None:
    TRACES.mkdir(exist_ok=True)
    rec = {"ts": dt.datetime.now().isoformat(timespec="seconds"), "task": task_id, "event": event, **data}
    with open(TRACES / f"{dt.date.today().isoformat()}.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


def read(task_id: str) -> list[dict]:
    out = []
    for f in sorted(TRACES.glob("*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            if rec.get("task") == task_id:
                out.append(rec)
    return out


def spend_today() -> float:
    f = TRACES / f"{dt.date.today().isoformat()}.jsonl"
    if not f.exists():
        return 0.0
    total = 0.0
    for line in f.read_text(encoding="utf-8").splitlines():
        rec = json.loads(line)
        if rec.get("event") == "result":
            total += float(rec.get("cost_usd") or 0)
    return total
