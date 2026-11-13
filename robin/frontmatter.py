"""Read and write markdown files with YAML frontmatter."""
from __future__ import annotations

from pathlib import Path

import yaml

FENCE = "---"


def split(text: str) -> tuple[dict, str]:
    """Return (frontmatter dict, body). Missing frontmatter -> ({}, text)."""
    if not text.startswith(FENCE + "\n"):
        return {}, text
    end = text.find("\n" + FENCE, len(FENCE))
    if end == -1:
        return {}, text
    meta = yaml.safe_load(text[len(FENCE) + 1 : end]) or {}
    body = text[end + len(FENCE) + 1 :].lstrip("\n")
    if not isinstance(meta, dict):
        raise ValueError("frontmatter is not a mapping")
    return meta, body


def read(path: Path) -> tuple[dict, str]:
    return split(path.read_text(encoding="utf-8"))


def dump(meta: dict, body: str) -> str:
    head = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=1000).strip()
    return f"{FENCE}\n{head}\n{FENCE}\n\n{body.lstrip()}"
