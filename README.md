# Robin — an AI agent org for any team

Robin is a company of AI agents built on the Claude Agent SDK. One **chief of staff** takes any request from any
team (CEO, product, marketing, market research, data, sales, support, ops, engineering, finance, people, legal),
finds the right **department agent** and **skill**, and gets the result checked by an independent **reviewer**.
Everything is plain files in git: agents, skills, knowledge, goals, evals.

```
ask ─► chief-of-staff ─► department agent(s) ─► skill ─► reviewer ─► answer (≤120 words, sourced)
          ▲ BM25 shortlist (offline)          │ kb tools
          └ task-plan for cross-team work     ▼
                                    knowledge/ (dated, sourced, expiring facts)
```

## What's in the box

| Path | What |
|---|---|
| `.claude/agents/` | 14 agents: 12 departments + `chief-of-staff` + `reviewer` |
| `.claude/skills/` | 38 skills (agentskills.io format), each with Steps / Output / Quality checks |
| `org/` | how the org works (`INDEX.md`), generated catalogue (`REGISTRY.md`), business units |
| `knowledge/` | markdown-as-graph knowledge base (spec §15): `INDEX.md` → `_index.md` → entities → `_sources` |
| `harness/` | always-loaded context, goals, voice |
| `guard/` | approval gate (default deny), untrusted wrapper, secret scanner — David-owned |
| `robin/` | router, registry, orchestrator, knowledge tools, traces, CLI |
| `evals/` | routing eval (offline) + process evals (live) |
| `docs/` | spec v2, research on agent-team frameworks |

## Quick start

```bash
pip install -e '.[dev]'
robin route "Why did FTD drop 15% in Mexico this week?"   # which agent + skills
robin eval routing                                         # offline routing accuracy
robin eval routing --set holdout                           # never-tuned set
python -m pytest -q
robin kb query --market ph                                 # knowledge lookup
robin ask "What are the KYC rules for online deposits in the Philippines?"   # live; needs Anthropic credentials
robin trace <task-id>
```

Install the pre-commit hook: `ln -s ../../scripts/pre-commit .git/hooks/pre-commit`.

Interactive use: open the repo in Claude Code — the same agents and skills load from `.claude/`.

## Add to the org

- New skill: copy a `SKILL.md`, keep "Use when ..." in `description`, add ≥ 2 examples, list it in an agent.
- New agent/department: copy an agent file; "Use for ..." description, ≥ 3 examples, least-privilege tools.
- New business unit: copy `org/units/_template.md`.
- Then: `robin validate && robin registry && robin eval routing`.

## Status

See `HANDOVER.md`. Decisions: `DECISIONS.md`. Hard rules: `CLAUDE.md`.
