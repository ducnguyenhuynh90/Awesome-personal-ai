import datetime as dt
import itertools

from robin import evalkit

CASE = {"id": "c1", "suite": "regression", "_source": "public", "request": "q", "checks": ["line1_answers"]}
NEVER = {"id": "n1", "suite": "never", "_source": "public", "request": "deploy", "checks": ["refuses"]}


def runner_from(outputs):
    it = itertools.cycle(outputs)
    return lambda req: {"output": next(it), "task": "t", "cost_usd": 0.01, "route": {"agent": "product-lead"}}


def test_runs_report_pass_every_time_vs_at_least_once():
    res = evalkit.run_cases([CASE], runs=3, runner=runner_from(["Yes, ship it.", "Great question! ...", "Yes."]))
    row = res["rows"][0]
    assert row["passes"] == 2 and row["pass_any"] and not row["pass_all"]   # flaky = blocks the gate
    assert not res["gate_ok"]


def test_never_suite_must_refuse():
    ok = evalkit.run_cases([NEVER], runner=runner_from(["I can't deploy: only David does that."]))
    bad = evalkit.run_cases([NEVER], runner=runner_from(["Deployed to production."]))
    assert ok["gate_ok"] and not bad["gate_ok"]


def test_capability_failures_do_not_block_gate():
    cap = {**CASE, "id": "k1", "suite": "capability"}
    assert evalkit.run_cases([cap], runner=runner_from(["Great question!"]))["gate_ok"]


def test_save_and_diff_show_flipped_cases(tmp_path, monkeypatch):
    monkeypatch.setattr(evalkit, "RESULTS", tmp_path)
    a = evalkit.save(evalkit.run_cases([CASE], runner=runner_from(["Great question!"])), "before")
    b = evalkit.save(evalkit.run_cases([CASE], runner=runner_from(["Yes."])), "after")
    out = evalkit.diff(a, b)
    assert out and out[0].startswith("FIXED") and "robin trace" in out[0]


def test_mine_uses_the_checks_that_would_have_caught_it(tmp_path, monkeypatch):
    fb = [{"task": "t9", "kind": "edit", "note": "too long", "request": "Explain D2",
           "output": "Great question! " + "word " * 200},
          {"task": "t8", "kind": "accept", "request": "x", "output": "fine"}]
    cases = evalkit.mine(fb)
    assert len(cases) == 1 and {"under_cap", "no_filler"} <= set(cases[0]["checks"])
    monkeypatch.setattr(evalkit, "PRIVATE_CASES", tmp_path / "private" / "cases.yaml")
    evalkit.append_private(cases)
    evalkit.append_private(cases)                                  # idempotent
    assert (tmp_path / "private" / "cases.yaml").read_text().count("mined-t9") == 1


def test_scorecard_line_per_agent():
    now = dt.datetime.now().isoformat(timespec="seconds")
    traces = [{"ts": now, "task": "t1", "event": "intake", "route": {"agent": "data-analyst"}},
              {"ts": now, "task": "t1", "event": "result", "cost_usd": 0.2},
              {"ts": now, "task": "t2", "event": "intake", "route": {"agent": "data-analyst"}},
              {"ts": now, "task": "t2", "event": "result", "cost_usd": 0.4}]
    fb = [{"task": "t1", "kind": "accept"}, {"task": "t2", "kind": "edit", "note": "wrong cohort"}]
    lines = evalkit.scorecard(traces, fb)
    row = next(l for l in lines if l.startswith("data-analyst"))
    assert "| 2 |" in row and "1/2" in row and "$0.300" in row and "wrong cohort" in row


def test_repo_cases_have_suites_and_never_cases():
    cases = evalkit.load_cases()
    assert all(c["suite"] in ("regression", "never", "capability") for c in cases)
    assert sum(c["suite"] == "never" for c in cases) >= 6
