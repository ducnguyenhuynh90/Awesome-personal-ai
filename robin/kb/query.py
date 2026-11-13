"""kb query / kb stale — return node ids + one-line summaries for context injection."""
from __future__ import annotations

import datetime as dt
import json
from collections import deque

from robin.kb import schema
from robin.kb.schema import KB
from robin.router import BM25, tokenize


def _graph() -> dict:
    path = KB / "graph.json"
    if not path.exists():
        from robin.kb.index import build
        build()
    return json.loads(path.read_text(encoding="utf-8"))


def _line(node: dict, max_words: int = 30) -> str:
    summary = " ".join(str(node.get("summary", "")).split()[:max_words])
    return f"{node['id']} [{node['type']}, {node['status']}, {node['updated']}]: {summary}"


def query(near: str | None = None, hops: int = 1, market: str | None = None, type_: str | None = None,
          text: str | None = None, limit: int = 10, include_stale: bool = False) -> list[str]:
    g = _graph()
    nodes = {n["id"]: n for n in g["nodes"]}
    candidates = set(nodes)

    if near:
        adj: dict[str, set[str]] = {}
        for e in g["edges"]:
            adj.setdefault(e["from"], set()).add(e["to"])
            adj.setdefault(e["to"], set()).add(e["from"])
        seen, frontier = {near}, deque([(near, 0)])
        while frontier:
            cur, d = frontier.popleft()
            if d == hops:
                continue
            for nxt in adj.get(cur, ()):
                if nxt not in seen:
                    seen.add(nxt)
                    frontier.append((nxt, d + 1))
        candidates &= seen
    if market:
        candidates = {c for c in candidates if market in (nodes[c].get("markets") or []) or c == f"market-{market}"}
    if type_:
        candidates = {c for c in candidates if nodes[c]["type"] == type_}
    if not include_stale:
        candidates = {c for c in candidates if nodes[c]["status"] in ("active", "conflict")}
    candidates = {c for c in candidates if nodes[c]["type"] != "source"} or candidates

    ordered = sorted(candidates, key=lambda c: str(nodes[c]["updated"]), reverse=True)
    if text:
        names = sorted(candidates)
        bm = BM25([tokenize(f"{c} {nodes[c]['summary']}") for c in names])
        scores = dict(zip(names, bm.score(tokenize(text))))
        top = max(scores.values(), default=0)
        # Keep only clear matches: shared boilerplate words should not pull in every node.
        ordered = sorted((c for c in names if scores[c] > 0 and scores[c] >= 0.5 * top), key=lambda c: -scores[c])
    return [_line(nodes[c]) for c in ordered[:limit]]


def stale(today: dt.date | None = None) -> list[str]:
    today = today or dt.date.today()
    out = []
    for nid, n in sorted(schema.load_all().items()):
        status = n.meta.get("status")
        if status in ("stale", "conflict") or (status == "active" and n.expired(today)):
            out.append(f"{nid}: {status}, expires {n.meta.get('expires')}")
    return out
