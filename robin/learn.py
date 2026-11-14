"""Craft-learning loop (spec §8) with the Grok Bot rule: a correction becomes a principle, never a story.

1. `robin feedback <task> --down "why"` or `--edit corrected.md` stores David's signal (gitignored feedback/).
2. `robin learn` turns the strongest new signal into ONE general rule for ONE agent or skill:
   - signal order: edit diffs > 👎 (spec §8)
   - overfit check: would it make sense to someone who wasn't there? No numbers, dates, URLs, names,
     company terms, or long quotes from the task; <= 30 words; not a duplicate of an existing pitfall.
   - weekly cap: at most one proposal per ISO week (silence is the default).
3. The proposal is a file in docs/proposals/. David applies it with `robin learn --apply <file>`.
"""
from __future__ import annotations

import datetime as dt
import difflib
import json
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from robin import frontmatter, trace
from robin.registry import load_agents, load_skills

ROOT = Path(__file__).resolve().parent.parent
FEEDBACK = ROOT / "feedback"
PROPOSALS = ROOT / "docs" / "proposals"
STATE = FEEDBACK / "_learn_state.json"
MAX_RULE_WORDS = 30
SIGNAL_RANK = {"edit": 0, "down": 1}


# ---------- capture ----------

def record(task_id: str, kind: str, note: str = "", corrected: str = "") -> Path:
    if kind not in SIGNAL_RANK:
        raise ValueError("kind must be 'edit' or 'down'")
    recs = trace.read(task_id)
    result = next((r for r in reversed(recs) if r.get("event") == "result"), {})
    intake = next((r for r in recs if r.get("event") == "intake"), {})
    FEEDBACK.mkdir(exist_ok=True)
    entry = {
        "ts": dt.datetime.now().isoformat(timespec="seconds"), "task": task_id, "kind": kind, "note": note,
        "request": intake.get("request", ""), "route": intake.get("route", {}),
        "output": result.get("output", ""), "corrected": corrected,
    }
    path = FEEDBACK / f"{dt.date.today().isoformat()}.jsonl"
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return path


def _all_feedback() -> list[dict]:
    out = []
    for f in sorted(FEEDBACK.glob("*.jsonl")):
        out += [json.loads(line) for line in f.read_text(encoding="utf-8").splitlines() if line.strip()]
    return out


def _state() -> dict:
    return json.loads(STATE.read_text()) if STATE.exists() else {"seen": [], "weeks": []}


def _save_state(s: dict) -> None:
    FEEDBACK.mkdir(exist_ok=True)
    STATE.write_text(json.dumps(s, indent=1))


def _week(d: dt.date | None = None) -> str:
    y, w, _ = (d or dt.date.today()).isocalendar()
    return f"{y}-W{w:02d}"


# ---------- overfit check ----------

def _company_terms() -> set[str]:
    path = ROOT / "harness" / "private" / "company.yaml"
    if not path.exists():
        return set()
    data = yaml.safe_load(path.read_text()) or {}
    terms: set[str] = set()

    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                walk(k); walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        elif isinstance(x, str) and len(x) >= 3:
            terms.add(x.lower())
    walk(data)
    return terms


def overfit_problems(rule: str, signal: dict, existing: list[str]) -> list[str]:
    """Empty list = the rule generalises. Each item is a reason to reject it."""
    p = []
    words = rule.split()
    if not words:
        return ["empty rule"]
    if len(words) > MAX_RULE_WORDS:
        p.append(f"over {MAX_RULE_WORDS} words")
    if re.search(r"\d", rule):
        p.append("contains a number or date (story, not principle)")
    if re.search(r"https?://|www\.", rule):
        p.append("contains a URL")
    if any(t in rule.lower() for t in _company_terms()):
        p.append("contains a company term (would leak into the public repo)")
    # Long verbatim quotes from the task = story, not principle.
    task_text = " ".join([signal.get("request", ""), signal.get("output", ""), signal.get("corrected", "")]).lower()
    for i in range(len(words) - 5):
        if " ".join(words[i:i + 6]).lower() in task_text:
            p.append("quotes the task verbatim (6+ words)")
            break
    # Mid-sentence capitalised words usually mean names.
    names = [w for w in words[1:] if re.match(r"^[A-Z][a-z]{2,}", w) and words[words.index(w) - 1][-1:] not in ".:;"]
    if names:
        p.append(f"looks like it names something specific: {names[:3]}")
    for e in existing:
        if difflib.SequenceMatcher(None, rule.lower(), e.lower()).ratio() > 0.8:
            p.append("duplicates an existing pitfall")
            break
    return p


# ---------- reflect ----------

@dataclass
class Proposal:
    target: str        # agent or skill name
    target_kind: str   # "skill" | "agent"
    rule: str
    signal: dict
    path: Path | None = None


def _existing_pitfalls(target_kind: str, target: str) -> list[str]:
    path = (ROOT / ".claude" / "skills" / target / "SKILL.md") if target_kind == "skill" else (ROOT / ".claude" / "agents" / f"{target}.md")
    if not path.exists():
        return []
    return [ln[2:].strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.startswith("- ")]


def _target_for(signal: dict) -> tuple[str, str]:
    route = signal.get("route") or {}
    skills = route.get("skills") or []
    if skills and skills[0] in load_skills():
        return "skill", skills[0]
    agent = route.get("agent") or "chief-of-staff"
    return "agent", agent if agent in load_agents() else "chief-of-staff"


def diff_text(signal: dict) -> str:
    if not signal.get("corrected"):
        return ""
    return "\n".join(difflib.unified_diff(signal.get("output", "").splitlines(), signal["corrected"].splitlines(),
                                          "robin", "david", lineterm="", n=1))


def learn(reflect, today: dt.date | None = None) -> Proposal | None:
    """Make at most one proposal this week. `reflect(signal, diff, target) -> rule` (cheap model in prod)."""
    st = _state()
    week = _week(today)
    if week in st["weeks"]:
        return None  # weekly cap: silence
    new = [s for s in _all_feedback() if f"{s['task']}:{s['ts']}" not in st["seen"]]
    if not new:
        return None
    new.sort(key=lambda s: (SIGNAL_RANK[s["kind"]], s["ts"]))
    for signal in new:
        kind, target = _target_for(signal)
        rule = (reflect(signal, diff_text(signal), target) or "").strip().strip('"').rstrip(".") + "."
        st["seen"].append(f"{signal['task']}:{signal['ts']}")
        if overfit_problems(rule.rstrip("."), signal, _existing_pitfalls(kind, target)):
            continue  # rejected; try the next signal
        prop = Proposal(target, kind, rule, signal)
        PROPOSALS.mkdir(parents=True, exist_ok=True)
        prop.path = PROPOSALS / f"learn-{week}.md"
        prop.path.write_text(
            f"# Learning proposal {week}\n\nStatus: awaiting David. Apply: `robin learn --apply {prop.path.relative_to(ROOT)}`\n\n"
            f"- target: {kind} `{target}`\n- signal: {signal['kind']} on task {signal['task']}\n"
            f"- rule: {rule}\n\nThe task's content is not copied here (public repo); see feedback/ locally.\n",
            encoding="utf-8")
        st["weeks"].append(week)
        _save_state(st)
        return prop
    _save_state(st)
    return None


def apply(proposal_path: Path) -> str:
    text = proposal_path.read_text(encoding="utf-8")
    kind = re.search(r"- target: (skill|agent) `([^`]+)`", text)
    rule = re.search(r"- rule: (.+)", text)
    if not (kind and rule):
        raise ValueError("not a learning proposal")
    k, target = kind.groups()
    path = (ROOT / ".claude" / "skills" / target / "SKILL.md") if k == "skill" else (ROOT / ".claude" / "agents" / f"{target}.md")
    meta, body = frontmatter.read(path)
    line = f"- {rule.group(1).strip()} (learned {dt.date.today().isoformat()})"
    if "## Pitfalls (learned)" in body:
        body = body.rstrip("\n") + "\n" + line + "\n"
    else:
        body = body.rstrip("\n") + "\n\n## Pitfalls (learned)\n\n" + line + "\n"
    path.write_text(frontmatter.dump(meta, body), encoding="utf-8")
    proposal_path.write_text(text.replace("Status: awaiting David.", f"Status: applied {dt.date.today().isoformat()}."),
                             encoding="utf-8")
    return f"{k} {target}: {line}"


def cheap_reflect(signal: dict, diff: str, target: str) -> str:
    """Production reflector: one general rule from one signal, using the cheap model tier."""
    import asyncio

    from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query
    models = yaml.safe_load((ROOT / "config" / "models.yaml").read_text())
    prompt = (
        f"David corrected an answer from `{target}`. Write ONE general rule (max {MAX_RULE_WORDS} words) that would have "
        "prevented the problem in any future task. Write the principle, not the story: no numbers, dates, names, "
        "products, markets or quotes from this task. Someone who wasn't there must understand it. Output only the rule.\n\n"
        f"<request>{signal.get('request', '')}</request>\n<robin_output>{signal.get('output', '')[:3000]}</robin_output>\n"
        f"<david_note>{signal.get('note', '')}</david_note>\n<diff>{diff[:3000]}</diff>"
    )

    async def go():
        out = ""
        opts = ClaudeAgentOptions(model=models["tiers"]["cheap"], allowed_tools=[], max_turns=1,
                                  system_prompt="You turn one correction into one general rule.")
        async for m in query(prompt=prompt, options=opts):
            if isinstance(m, ResultMessage):
                out = m.result or ""
        return out

    return asyncio.run(go())
