import datetime as dt
import json

import pytest

from robin import learn


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(learn, "FEEDBACK", tmp_path / "feedback")
    monkeypatch.setattr(learn, "STATE", tmp_path / "feedback" / "_learn_state.json")
    monkeypatch.setattr(learn, "PROPOSALS", tmp_path / "proposals")
    monkeypatch.setattr(learn, "ROOT", tmp_path)
    monkeypatch.setattr(learn, "_company_terms", lambda: {"kzwl"})
    (tmp_path / "feedback").mkdir()
    return tmp_path


def _signal(env, kind="edit", task="t-1", output="Long reply about GCash cashback in PH with 5% offer.",
            corrected="Short reply."):
    rec = {"ts": f"2026-11-13T10:00:0{task[-1]}", "task": task, "kind": kind, "note": "too long",
           "request": "Turn GCash cashback into an experiment", "route": {"agent": "product-lead", "skills": ["idea-to-hypothesis"]},
           "output": output, "corrected": corrected}
    with open(env / "feedback" / "2026-11-13.jsonl", "a") as fh:
        fh.write(json.dumps(rec) + "\n")


def test_overfit_rejects_stories():
    sig = {"request": "Turn GCash cashback into an experiment", "output": "", "corrected": ""}
    assert learn.overfit_problems("Never offer 5% cashback", sig, [])                     # number
    assert learn.overfit_problems("Check https://x.y first", sig, [])                    # url
    assert learn.overfit_problems("Turn GCash cashback into an experiment only when asked", sig, [])  # verbatim quote
    assert learn.overfit_problems("Put the full design in outbox and reply with three lines",
                                  sig, ["Put the full design in outbox and reply with three lines"])  # duplicate
    assert not learn.overfit_problems("Put tables and caveats in the outbox file and keep the reply to the decision",
                                      sig, [])


def test_one_proposal_per_week_and_edits_first(env):
    _signal(env, kind="down", task="t-1")
    _signal(env, kind="edit", task="t-2")
    seen = []

    def reflect(signal, diff, target):
        seen.append(signal["kind"])
        return "Keep the reply to the decision and move tables and caveats into the linked outbox file"

    today = dt.date(2026, 11, 13)
    prop = learn.learn(reflect, today)
    assert prop and seen == ["edit"]                       # edit diffs outrank 👎
    assert prop.target == "idea-to-hypothesis" and prop.target_kind == "skill"
    assert "GCash" not in prop.path.read_text()            # task content not copied to the public repo
    _signal(env, kind="edit", task="t-3")
    assert learn.learn(reflect, today) is None             # weekly cap
    assert learn.learn(reflect, today + dt.timedelta(days=7)) is not None


def test_rejected_rule_makes_no_proposal(env):
    _signal(env)
    assert learn.learn(lambda s, d, t: "Never offer 5% cashback on KZWL", dt.date(2026, 11, 13)) is None
    assert not (env / "proposals").exists()


def test_apply_adds_pitfall(env):
    skill = env / ".claude" / "skills" / "demo"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text("---\nname: demo\ndescription: d\n---\n\n# demo\n\n## Steps\n\n1. x\n")
    prop = env / "proposals" / "learn-2026-W46.md"
    prop.parent.mkdir()
    prop.write_text("# p\n\nStatus: awaiting David.\n\n- target: skill `demo`\n- signal: edit\n- rule: Lead with the decision.\n")
    out = learn.apply(prop)
    body = (skill / "SKILL.md").read_text()
    assert "## Pitfalls (learned)" in body and "- Lead with the decision." in body
    assert "Status: applied" in prop.read_text() and "demo" in out


def test_profile_provenance_and_forget_by_source(tmp_path):
    from robin import profile
    path = tmp_path / "profile.md"
    profile.remember("Weekly sync is Friday afternoon", source="calendar", path=path)
    profile.remember("Prefers tables for comparisons", source="david", status="done", path=path)
    text = path.read_text()
    assert "[source: calendar ·" in text and "status: done" in text
    removed = profile.forget(source="calendar", path=path)
    assert len(removed) == 1 and "Weekly sync" in removed[0]
    assert "Prefers tables" in path.read_text()
