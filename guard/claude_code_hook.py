"""Claude Code hook: applies Robin's approval gate inside Claude Code sessions (cloud or local).

Approved by David 2026-11-14. Registered in .claude/settings.json for PreToolUse and PostToolUse.

Scope: company connector tools (mcp__<connector>__<action>). Repo work (Read/Write/Edit/Bash/git) is left to
Claude Code's own permissions, so developing Robin is not blocked. Exempt: Robin's own kb tools and the
session's infrastructure / dev tools listed in EXEMPT_PREFIXES.

PreToolUse : connector writes go through guard.approval_gate.decide() with the session id as the task id.
             Allowed calls print nothing (Claude Code's normal permissions still apply); denied calls are blocked.
PostToolUse: WebFetch / WebSearch / connector reads mark the session tainted (Meta Muse pattern).
Approve one write for a session: `robin approve <session-id> <tool>` (the deny message shows both).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from guard import approval_gate  # noqa: E402

EXEMPT_PREFIXES = (
    "mcp__kb__",                    # Robin's own knowledge tools (locked writer)
    "mcp__claude-code-remote__",    # session infrastructure (scheduling, sessions)
    "mcp__github__",                # repo development (PRs only when David asks)
)
TAINT_TOOLS = {"WebFetch", "WebSearch"}


def in_scope(tool: str) -> bool:
    return tool.startswith("mcp__") and not tool.startswith(EXEMPT_PREFIXES)


def handle(event: dict) -> dict | None:
    tool = event.get("tool_name", "")
    session = event.get("session_id") or None
    name = event.get("hook_event_name")
    if name == "PostToolUse":
        if tool in TAINT_TOOLS or (in_scope(tool) and approval_gate._is_mcp_read(tool, event.get("tool_input"))):
            approval_gate.mark_tainted(session, tool)
        return None
    if name != "PreToolUse" or not in_scope(tool):
        return None
    decision, reason = approval_gate.decide(tool, event.get("tool_input") or {}, session)
    if decision == "allow":
        return None  # defer to Claude Code's normal permission flow
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"Robin gate: {reason}" + (
                "" if "hand-off" in reason or "read-only" in reason or "circuit breaker" in reason
                else f" (David can run `robin approve {session} {tool}`)"),
        }
    }


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0  # never break the session on bad input
    out = handle(event)
    if out:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
