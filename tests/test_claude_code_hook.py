import pytest

from guard import approval_gate as g
from guard import claude_code_hook as h


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(g, "APPROVALS", tmp_path / "approvals")
    monkeypatch.setattr(g, "RULES_FILE", tmp_path / "none.yaml")


def ev(tool, name="PreToolUse", inp=None, sid="s1"):
    return {"hook_event_name": name, "session_id": sid, "tool_name": tool, "tool_input": inp or {}}


def test_connector_reads_allowed_writes_denied():
    assert h.handle(ev("mcp__Slack__slack_read_channel")) is None
    assert h.handle(ev("mcp__Notion__notion-search")) is None
    out = h.handle(ev("mcp__Slack__slack_send_message"))
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "robin approve s1 mcp__Slack__slack_send_message" in out["hookSpecificOutput"]["permissionDecisionReason"]


def test_handoff_message_does_not_suggest_approve():
    reason = h.handle(ev("mcp__Google_Drive__share_file"))["hookSpecificOutput"]["permissionDecisionReason"]
    assert "hand-off" in reason and "robin approve" not in reason


def test_repo_work_and_infrastructure_untouched():
    for tool in ("Write", "Edit", "Bash", "mcp__github__create_pull_request",
                 "mcp__claude-code-remote__create_trigger", "mcp__kb__add_fact"):
        assert h.handle(ev(tool)) is None


def test_session_grant_allows_once():
    g.approve("s1", "mcp__Slack__slack_send_message")
    assert h.handle(ev("mcp__Slack__slack_send_message")) is None
    assert h.handle(ev("mcp__Slack__slack_send_message")) is not None


def test_post_tool_use_taints_session():
    h.handle(ev("WebFetch", name="PostToolUse"))
    assert g.is_tainted("s1")
    h.handle(ev("mcp__Gmail__get_message", name="PostToolUse", sid="s2"))
    assert g.is_tainted("s2")
    h.handle(ev("Read", name="PostToolUse", sid="s3"))
    assert not g.is_tainted("s3")
