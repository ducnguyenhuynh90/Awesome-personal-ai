"""PreToolUse approval gate. Default deny for every tool that changes the outside world.

A write is allowed only if the task carries an approval token that David issued
for that exact draft (`robin approve <draft-id>` writes approvals/<task-id>.json).
Local scratch writes inside work/ and outbox/ are allowed (drafts are the product).
Knowledge writes go through the single-writer queue (robin.kb.writer), not tools.
"""
from __future__ import annotations

import fnmatch
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APPROVALS = ROOT / "approvals"

READ_ONLY_TOOLS = {
    "Read", "Glob", "Grep", "WebSearch", "WebFetch", "TodoWrite", "Task", "Agent", "Skill", "ToolSearch",
}
LOCAL_WRITE_TOOLS = {"Write", "Edit", "NotebookEdit"}
LOCAL_WRITE_ALLOWED = ["work/*", "outbox/*"]

# Robin's own in-process tools; writes go through robin.kb.writer.
INTERNAL_PREFIXES = ("mcp__kb__",)

# MCP tools whose verb is read-only. Anything else under mcp__ is a write.
MCP_READ_VERBS = ("get", "list", "search", "read", "fetch", "query", "find", "describe", "view", "retrieve")

# Bash: allow a small read-only set; everything else needs approval.
BASH_READ_ONLY = ("ls ", "cat ", "head ", "tail ", "wc ", "grep ", "rg ", "jq ", "git log", "git show", "git diff --stat", "robin kb query", "robin kb stale", "robin route")
BASH_BLOCK_CHARS = (">", "|", ";", "&", "`", "$(", "\n")


def _is_mcp_read(tool: str) -> bool:
    verb = tool.split("__")[-1].lower()
    return verb.startswith(MCP_READ_VERBS)


def _approved(task_id: str | None, tool: str, tool_input: dict) -> bool:
    if not task_id:
        return False
    f = APPROVALS / f"{task_id}.json"
    if not f.exists():
        return False
    try:
        token = json.loads(f.read_text())
    except json.JSONDecodeError:
        return False
    allowed = token.get("tools", [])
    return token.get("approved_by") == "david" and any(fnmatch.fnmatch(tool, p) for p in allowed)


def decide(tool: str, tool_input: dict, task_id: str | None = None, cwd: Path = ROOT) -> tuple[str, str]:
    """Return (decision, reason). decision is 'allow' or 'deny'."""
    if tool in READ_ONLY_TOOLS:
        return "allow", "read-only tool"
    if tool.startswith(INTERNAL_PREFIXES):
        return "allow", "internal knowledge tool (locked writer, secret redaction, lint)"
    if tool.startswith("mcp__") and _is_mcp_read(tool):
        return "allow", "read-only MCP tool"
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
    if _approved(task_id, tool, tool_input):
        return "allow", f"approval token for task {task_id}"
    return "deny", (
        f"'{tool}' changes something outside Robin's drafts. Default deny: save a draft in outbox/ "
        "and ask David to reply 'go' for that draft."
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
