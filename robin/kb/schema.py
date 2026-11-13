"""Node schema, edge vocabulary and parsing for knowledge files."""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from robin import frontmatter

ROOT = Path(__file__).resolve().parent.parent.parent
KB = ROOT / "knowledge"
SOURCES = KB / "_sources"

# Node types -> domain folder. Closed set; add via PR (David).
TYPES: dict[str, str] = yaml.safe_load((KB / "_types.yaml").read_text())["types"] if (KB / "_types.yaml").exists() else {}

# Edge vocabulary (spec §15.4, amended in DECISIONS.md D-006). Closed set; add via PR only.
EDGES = {
    "operates_in",   # company/product/competitor -> market
    "regulated_by",  # market/product -> regulator
    "uses",          # anything -> payment-method / channel / vendor
    "competes_with", # competitor/product <-> competitor/product
    "impacts",       # anything -> metric, with (+) or (-); add 'causal' when it causes it
    "evidence_for",  # source -> node
    "tests",         # experiment -> hypothesis/product/metric
    "serves",        # product/task -> segment or goal id
    "targets",       # campaign/product -> segment/market
    "part_of",       # node -> larger node (product -> company, segment -> market)
    "supersedes",    # node -> older node it replaces
}

STATUSES = {"active", "stale", "archived", "conflict"}
GRADES = {"A", "B", "C"}
OWNERS_DEFAULT = {"robin", "david"}
BODY_HEADERS = ["## Facts", "## Relations", "## Open questions", "## Changelog"]
REQUIRED = ["id", "type", "status", "updated", "confidence", "expires", "summary"]

CAPS_WORDS = {"INDEX.md": 300, "_index.md": 500, "entity": 1500}

ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\[\[([a-z0-9][a-z0-9\-]*)\]\]")
FACT_RE = re.compile(
    r"^- \[(?P<date>\d{4}-\d{2}-\d{2})\] (?P<text>.+?) — (?P<src>\[\[src-[a-z0-9\-]+\]\](?:, \[\[src-[a-z0-9\-]+\]\])*)"
    r" — (?P<grade>[ABC])(?P<flags>(?: \((?:inferred|superseded[^)]*|conflict[^)]*)\))*)$"
)
REL_RE = re.compile(r"^- (?P<edge>[a-z_]+) \[\[(?P<target>[a-z0-9\-]+)\]\](?: \((?P<note>[^)]*)\))?$")


@dataclass
class Fact:
    date: str
    text: str
    sources: list[str]
    grade: str
    inferred: bool
    superseded: bool
    line: int


@dataclass
class Edge:
    edge: str
    target: str
    note: str
    line: int


@dataclass
class Node:
    path: Path
    meta: dict
    body: str
    sections: dict[str, list[tuple[int, str]]] = field(default_factory=dict)
    facts: list[Fact] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)
    parse_errors: list[str] = field(default_factory=list)

    @property
    def id(self) -> str:
        return str(self.meta.get("id", ""))

    @property
    def type(self) -> str:
        return str(self.meta.get("type", ""))

    @property
    def words(self) -> int:
        return len(self.body.split())

    def expired(self, today: dt.date | None = None) -> bool:
        exp = self.meta.get("expires")
        if not exp:
            return False
        exp = exp if isinstance(exp, dt.date) else dt.date.fromisoformat(str(exp))
        return exp < (today or dt.date.today())


def is_entity_file(path: Path) -> bool:
    if path.suffix != ".md":
        return False
    rel = path.relative_to(KB)
    if len(rel.parts) < 2:
        return False  # top-level files (INDEX, _gaps, _changelog, _schema)
    return not path.name.startswith("_") or rel.parts[0] == "_sources" and path.name.startswith("src-")


def parse(path: Path) -> Node:
    meta, body = frontmatter.read(path)
    node = Node(path=path, meta=meta, body=body)
    current = None
    for i, raw in enumerate(body.splitlines(), start=1):
        line = raw.rstrip()
        if line.startswith("## "):
            current = line
            node.sections.setdefault(current, [])
            continue
        if current and line.strip():
            node.sections[current].append((i, line))

    for i, line in node.sections.get("## Facts", []):
        if not line.startswith("- "):
            continue
        m = FACT_RE.match(line)
        if not m:
            node.parse_errors.append(f"line {i}: fact must be '- [YYYY-MM-DD] fact — [[src-id]] — A|B|C'")
            continue
        flags = m.group("flags") or ""
        node.facts.append(Fact(
            date=m.group("date"), text=m.group("text"), sources=LINK_RE.findall(m.group("src")),
            grade=m.group("grade"), inferred="(inferred)" in flags, superseded="(superseded" in flags, line=i,
        ))

    for i, line in node.sections.get("## Relations", []):
        if not line.startswith("- "):
            continue
        m = REL_RE.match(line)
        if not m:
            node.parse_errors.append(f"line {i}: relation must be '- <edge> [[target-id]] (optional note)'")
            continue
        node.edges.append(Edge(m.group("edge"), m.group("target"), m.group("note") or "", i))
    return node


def load_all() -> dict[str, Node]:
    nodes: dict[str, Node] = {}
    for path in sorted(KB.rglob("*.md")):
        if is_entity_file(path):
            node = parse(path)
            nodes[node.id or path.stem] = node
    return nodes


def domain_dirs() -> list[Path]:
    return sorted({KB / d for d in TYPES.values()})
