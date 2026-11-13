"""Readable, editable owner profile (Muse pattern). Personal: lives in gitignored harness/private/profile.md."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "harness" / "private" / "profile.md"
TEMPLATE = ROOT / "harness" / "profile.example.md"


def read(path: Path = PROFILE) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def remember(line: str, path: Path = PROFILE) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(TEMPLATE.read_text(encoding="utf-8").replace("(copy to harness/private/profile.md — gitignored; edit freely)", ""),
                        encoding="utf-8")
    entry = f"- {line.strip().rstrip('.')}. ({dt.date.today().isoformat()})\n"
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(entry)
    return entry.strip()


def forget(text: str, path: Path = PROFILE) -> list[str]:
    """Remove every preference line containing `text` (case-insensitive). Returns the removed lines."""
    if not path.exists():
        return []
    keep, removed = [], []
    for line in path.read_text(encoding="utf-8").splitlines(keepends=True):
        if line.startswith("- ") and text.lower() in line.lower():
            removed.append(line.strip())
        else:
            keep.append(line)
    path.write_text("".join(keep), encoding="utf-8")
    return removed
