"""Readable, editable owner profile (Muse pattern). Personal: lives in gitignored harness/private/profile.md."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "harness" / "private" / "profile.md"
TEMPLATE = ROOT / "harness" / "profile.example.md"


def read(path: Path = PROFILE) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def remember(line: str, source: str = "david", status: str = "", path: Path = PROFILE) -> str:
    """Add one preference with provenance (OpenAI dots lesson: every memory knows where it came from)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(TEMPLATE.read_text(encoding="utf-8").replace("(copy to harness/private/profile.md — gitignored; edit freely)", ""),
                        encoding="utf-8")
    tags = f"source: {source} · {dt.date.today().isoformat()}" + (f" · status: {status}" if status else "")
    entry = f"- {line.strip().rstrip('.')}. [{tags}]\n"
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(entry)
    return entry.strip()


def forget(text: str = "", source: str = "", path: Path = PROFILE) -> list[str]:
    """Remove preference lines containing `text`, and/or every line learned from `source`. Returns removed lines."""
    if not path.exists() or not (text or source):
        return []
    keep, removed = [], []
    for line in path.read_text(encoding="utf-8").splitlines(keepends=True):
        hit_text = bool(text) and text.lower() in line.lower()
        hit_src = bool(source) and f"source: {source.lower()} ·" in line.lower()
        if line.startswith("- ") and (hit_text or hit_src):
            removed.append(line.strip())
        else:
            keep.append(line)
    path.write_text("".join(keep), encoding="utf-8")
    return removed
