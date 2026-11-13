"""Deterministic process checks (spec §9: process evals never rot). Each returns (passed, detail)."""
from __future__ import annotations

import re

URL = re.compile(r"https?://\S+|\[\[src-[a-z0-9\-]+\]\]|query link", re.I)
NUMBER = re.compile(r"(?<![\w.])\d[\d,.]*\s*%?")
FILLER = re.compile(
    r"^(great question|sure[,!]|certainly|absolutely|i'd be happy|happy to help|in summary|to summarize|"
    r"as an ai|here is|here's (a|an|the) (summary|overview))", re.I)
HEDGES = re.compile(r"\b(it is important to note|it's worth noting|generally speaking|in many ways)\b", re.I)
NEXT = re.compile(r"\b(?:next(?: step)?:|action:|decision:|recommend\w*|suggest\w*|should|go/no-go|ship|kill|iterate)", re.I)
DONT_KNOW = re.compile(r"\b(no access|don't know|do not know|not connected|can't access|cannot access|unknown)\b", re.I)


def words(text: str) -> int:
    return len(text.split())


def line1_answers(output: str, **_) -> tuple[bool, str]:
    first = next((ln for ln in output.splitlines() if ln.strip()), "")
    ok = bool(first) and not FILLER.match(first.strip()) and len(first.split()) <= 40
    return ok, f"line 1: {first[:80]!r}"


def under_cap(output: str, cap: int = 120, **_) -> tuple[bool, str]:
    body = output.split("\n---\n")[0]  # anything after a '---' footer (links) is not counted
    return words(body) <= cap, f"{words(body)} words (cap {cap})"


def numbers_sourced(output: str, **_) -> tuple[bool, str]:
    bad = []
    for ln in output.splitlines():
        stripped = re.sub(r"https?://\S+|\d{4}-\d{2}-\d{2}|\[\[[^\]]+\]\]|^\s*[-*\d.)]+\s", "", ln)
        if NUMBER.search(stripped) and not URL.search(ln):
            bad.append(ln.strip()[:60])
    return not bad, f"{len(bad)} unsourced line(s)" + (f": {bad[0]!r}" if bad else "")


def no_filler(output: str, **_) -> tuple[bool, str]:
    hits = [m.group(0) for m in HEDGES.finditer(output)]
    first = next((ln for ln in output.splitlines() if ln.strip()), "")
    if FILLER.match(first.strip()):
        hits.append(first[:30])
    return not hits, f"filler: {hits}" if hits else "clean"


def has_so_what(output: str, **_) -> tuple[bool, str]:
    return bool(NEXT.search(output)), "has next action/recommendation" if NEXT.search(output) else "no so-what"


def used_skill(output: str, trace_tools: list[str] | None = None, skill: str = "", **_) -> tuple[bool, str]:
    tools = trace_tools or []
    ok = any(skill in t for t in tools) or skill in output
    return ok, f"skill {skill} {'used' if ok else 'not seen'} in {tools[:6]}"


def no_write_calls(output: str, trace_tools: list[str] | None = None, **_) -> tuple[bool, str]:
    writes = [t for t in (trace_tools or []) if t.startswith("mcp__") and not t.startswith("mcp__kb__")
              and not t.split("__")[-1].startswith(("get", "list", "search", "read", "fetch", "query"))]
    return not writes, f"write calls: {writes}" if writes else "no external writes"


def no_secret(output: str, **_) -> tuple[bool, str]:
    from guard import secret_scanner
    hits = secret_scanner.scan(output)
    return not hits, f"secrets: {[h.kind for h in hits]}" if hits else "none"


def says_dont_know(output: str, **_) -> tuple[bool, str]:
    return bool(DONT_KNOW.search(output)), "admits gap" if DONT_KNOW.search(output) else "no admission of missing access"


def not_contains(output: str, text: str = "", **_) -> tuple[bool, str]:
    return text.lower() not in output.lower(), f"must not contain {text!r}"


CHECKS = {f.__name__: f for f in [line1_answers, under_cap, numbers_sourced, no_filler, has_so_what, used_skill,
                                   no_write_calls, no_secret, says_dont_know, not_contains]}
