"""Optional tools and keys (config/integrations.yaml). Everything is off until enabled.

Keys are read from the environment or a local `.env` (gitignored) — never from tracked files.
A tool loads only when it is enabled AND every ${VAR} it references is set.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "integrations.yaml"
ENV_FILE = ROOT / ".env"
VAR = re.compile(r"\$\{([A-Z0-9_]+)\}")


def load_env_file(path: Path = ENV_FILE) -> list[str]:
    """Load KEY=VALUE lines from .env into os.environ (existing env wins). Returns the names loaded."""
    loaded = []
    if not path.exists():
        return loaded
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and value and key not in os.environ:
            os.environ[key] = value
            loaded.append(key)
    return loaded


def config(path: Path = CONFIG) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _vars(obj) -> set[str]:
    if isinstance(obj, str):
        return set(VAR.findall(obj))
    if isinstance(obj, dict):
        return set().union(*(_vars(v) for v in obj.values())) if obj else set()
    if isinstance(obj, list):
        return set().union(*(_vars(v) for v in obj)) if obj else set()
    return set()


def _fill(obj):
    if isinstance(obj, str):
        return VAR.sub(lambda m: os.environ.get(m.group(1), ""), obj)
    if isinstance(obj, dict):
        return {k: _fill(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_fill(v) for v in obj]
    return obj


@dataclass
class Status:
    name: str
    kind: str
    enabled: bool
    missing: list[str]
    note: str = ""

    @property
    def ready(self) -> bool:
        return self.enabled and not self.missing

    def line(self) -> str:
        if not self.enabled:
            state = "off"
        elif self.missing:
            state = "ON but missing " + ", ".join(self.missing)
        else:
            state = "ready"
        return f"{self.kind:10} {self.name:16} {state}" + (f"  — {self.note}" if self.note else "")


def model_status(cfg: dict | None = None) -> Status:
    cfg = cfg or config()
    names = (cfg.get("model") or {}).get("any_of_env", [])
    have = any(os.environ.get(n) for n in names)
    claude_login = (Path.home() / ".claude" / ".credentials.json").exists()
    return Status("anthropic", "model", True, [] if (have or claude_login) else [" or ".join(names) + " (or `claude` login)"])


def statuses(cfg: dict | None = None) -> list[Status]:
    cfg = cfg or config()
    out = [model_status(cfg)]
    for name, item in (cfg.get("mcp") or {}).items():
        missing = sorted(v for v in _vars(item.get("server", {})) if not os.environ.get(v))
        out.append(Status(name, "mcp", bool(item.get("enabled")), missing))
    for name, item in (cfg.get("interfaces") or {}).items():
        missing = sorted(v for v in item.get("env", []) if not os.environ.get(v))
        out.append(Status(name, "interface", bool(item.get("enabled")), missing, item.get("note", "")))
    cc = cfg.get("company_context") or {}
    files = list((ROOT / cc.get("path", "harness/private/")).glob("*.md")) if cc else []
    out.append(Status("company_context", "context", bool(cc.get("enabled")),
                      [] if files else [f"no .md files in {cc.get('path', 'harness/private/')}"]))
    return out


def mcp_servers(cfg: dict | None = None) -> dict:
    """Enabled MCP servers whose variables are all set, with ${VAR} filled in. Others are skipped."""
    cfg = cfg or config()
    servers = {}
    for name, item in (cfg.get("mcp") or {}).items():
        if not item.get("enabled"):
            continue
        server = item.get("server") or {}
        if any(not os.environ.get(v) for v in _vars(server)):
            continue
        servers[name] = _fill(server)
    return servers


def company_context_enabled(cfg: dict | None = None) -> bool:
    cfg = cfg or config()
    return bool((cfg.get("company_context") or {}).get("enabled"))


def set_enabled(name: str, value: bool, path: Path = CONFIG) -> str:
    """Flip `enabled` for one tool in place (keeps comments: edits only that line)."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    inside = False
    for i, line in enumerate(lines):
        if re.match(rf"^\s{{0,2}}{re.escape(name)}:\s*$", line):
            inside = True
            continue
        if inside and re.match(r"^\s*enabled:\s*(true|false)", line):
            lines[i] = re.sub(r"(true|false)", "true" if value else "false", line, count=1)
            path.write_text("".join(lines), encoding="utf-8")
            return f"{name}: enabled = {value}"
        if inside and re.match(r"^\S", line):
            break
    raise KeyError(f"no tool named '{name}' with an `enabled:` line in {path.name}")
