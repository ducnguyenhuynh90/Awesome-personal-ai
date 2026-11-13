import datetime as dt
import json

from robin import checkin, routines
from robin.registry import load_agents


def test_repo_routines_valid_and_off():
    assert routines.validate(set(load_agents())) == []
    assert all(not r["enabled"] for r in routines.load().values())


def test_validator_rejects_bad_contract(tmp_path):
    bad = tmp_path / "r.yaml"
    bad.write_text("routines:\n  x:\n    enabled: true\n    owner: nobody\n    trigger: {cron: 'bad'}\n"
                   "    deliver_to: slack\n    on_source_down: use_cache\n")
    errs = routines.validate({"research-lead"}, bad)
    joined = " ".join(errs)
    for needle in ("'ask' missing", "not an agent", "trigger needs", "deliver_to", "report_failure"):
        assert needle in joined


def test_limits_and_silent_slowdown(tmp_path, monkeypatch):
    monkeypatch.setattr(routines, "RUN_LOG", tmp_path / "routines.jsonl")
    r = {"enabled": True, "max_runs_per_day": 2, "end_date": None}
    assert routines.can_run("x", r)[0]
    for _ in range(3):
        routines.log_run("x", "silent")
    ok, why = routines.can_run("x", {**r, "max_runs_per_day": 9})
    assert not ok and "silent" in why                     # 3 silent in a row -> slow down
    assert not routines.can_run("x", {**r, "end_date": "2020-01-01"})[0]
    assert not routines.can_run("x", {**r, "enabled": False})[0]


def test_proactive_prompt_is_read_only_and_silent_by_default():
    p = routines.proactive_prompt("knowledge-scan", routines.load()["knowledge-scan"])
    assert "SILENT" in p and "FAILED" in p and "cannot send" in p


def test_checkin_silent_when_nothing_and_skips_when_active(tmp_path, monkeypatch):
    monkeypatch.setattr(checkin, "LOG", tmp_path / "checkins.jsonl")
    monkeypatch.setattr(checkin, "digest", lambda: [])
    monkeypatch.setattr(checkin, "_last_owner_activity", lambda: None)
    assert checkin.run()["status"] == "silent"
    now = dt.datetime(2026, 11, 13, 10, 0)
    monkeypatch.setattr(checkin, "_last_owner_activity", lambda: now - dt.timedelta(minutes=5))
    assert checkin.run(now)["status"] == "skipped"
    monkeypatch.setattr(checkin, "digest", lambda: ["1 proposal needs your go"])
    assert checkin.run(now + dt.timedelta(hours=1))["status"] == "message"
    assert len((tmp_path / "checkins.jsonl").read_text().splitlines()) == 3
