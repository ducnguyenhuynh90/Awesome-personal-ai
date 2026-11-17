"""Gate v2 (approved by David 2026-11-13): handoff, read-only connectors, breaker, action rules, taint, grants."""
import datetime as dt
import json

import pytest

from guard import approval_gate as g


@pytest.fixture
def gate(tmp_path, monkeypatch):
    monkeypatch.setattr(g, "APPROVALS", tmp_path / "approvals")
    rules = tmp_path / "action_rules.yaml"
    rules.write_text("rules:\n  - {pattern: 'mcp__slack__*draft*', behaviour: auto}\n"
                     "  - {pattern: 'mcp__notion__*', behaviour: when_told}\n"
                     "  - {pattern: 'mcp__calendar__*', behaviour: handoff}\n")
    monkeypatch.setattr(g, "RULES_FILE", rules)
    integ = tmp_path / "integrations.yaml"
    integ.write_text("mcp:\n  posthog: {enabled: true, send: false}\n  slack: {enabled: true, send: true}\n")
    monkeypatch.setattr(g, "INTEGRATIONS_FILE", integ)
    return tmp_path


def test_hard_handoff_cannot_be_granted(gate):
    with pytest.raises(ValueError):
        g.approve("t1", "mcp__bank__transfer_funds")
    assert g.decide("mcp__bank__transfer_funds", {}, "t1")[0] == "deny"
    assert g.decide("mcp__github__merge_pull_request", {}, "t1")[0] == "deny"
    assert g.decide("Bash", {"command": "kubectl deploy app"}, "t1")[0] == "deny"


def test_read_only_connector_blocks_writes_even_with_grant(gate):
    g.approve("t1", "mcp__posthog__create_dashboard", scope="task")
    assert g.decide("mcp__posthog__create_dashboard", {}, "t1")[0] == "deny"
    assert g.decide("mcp__posthog__query_insights", {}, "t1")[0] == "allow"   # reads still fine


def test_action_rules(gate):
    assert g.decide("mcp__slack__send_message_draft", {}, "t1")[0] == "allow"      # auto
    assert g.decide("mcp__notion__update_page", {}, "t2")[0] == "deny"             # when_told, no grant
    assert not (gate / "approvals" / "t2.pending.json").exists()                   # when_told leaves no pending
    g.approve("t3", "mcp__calendar__create_event", scope="task")
    assert g.decide("mcp__calendar__create_event", {}, "t3")[0] == "deny"          # handoff beats grants
    assert g.decide("mcp__slack__send_message", {"channel": "C1"}, "t4")[0] == "deny"  # default = ask
    assert json.loads((gate / "approvals" / "t4.pending.json").read_text())["tool"] == "mcp__slack__send_message"


def test_taint_disables_auto_and_standing_but_not_task_grants(gate):
    g.approve(None, "mcp__slack__send_message", scope="until:2099-01-01", standing=True)
    assert g.decide("mcp__slack__send_message", {}, "t5")[0] == "allow"             # standing grant, clean task
    g.mark_tainted("t5", "WebFetch")
    assert g.decide("mcp__slack__send_message", {}, "t5")[0] == "deny"              # tainted: standing ignored
    assert g.decide("mcp__slack__send_message_draft", {}, "t5")[0] == "deny"        # tainted: auto ignored
    g.approve("t5", "mcp__slack__send_message")
    assert g.decide("mcp__slack__send_message", {}, "t5")[0] == "allow"             # explicit per-task grant works


def test_once_is_consumed_and_input_must_match(gate):
    g.approve("t6", "mcp__slack__send_message", input_match={"channel": "C1"})
    assert g.decide("mcp__slack__send_message", {"channel": "C2"}, "t6")[0] == "deny"   # wrong target
    assert g.decide("mcp__slack__send_message", {"channel": "C1"}, "t6")[0] == "allow"
    assert g.decide("mcp__slack__send_message", {"channel": "C1"}, "t6")[0] == "deny"   # consumed


def test_until_expires_and_standing_needs_date(gate):
    with pytest.raises(ValueError):
        g.approve(None, "mcp__slack__send_message", scope="task", standing=True)
    past = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    g.approve("t7", "mcp__slack__send_message", scope=f"until:{past}")
    assert g.decide("mcp__slack__send_message", {}, "t7")[0] == "deny"


def test_circuit_breaker_after_three_denials(gate):
    g.approve("t8", "mcp__slack__send_message", scope="task")
    for _ in range(3):
        assert g.decide("mcp__notion__update_page", {}, "t8")[0] == "deny"
    decision, reason = g.decide("mcp__slack__send_message", {}, "t8")
    assert decision == "deny" and "circuit breaker" in reason                      # even granted writes stop
    assert g.decide("Read", {}, "t8")[0] == "allow"                                 # reads continue


def test_denials_say_do_not_retry(gate):
    assert "Do not retry" in g.decide("mcp__slack__send_message", {}, "t9")[1]


def test_taint_sources():
    from robin.orchestrator import ROOT, taint_source
    assert taint_source("WebFetch", {}) == "WebFetch"
    assert taint_source("mcp__gmail__get_message", {})
    assert taint_source("mcp__kb__query", {}) == ""
    assert taint_source("Read", {"file_path": str(ROOT / "knowledge" / "_sources" / "src-0001.md")})
    assert taint_source("Read", {"file_path": str(ROOT / ".claude" / "agents" / "product-lead.md")}) == ""
