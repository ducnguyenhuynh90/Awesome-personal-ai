"""Knowledge base tests run against a temporary copy of knowledge/."""
import datetime as dt
import importlib
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def kb(tmp_path, monkeypatch):
    dst = tmp_path / "knowledge"
    shutil.copytree(ROOT / "knowledge", dst)
    from robin.kb import schema
    monkeypatch.setattr(schema, "KB", dst)
    monkeypatch.setattr(schema, "SOURCES", dst / "_sources")
    mods = {}
    for name in ("lint", "index", "query", "writer"):
        mod = importlib.import_module(f"robin.kb.{name}")
        monkeypatch.setattr(mod, "KB", dst, raising=False)
        mods[name] = mod
    monkeypatch.setattr(mods["writer"], "SOURCES", dst / "_sources")
    monkeypatch.setattr(mods["writer"], "LOCK", dst / ".write.lock")
    return mods


def test_repo_kb_lints_clean():
    from robin.kb import lint
    assert lint.lint() == []


def test_add_source_fact_and_lint(kb):
    w = kb["writer"]
    sid = w.add_source("https://example.gov/rule", "Rule text. Contact @someuser or a@b.com. "
                       "key: postgres://u:Secr3tPass@h/db", "A", "Regulator page on deposits")
    body = (kb["lint"].KB / "_sources" / f"{sid}.md").read_text()
    assert "Secr3tPass" not in body and "@someuser" not in body and "a@b.com" not in body
    w.add_fact("market-ph", "Example fact for test", [sid], "A")
    kb["index"].build()
    assert kb["lint"].lint() == []
    text = (kb["lint"].KB / "markets" / "market-ph.md").read_text()
    assert f"— [[{sid}]] — A" in text


def test_fact_needs_existing_source(kb):
    with pytest.raises(kb["writer"].KBWriteError):
        kb["writer"].add_fact("market-ph", "no source", [], "A")
    with pytest.raises(kb["writer"].KBWriteError):
        kb["writer"].add_fact("market-ph", "bad source", ["src-9999"], "A")


def test_lint_catches_bad_edge_and_link(kb):
    path = kb["lint"].KB / "markets" / "market-mx.md"
    text = path.read_text().replace("## Relations\n", "## Relations\n- likes [[market-zz]]\n")
    path.write_text(text)
    errors = kb["lint"].lint()
    assert any("not in closed vocabulary" in e for e in errors)
    assert any("[[market-zz]] has no file" in e for e in errors)


def test_lint_catches_bad_fact_line(kb):
    path = kb["lint"].KB / "markets" / "market-th.md"
    path.write_text(path.read_text().replace("## Facts\n", "## Facts\n- TH uses phone login\n"))
    assert any("fact must be" in e for e in kb["lint"].lint())


def test_index_flips_expired_to_stale(kb):
    future = dt.date.today() + dt.timedelta(days=400)
    assert kb["lint"].lint(today=future)  # lint reports, does not edit
    out = kb["index"].build(today=future)
    assert len(out["flipped_to_stale"]) == 5
    assert kb["query"].stale(today=future)


def test_query_graph_hops(kb):
    w = kb["writer"]
    w.create_node("competitor-acme", "competitor", "Test competitor in PH", markets=["ph"])
    path = kb["lint"].KB / "competitors" / "competitor-acme.md"
    path.write_text(path.read_text().replace("## Relations\n", "## Relations\n- operates_in [[market-ph]]\n"))
    kb["index"].build()
    near = kb["query"].query(near="market-ph", hops=1)
    assert any(line.startswith("competitor-acme") for line in near)
    assert kb["lint"].lint() == []


def test_index_md_under_cap():
    from robin.kb import schema
    words = len((schema.KB / "INDEX.md").read_text().split())
    assert words <= 300
