"""kb lint — check-only. Never edits files (DECISIONS.md D-008)."""
from __future__ import annotations

import datetime as dt

from robin.kb import schema
from robin.kb.schema import KB, Node

from guard import secret_scanner


def _words(path) -> int:
    from robin import frontmatter
    _, body = frontmatter.read(path)
    return len(body.split())


def lint(today: dt.date | None = None) -> list[str]:
    today = today or dt.date.today()
    errors: list[str] = []
    if not schema.TYPES:
        return ["knowledge/_types.yaml missing or empty"]
    nodes = schema.load_all()
    ids = set(nodes)

    # Layer caps for INDEX and domain indexes.
    index = KB / "INDEX.md"
    if not index.exists():
        errors.append("knowledge/INDEX.md missing")
    elif _words(index) > schema.CAPS_WORDS["INDEX.md"]:
        errors.append(f"INDEX.md: {_words(index)} words > cap {schema.CAPS_WORDS['INDEX.md']}")
    for d in schema.domain_dirs():
        idx = d / "_index.md"
        if d.name == "_sources":
            continue
        if d.exists() and any(p for p in d.glob("*.md") if not p.name.startswith("_")):
            if not idx.exists():
                errors.append(f"{idx.relative_to(KB.parent)} missing — run `robin kb index`")
            elif _words(idx) > schema.CAPS_WORDS["_index.md"]:
                errors.append(f"{idx.relative_to(KB.parent)}: over {schema.CAPS_WORDS['_index.md']} words — split the domain")

    for nid, n in nodes.items():
        errors.extend(f"{n.path.relative_to(KB.parent)}: {e}" for e in check_node(n, ids, today))
    return errors


def check_node(n: Node, ids: set[str], today: dt.date) -> list[str]:
    e: list[str] = []
    m = n.meta
    for key in schema.REQUIRED:
        if m.get(key) in (None, ""):
            e.append(f"frontmatter '{key}' missing")
    if n.id and not schema.ID_RE.match(n.id):
        e.append(f"id '{n.id}' must be a lowercase slug")
    if n.id and n.path.stem != n.id:
        e.append(f"file name must equal id ('{n.id}.md')")
    if n.type and n.type not in schema.TYPES:
        e.append(f"type '{n.type}' not in knowledge/_types.yaml")
    elif n.type:
        expected = schema.TYPES[n.type]
        top = n.path.relative_to(KB).parts[0]
        if top not in (expected, "_archive"):
            e.append(f"type '{n.type}' belongs in knowledge/{expected}/")
    if m.get("status") and m["status"] not in schema.STATUSES:
        e.append(f"status must be one of {sorted(schema.STATUSES)}")
    if m.get("confidence") and str(m["confidence"]) not in schema.GRADES:
        e.append("confidence must be A, B or C")
    if m.get("status") == "active" and n.expired(today):
        e.append("expired but status is active — run `robin kb index` to flip it to stale")
    summary = str(m.get("summary") or "")
    if len(summary.split()) > 30:
        e.append("summary over 30 words")
    for key in ("related", "sources", "markets"):
        if key in m and not isinstance(m[key], list):
            e.append(f"'{key}' must be a list")
    for ref in m.get("sources") or []:
        if ref not in ids:
            e.append(f"sources: [[{ref}]] does not exist")

    if n.type != "source":
        present = [h for h in schema.BODY_HEADERS if h in n.sections]
        if present != schema.BODY_HEADERS:
            e.append(f"body headers must be exactly, in order: {', '.join(schema.BODY_HEADERS)}")
        if n.words > schema.CAPS_WORDS["entity"]:
            e.append(f"{n.words} words > cap {schema.CAPS_WORDS['entity']} — split the file and link the parts")
    e.extend(n.parse_errors)
    for f in n.facts:
        for s in f.sources:
            if s not in ids:
                e.append(f"line {f.line}: source [[{s}]] does not exist in knowledge/_sources/")
    for edge in n.edges:
        if edge.edge not in schema.EDGES:
            e.append(f"line {edge.line}: edge '{edge.edge}' not in closed vocabulary")
        if edge.target not in ids:
            e.append(f"line {edge.line}: link [[{edge.target}]] has no file")
        if edge.edge == "impacts" and not any(s in edge.note for s in ("+", "-", "−")):
            e.append(f"line {edge.line}: 'impacts' needs (+) or (-) in the note")
    if secret_scanner.scan(n.path.read_text(encoding="utf-8")):
        e.append("possible secret in file — redact before commit")
    return e
