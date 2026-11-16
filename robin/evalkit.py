"""Eval flywheel (from "The Eval Flywheel" doc): suites, repeated runs, cost/latency, saved results, diffs,
failure mining and a weekly scorecard.

Suites (field `suite` on each process case):
  regression  must stay at 100% (pass every run) — blocks a change
  never       things Robin must never do (approve, post, leak, deploy) — must stay at 100%
  capability  hard cases; 40–70% is healthy; tracks progress
Cases come from evals/process/cases.yaml (public, synthetic) and evals/private/cases.yaml (gitignored: cases mined
from David's real requests, which may hold company details).
Results (with outputs, for reading flipped cases) go to evals/results/ (gitignored).
"""
from __future__ import annotations

import datetime as dt
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PUBLIC_CASES = ROOT / "evals" / "process" / "cases.yaml"
PRIVATE_CASES = ROOT / "evals" / "private" / "cases.yaml"
RESULTS = ROOT / "evals" / "results"
GATE_SUITES = ("regression", "never")


# ---------- cases ----------

def load_cases(suites: list[str] | None = None, only: list[str] | None = None) -> list[dict]:
    cases = []
    for path in (PUBLIC_CASES, PRIVATE_CASES):
        if path.exists():
            for c in (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("cases") or []:
                c.setdefault("suite", "regression")
                c["_source"] = "private" if path == PRIVATE_CASES else "public"
                cases.append(c)
    if suites:
        cases = [c for c in cases if c["suite"] in suites]
    if only:
        cases = [c for c in cases if c["id"] in only]
    return cases


# ---------- run ----------

def run_cases(cases: list[dict], runs: int = 1, runner=None, checks=None) -> dict:
    """Run each case `runs` times. runner(request) -> orchestrator result dict."""
    if runner is None:
        from robin.orchestrator import run_sync as runner
    if checks is None:
        from evals.process.checks import CHECKS as checks
    rows = []
    for c in cases:
        attempts = []
        for _ in range(runs):
            t0 = time.monotonic()
            res = runner(c["request"])
            secs = round(time.monotonic() - t0, 1)
            results = [checks[n](res.get("output", ""), trace_tools=res.get("tools"), **(c.get("args") or {}))
                       for n in c["checks"]]
            attempts.append({"pass": all(r[0] for r in results), "details": [r[1] for r in results],
                             "task": res.get("task"), "cost_usd": res.get("cost_usd", 0), "seconds": secs,
                             "agent": (res.get("route") or {}).get("agent"), "output": res.get("output", "")})
        n_pass = sum(a["pass"] for a in attempts)
        rows.append({"id": c["id"], "suite": c["suite"], "source": c["_source"], "runs": runs,
                     "pass_any": n_pass > 0, "pass_all": n_pass == runs, "passes": n_pass,
                     "cost_usd": round(sum(a["cost_usd"] for a in attempts) / runs, 4),
                     "seconds": round(sum(a["seconds"] for a in attempts) / runs, 1),
                     "agent": attempts[0]["agent"], "attempts": attempts})
    return summarize(rows)


def summarize(rows: list[dict]) -> dict:
    by_suite: dict[str, dict] = {}
    for suite in sorted({r["suite"] for r in rows}):
        rs = [r for r in rows if r["suite"] == suite]
        by_suite[suite] = {"cases": len(rs), "pass_all": sum(r["pass_all"] for r in rs),
                           "pass_any": sum(r["pass_any"] for r in rs),
                           "cost_usd": round(sum(r["cost_usd"] for r in rs), 4),
                           "avg_seconds": round(sum(r["seconds"] for r in rs) / len(rs), 1)}
    gate_ok = all(r["pass_all"] for r in rows if r["suite"] in GATE_SUITES)
    return {"rows": rows, "suites": by_suite, "gate_ok": gate_ok}


def save(result: dict, label: str = "", model: str = "") -> Path:
    RESULTS.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = RESULTS / f"{stamp}{'-' + label if label else ''}.json"
    path.write_text(json.dumps({"ts": stamp, "model": model, **result}, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def diff(a: Path, b: Path) -> list[str]:
    """Cases whose pass_all flipped between two saved runs — read these transcripts before trusting a score."""
    ra = {r["id"]: r for r in json.loads(a.read_text())["rows"]}
    rb = {r["id"]: r for r in json.loads(b.read_text())["rows"]}
    out = []
    for cid in sorted(set(ra) & set(rb)):
        if ra[cid]["pass_all"] != rb[cid]["pass_all"]:
            arrow = "FIXED " if rb[cid]["pass_all"] else "BROKEN"
            task = rb[cid]["attempts"][0]["task"]
            out.append(f"{arrow} {cid} ({rb[cid]['suite']}) — read: robin trace {task}")
    for cid in sorted(set(rb) - set(ra)):
        out.append(f"NEW    {cid} ({rb[cid]['suite']}) pass_all={rb[cid]['pass_all']}")
    return out


# ---------- mine: confirmed failures become permanent cases ----------

def mine(feedback: list[dict], checks=None, mined_ids: set[str] | None = None) -> list[dict]:
    """Turn edit/reject feedback into candidate regression cases.

    Every deterministic check is run on the bad output; the checks it FAILS are the ones that would have caught it,
    so they become the case's checks. If none fail, the case is marked `needs_check` for David to write one.
    """
    if checks is None:
        from evals.process.checks import CHECKS as checks
    mined_ids = mined_ids or set()
    generic = ["line1_answers", "under_cap", "numbers_sourced", "no_filler", "has_so_what", "no_secret"]
    out = []
    for f in feedback:
        if f.get("kind") not in ("edit", "down", "reject") or not f.get("request"):
            continue
        cid = f"mined-{f['task']}"
        if cid in mined_ids:
            continue
        failing = [n for n in generic if not checks[n](f.get("output", ""))[0]]
        out.append({"id": cid, "suite": "regression", "request": f["request"],
                    "checks": failing or ["line1_answers"], "needs_check": not failing,
                    "why": f.get("note", "")})
    return out


def append_private(cases: list[dict]) -> Path:
    PRIVATE_CASES.parent.mkdir(parents=True, exist_ok=True)
    data = yaml.safe_load(PRIVATE_CASES.read_text()) if PRIVATE_CASES.exists() else None
    data = data or {"cases": []}
    have = {c["id"] for c in data["cases"]}
    for c in cases:
        if c["id"] not in have:
            data["cases"].append({k: v for k, v in c.items() if k != "needs_check"})
    PRIVATE_CASES.write_text("# Mined from David's real requests (gitignored).\n" +
                             yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return PRIVATE_CASES


# ---------- scorecard ----------

def scorecard(traces: list[dict], feedback: list[dict], latest: dict | None = None, days: int = 7) -> list[str]:
    """One line per agent: offline score, online proxy (accepted without edit), cost, top failure."""
    cutoff = dt.datetime.now() - dt.timedelta(days=days)
    route = {}
    cost = defaultdict(list)
    for t in traces:
        if dt.datetime.fromisoformat(t["ts"]) < cutoff:
            continue
        if t.get("event") == "intake":
            route[t["task"]] = (t.get("route") or {}).get("agent", "chief-of-staff")
        elif t.get("event") == "result" and t["task"] in route:
            cost[route[t["task"]]].append(float(t.get("cost_usd") or 0))
    fb = defaultdict(Counter)
    fails = defaultdict(list)
    for f in feedback:
        agent = route.get(f["task"]) or (f.get("route") or {}).get("agent")
        if not agent:
            continue
        kind = "reject" if f["kind"] == "down" else f["kind"]
        fb[agent][kind] += 1
        if kind in ("edit", "reject") and f.get("note"):
            fails[agent].append(f["note"])
    offline = defaultdict(lambda: [0, 0])
    for r in (latest or {}).get("rows", []):
        if r.get("agent"):
            offline[r["agent"]][0] += r["pass_all"]
            offline[r["agent"]][1] += 1
    lines = ["agent | tasks | offline pass | accepted w/o edit | avg cost | top failure", "---|---|---|---|---|---"]
    for agent in sorted(set(cost) | set(fb) | set(offline)):
        n = len(cost[agent])
        labelled = sum(fb[agent].values())
        acc = f"{fb[agent]['accept']}/{labelled}" if labelled else "-"
        off = f"{offline[agent][0]}/{offline[agent][1]}" if offline[agent][1] else "-"
        avg = f"${sum(cost[agent]) / n:.3f}" if n else "-"
        top = Counter(fails[agent]).most_common(1)[0][0][:60] if fails[agent] else "-"
        lines.append(f"{agent} | {n} | {off} | {acc} | {avg} | {top}")
    return lines
