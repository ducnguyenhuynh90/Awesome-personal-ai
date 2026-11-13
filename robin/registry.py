"""Registry of role agents and skills.

Source of truth is the files Claude Code already understands:
  .claude/agents/<name>.md           one role agent (department lead or staff role)
  .claude/skills/<name>/SKILL.md     one skill (agentskills.io format)

Robin-specific fields live under `metadata:` so Claude Code and the Agent SDK
ignore them, while the router and validator use them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from robin import frontmatter

ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT / ".claude" / "agents"
SKILLS_DIR = ROOT / ".claude" / "skills"

TIERS = {"executor", "reviewer", "cheap", "deep"}
SENSITIVITY = {"normal", "restricted"}
AGENT_KINDS = {"department", "staff"}


@dataclass
class Skill:
    name: str
    description: str
    department: str
    tags: list[str]
    examples: list[str]
    writes_to: list[str]
    context: list[str]
    domains: list[str]
    path: Path
    body: str

    def search_text(self) -> str:
        return " ".join([self.name.replace("-", " "), self.description, " ".join(self.tags), " ".join(self.examples)])


@dataclass
class Agent:
    name: str
    description: str
    department: str
    kind: str
    tier: str
    model: str | None
    tools: list[str]
    skills: list[str]
    handles: list[str]
    not_for: list[str]
    examples: list[str]
    sensitivity: str
    kb_domains: list[str]
    path: Path
    body: str
    extra: dict = field(default_factory=dict)

    def search_text(self) -> str:
        return " ".join(
            [self.department.replace("-", " "), self.description, " ".join(self.handles), " ".join(self.examples)]
        )


def _list(meta: dict, key: str) -> list[str]:
    value = meta.get(key) or []
    if isinstance(value, str):
        value = [v.strip() for v in value.split(",") if v.strip()]
    return list(value)


def load_skills(skills_dir: Path = SKILLS_DIR) -> dict[str, Skill]:
    skills: dict[str, Skill] = {}
    for path in sorted(skills_dir.glob("*/SKILL.md")):
        meta, body = frontmatter.read(path)
        md = meta.get("metadata") or {}
        skill = Skill(
            name=meta.get("name", ""),
            description=meta.get("description", ""),
            department=md.get("department", ""),
            tags=_list(md, "tags"),
            examples=_list(md, "examples"),
            writes_to=_list(md, "writes_to"),
            context=_list(md, "context"),
            domains=_list(md, "domains"),
            path=path,
            body=body,
        )
        skills[skill.name or path.parent.name] = skill
    return skills


def load_agents(agents_dir: Path = AGENTS_DIR) -> dict[str, Agent]:
    agents: dict[str, Agent] = {}
    for path in sorted(agents_dir.glob("*.md")):
        meta, body = frontmatter.read(path)
        md = meta.get("metadata") or {}
        agent = Agent(
            name=meta.get("name", ""),
            description=meta.get("description", ""),
            department=md.get("department", ""),
            kind=md.get("kind", "department"),
            tier=md.get("tier", "executor"),
            model=meta.get("model"),
            tools=_list(meta, "tools"),
            skills=_list(meta, "skills"),
            handles=_list(md, "handles"),
            not_for=_list(md, "not_for"),
            examples=_list(md, "examples"),
            sensitivity=md.get("sensitivity", "normal"),
            kb_domains=_list(md, "kb_domains"),
            path=path,
            body=body,
            extra=md,
        )
        agents[agent.name or path.stem] = agent
    return agents


# Tools an agent may list without David's sign-off. Write/Edit are safe here because the
# approval gate confines them to work/ and outbox/. Anything else needs metadata.write_tools_approved.
SAFE_TOOLS = {"Read", "Grep", "Glob", "WebSearch", "WebFetch", "Write", "Edit", "Skill", "TodoWrite", "Agent"}
# In-process tools that write only through Robin's own guarded writer.
INTERNAL_PREFIXES = ("mcp__kb__",)
MCP_READ_VERBS = ("get", "list", "search", "read", "fetch", "query", "find", "describe", "view", "retrieve")


def _unsafe(tools: list[str]) -> set[str]:
    out = set()
    for t in tools:
        if t in SAFE_TOOLS or t.startswith(INTERNAL_PREFIXES):
            continue
        if t.startswith("mcp__") and t.split("__")[-1].lower().startswith(MCP_READ_VERBS):
            continue
        out.add(t)
    return out


def validate(agents: dict[str, Agent] | None = None, skills: dict[str, Skill] | None = None) -> list[str]:
    """Return a list of problems. Empty list = registry is valid."""
    agents = load_agents() if agents is None else agents
    skills = load_skills() if skills is None else skills
    errors: list[str] = []

    for key, s in skills.items():
        where = f"skill {key}"
        if s.name != s.path.parent.name:
            errors.append(f"{where}: name '{s.name}' must equal folder '{s.path.parent.name}'")
        if not (40 <= len(s.description) <= 1024):
            errors.append(f"{where}: description must be 40-1024 chars (is {len(s.description)})")
        if "use when" not in s.description.lower():
            errors.append(f"{where}: description must say 'Use when ...' so the router and Claude can pick it")
        if not s.department:
            errors.append(f"{where}: metadata.department missing")
        if len(s.examples) < 2:
            errors.append(f"{where}: needs >= 2 metadata.examples (routing eval depends on them)")
        for header in ("## Steps", "## Output", "## Quality checks"):
            if header not in s.body:
                errors.append(f"{where}: body missing '{header}'")

    departments = {a.department for a in agents.values() if a.kind == "department"}
    for key, a in agents.items():
        where = f"agent {key}"
        if a.name != a.path.stem:
            errors.append(f"{where}: name '{a.name}' must equal file name '{a.path.stem}'")
        if "use when" not in a.description.lower() and "use for" not in a.description.lower():
            errors.append(f"{where}: description must say 'Use for/when ...'")
        if a.kind not in AGENT_KINDS:
            errors.append(f"{where}: metadata.kind must be one of {sorted(AGENT_KINDS)}")
        if a.tier not in TIERS:
            errors.append(f"{where}: metadata.tier must be one of {sorted(TIERS)}")
        if a.sensitivity not in SENSITIVITY:
            errors.append(f"{where}: metadata.sensitivity must be one of {sorted(SENSITIVITY)}")
        for sk in a.skills:
            if sk not in skills:
                errors.append(f"{where}: unknown skill '{sk}'")
        bad = _unsafe(a.tools) - set(a.extra.get("write_tools_approved", []))
        if bad:
            errors.append(f"{where}: write tools {sorted(bad)} need metadata.write_tools_approved (David only)")
        if a.kind == "department" and len(a.examples) < 3:
            errors.append(f"{where}: department agents need >= 3 metadata.examples")

    for key, s in skills.items():
        if s.department not in departments | {"shared", "staff"}:
            errors.append(f"skill {key}: department '{s.department}' has no department agent")
        owners = [a.name for a in agents.values() if key in a.skills]
        if not owners:
            errors.append(f"skill {key}: no agent lists it in skills")
    return errors
