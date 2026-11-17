"""Memory retrieval eval: precision / recall / F1 of `kb query` on a synthetic fixture KB."""
from __future__ import annotations

import importlib
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixture" / "knowledge"


def _point_kb_at(path: Path) -> dict:
    from robin.kb import schema
    saved = {"schema": (schema.KB, schema.SOURCES)}
    schema.KB, schema.SOURCES = path, path / "_sources"
    for name in ("lint", "index", "query", "writer"):
        mod = importlib.import_module(f"robin.kb.{name}")
        saved[name] = getattr(mod, "KB", None)
        mod.KB = path
    return saved


def _restore(saved: dict) -> None:
    from robin.kb import schema
    schema.KB, schema.SOURCES = saved["schema"]
    for name in ("lint", "index", "query", "writer"):
        importlib.import_module(f"robin.kb.{name}").KB = saved[name]


def run(cases_path: Path = HERE / "cases.yaml", limit: int = 5) -> dict:
    cases = yaml.safe_load(cases_path.read_text())["cases"]
    saved = _point_kb_at(FIXTURE)
    try:
        from robin.kb.query import query
        rows = []
        for c in cases:
            got = [line.split(" ")[0] for line in query(near=c.get("near"), hops=int(c.get("hops", 1)),
                                                         market=c.get("market"), type_=c.get("type"),
                                                         text=c.get("text"), limit=limit)]
            exp = set(c["expect"])
            hit = exp & set(got)
            p = len(hit) / len(got) if got else 0.0
            r = len(hit) / len(exp)
            rows.append({"id": c["id"], "precision": p, "recall": r, "got": got, "expect": sorted(exp)})
    finally:
        _restore(saved)
    n = len(rows)
    P = sum(x["precision"] for x in rows) / n
    R = sum(x["recall"] for x in rows) / n
    F = 2 * P * R / (P + R) if P + R else 0.0
    return {"precision": P, "recall": R, "f1": F, "rows": rows}
