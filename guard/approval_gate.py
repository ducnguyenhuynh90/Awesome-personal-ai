"""PreToolUse approval gate. Default deny for every tool that changes the outside world.

Approved by David 2026-11-13 ("go all"), from Meta Muse (Sentinel, taint), OpenAI dots (action rules) and
xAI Grok Bot (approval memory):

Order of checks for a tool call:
 1. Hard handoff: money, credentials, permissions, deploys, deletes, publishing — David does these himself.
    No rule, token or grant can allow them.
 2. Read-only connector: a tool from a connector with `send: false` (config/integrations.yaml) never writes.
 3. Circuit breaker: 3 denials in a row in one task stop every further write in that task.
 4. Reads, Robin's own kb tools, drafts in work/ and outbox/, read-only shell: allowed.
 5. Action rules (config/action_rules.yaml): auto | when_told | ask | handoff. Unmatched writes = ask.
    `auto` and standing grants do NOT apply once the task is tainted (it read untrusted content).
 6. Grants (approvals/<task>.json, written only by `robin approve`): scope once (consumed) | task | until:DATE,
    tool pattern plus optional exact input match. Standing grants (approvals/standing.json) need an end date.
Denials tell the agent not to retry; `ask` leaves approvals/<task>.pending.json for David's check-in.
"""
from __future__ import annotations

import datetime as dt
import fnmatch
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
APPROVALS = ROOT / "approvals"
RULES_FILE = ROOT / "config" / "action_rules.yaml"
INTEGRATIONS_FILE = ROOT / "config" / "integrations.yaml"

READ_ONLY_TOOLS = {
    "Read", "Glob", "Grep", "WebSearch", "WebFetch", "TodoWrite", "Task", "Agent", "Skill", "ToolSearch",
}
LOCAL_WRITE_TOOLS = {"Write", "Edit", "NotebookEdit"}
LOCAL_WRITE_ALLOWED = ["work/*", "outbox/*"]

# Robin's own in-process tools; writes go through robin.kb.writer.
INTERNAL_PREFIXES = ("mcp__kb__",)

# MCP tools whose verb is read-only. Anything else under mcp__ is a write.
MCP_READ_VERBS = ("get", "list", "search", "read", "fetch", "query", "find", "describe", "view", "retrieve", "download")
# Generic command tools (e.g. PostHog `exec`) count as reads unless the command names a write.
WRITE_WORDS = re.compile(r"\b(create|update|delete|remove|patch|post|send|set|add|edit|write|archive|enable|disable)\b", re.I)

# Bash: allow a small read-only set; everything else needs approval.
BASH_READ_ONLY = ("ls ", "cat ", "head ", "tail ", "wc ", "grep ", "rg ", "jq ", "git log", "git show", "git diff --stat", "robin kb query", "robin kb stale", "robin route")
BASH_BLOCK_CHARS = (">", "|", ";", "&", "`", "$(", "\n")

# Always handed to David (OpenAI dots: some actions are always human). Matched on the tool's action name.
HARD_HANDOFF = re.compile(
    r"pay|payment|transfer|refund|payout|withdraw|password|credential|secret|token|permission|role|grant|share_file|"
    r"deploy|release|merge|delete|remove|drop|trash|publish", re.I)
BREAKER_LIMIT = 3
BEHAVIOURS = {"auto", "when_told", "ask", "handoff"}
NO_RETRY = " Do not retry this call."


# ---------- task state: taint and denial streak ----------

def _state_path(task_id: str) -> Path:
    return APPROVALS / "_state" / f"{task_id}.json"


def _state(task_id: str | None) -> dict:
    if not task_id:
        return {"tainted": False, "denials": 0}
    p = _state_path(task_id)
    return json.loads(p.read_text()) if p.exists() else {"tainted": False, "denials": 0}


def _save_state(task_id: str | None, st: dict) -> None:
    if not task_id:
        return
    path = _state_path(task_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(st))


def mark_tainted(task_id: str | None, source: str = "") -> None:
    """Called when a task reads untrusted content (Meta Muse taint)."""
    if not task_id:
        return
    st = _state(task_id)
    if not st.get("tainted"):
        st["tainted"] = True
        st["taint_source"] = source
        _save_state(task_id, st)


def is_tainted(task_id: str | None) -> bool:
    return bool(_state(task_id).get("tainted"))


# ---------- config ----------

def _action(tool: str) -> str:
    """Action name without the connector prefix: mcp__Slack__slack_read_channel -> read_channel."""
    if not tool.startswith("mcp__"):
        return tool
    parts = tool.split("__")
    action = parts[-1]
    conn = parts[1].lower() if len(parts) >= 3 else ""
    for sep in ("_", "-"):
        if conn and action.lower().startswith(conn + sep):
            return action[len(conn) + 1:]
    return action


def _connector(tool: str) -> str | None:
    parts = tool.split("__")
    return parts[1].lower() if tool.startswith("mcp__") and len(parts) >= 3 else None


def _rules() -> list[dict]:
    if not RULES_FILE.exists():
        return []
    rules = (yaml.safe_load(RULES_FILE.read_text()) or {}).get("rules") or []
    return [r for r in rules if r.get("behaviour") in BEHAVIOURS and r.get("pattern")]


def _read_only_connectors() -> set[str]:
    if not INTEGRATIONS_FILE.exists():
        return set()
    mcp = (yaml.safe_load(INTEGRATIONS_FILE.read_text()) or {}).get("mcp") or {}
    return {name.lower() for name, item in mcp.items() if item.get("send") is False}


def _behaviour(tool: str) -> str:
    for r in _rules():
        if fnmatch.fnmatch(tool, r["pattern"]):
            return r["behaviour"]
    return "ask"


def _read_actions() -> dict[str, set[str]]:
    if not INTEGRATIONS_FILE.exists():
        return {}
    mcp = (yaml.safe_load(INTEGRATIONS_FILE.read_text()) or {}).get("mcp") or {}
    return {n.lower(): {a.lower() for a in (i.get("read_actions") or [])} for n, i in mcp.items()}


def _is_mcp_read(tool: str, tool_input: dict | None = None) -> bool:
    action = _action(tool).lower()
    if action.startswith(MCP_READ_VERBS):
        return True
    conn = _connector(tool)
    if conn and action in _read_actions().get(conn, set()):
        return not WRITE_WORDS.search(json.dumps(tool_input or {}))
    return False


# ---------- grants ----------

def _grant_matches(g: dict, tool: str, tool_input: dict, today: dt.date) -> bool:
    if not fnmatch.fnmatch(tool, g.get("tool", "")):
        return False
    for k, v in (g.get("input") or {}).items():  # exact match on the target (channel, recipient, page...)
        if str(tool_input.get(k)) != str(v):
            return False
    scope = str(g.get("scope", "once"))
    if scope.startswith("until:"):
        return today <= dt.date.fromisoformat(scope.split(":", 1)[1])
    return scope in ("once", "task")


def _load_token(path: Path) -> dict:
    try:
        token = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    if token.get("approved_by") != "david":
        return {}
    if "grants" not in token and "tools" in token:  # legacy format: task-scoped tool list
        token["grants"] = [{"tool": t, "scope": "task"} for t in token["tools"]]
    return token


def _use_grant(task_id: str | None, tool: str, tool_input: dict, tainted: bool) -> str | None:
    """Return a reason string if a grant allows the call, else None. Consumes `once` grants."""
    today = dt.date.today()
    if task_id:
        path = APPROVALS / f"{task_id}.json"
        token = _load_token(path) if path.exists() else {}
        for i, g in enumerate(token.get("grants", [])):
            if _grant_matches(g, tool, tool_input, today):
                if g.get("scope", "once") == "once":
                    token["grants"].pop(i)
                    path.write_text(json.dumps(token, indent=1))
                return f"grant ({g.get('scope', 'once')}) for task {task_id}"
    if not tainted:
        standing = APPROVALS / "standing.json"
        token = _load_token(standing) if standing.exists() else {}
        for g in token.get("grants", []):
            if str(g.get("scope", "")).startswith("until:") and _grant_matches(g, tool, tool_input, today):
                return f"standing grant ({g['scope']})"
    return None


def approve(task_id: str | None, tool: str, scope: str = "once", input_match: dict | None = None,
            standing: bool = False) -> Path:
    """Write a grant. Called only from David's CLI (`robin approve`), never by agents."""
    if HARD_HANDOFF.search(_action(tool)):
        raise ValueError(f"'{tool}' is a hand-off action (money, credentials, permissions, deploy, delete, publish): "
                         "David does it himself; it cannot be approved for an agent.")
    if scope not in ("once", "task") and not re.match(r"^until:\d{4}-\d{2}-\d{2}$", scope):
        raise ValueError("scope must be once | task | until:YYYY-MM-DD")
    if standing and not scope.startswith("until:"):
        raise ValueError("standing grants need an end date: --scope until:YYYY-MM-DD")
    APPROVALS.mkdir(exist_ok=True)
    path = APPROVALS / ("standing.json" if standing else f"{task_id}.json")
    token = _load_token(path) if path.exists() else {}
    token = token or {"approved_by": "david", "grants": []}
    token["grants"].append({"tool": tool, "scope": scope, **({"input": input_match} if input_match else {})})
    path.write_text(json.dumps(token, indent=1))
    pending = APPROVALS / f"{task_id}.pending.json"
    if task_id and pending.exists():
        pending.unlink()
    return path


def _leave_pending(task_id: str | None, tool: str, tool_input: dict) -> None:
    if not task_id:
        return
    APPROVALS.mkdir(exist_ok=True)
    keys = {k: v for k, v in tool_input.items() if isinstance(v, (str, int)) and len(str(v)) < 200}
    (APPROVALS / f"{task_id}.pending.json").write_text(json.dumps({"task": task_id, "tool": tool, "input": keys}, indent=1))


# ---------- decision ----------

def decide(tool: str, tool_input: dict, task_id: str | None = None, cwd: Path = ROOT) -> tuple[str, str]:
    """Return (decision, reason). decision is 'allow' or 'deny'."""
    decision, reason = _decide(tool, tool_input, task_id, cwd)
    st = _state(task_id)
    if decision == "deny":
        st["denials"] = st.get("denials", 0) + 1
        reason += NO_RETRY
    elif not _is_read(tool, tool_input, cwd):
        st["denials"] = 0  # an allowed write resets the streak
    _save_state(task_id, st)
    return decision, reason


def _is_read(tool: str, tool_input: dict, cwd: Path) -> bool:
    return tool in READ_ONLY_TOOLS or tool.startswith(INTERNAL_PREFIXES) or (tool.startswith("mcp__") and _is_mcp_read(tool, tool_input))


def _decide(tool: str, tool_input: dict, task_id: str | None, cwd: Path) -> tuple[str, str]:
    action = _action(tool)
    if tool.startswith("mcp__") and not _is_mcp_read(tool, tool_input) and HARD_HANDOFF.search(action):
        return "deny", f"'{tool}' is a hand-off action (money, credentials, permissions, deploy, delete, publish): David does it himself."
    conn = _connector(tool)
    if conn and conn in _read_only_connectors() and not _is_mcp_read(tool, tool_input):
        return "deny", f"connector '{conn}' is read-only (send: false in config/integrations.yaml)."
    if tool in READ_ONLY_TOOLS:
        return "allow", "read-only tool"
    if tool.startswith(INTERNAL_PREFIXES):
        return "allow", "internal knowledge tool (locked writer, secret redaction, lint)"
    if tool.startswith("mcp__") and _is_mcp_read(tool, tool_input):
        return "allow", "read-only MCP tool"
    st = _state(task_id)
    if st.get("denials", 0) >= BREAKER_LIMIT:
        return "deny", f"circuit breaker: {st['denials']} denials in a row in this task. Stop and report to David."
    if tool in LOCAL_WRITE_TOOLS:
        path = Path(tool_input.get("file_path", ""))
        try:
            rel = path.resolve().relative_to(cwd.resolve()).as_posix()
        except ValueError:
            rel = ""
        if rel and any(fnmatch.fnmatch(rel, p) for p in LOCAL_WRITE_ALLOWED):
            return "allow", "local draft write"
    if tool == "Bash":
        cmd = (tool_input.get("command") or "").strip()
        if cmd.startswith(BASH_READ_ONLY) and not any(c in cmd for c in BASH_BLOCK_CHARS):
            return "allow", "read-only shell command"
        if HARD_HANDOFF.search(cmd):
            return "deny", "this shell command is a hand-off action (deploy, delete, credentials, money, publish): David runs it himself."

    tainted = bool(st.get("tainted"))
    behaviour = _behaviour(tool)
    if behaviour == "handoff":
        return "deny", f"'{tool}' is set to hand off (config/action_rules.yaml): David does it himself."
    if behaviour == "auto" and not tainted:
        return "allow", "action rule: auto"
    granted = _use_grant(task_id, tool, tool_input, tainted)
    if granted:
        return "allow", granted
    if behaviour == "ask":
        _leave_pending(task_id, tool, tool_input)
    taint_note = " This task read untrusted content, so auto rules and standing grants do not apply." if tainted else ""
    return "deny", (
        f"'{tool}' changes something outside Robin's drafts. Save a draft in outbox/; David approves with "
        f"`robin approve {task_id or '<task>'} {tool}`.{taint_note}"
    )


def make_hook(task_id: str | None):
    """Build an Agent SDK PreToolUse hook callback bound to a task id."""

    async def hook(input_data, tool_use_id, context):  # noqa: ARG001 - SDK signature
        decision, reason = decide(input_data.get("tool_name", ""), input_data.get("tool_input") or {}, task_id)
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": reason,
            }
        }

    return hook
