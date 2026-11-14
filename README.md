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
| `docs/` | research on agent-team frameworks, proposals (spec and company config are local: `harness/private/`) |

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

## Test it first (no company data, no tool keys)

```bash
pip install -e '.[dev]'
robin doctor                                   # what works now, what is missing (never prints keys)
robin ask --dry-run "Why did FTD drop in Mexico?"   # routing + prompt, no model call, no cost
robin eval routing && python -m pytest -q      # offline checks
cp .env.example .env                           # then set only ANTHROPIC_API_KEY (or run `claude` to log in)
robin ask "Write 5 push variants to win back lapsed depositors"   # first live answer
```

Without tools or company context, agents still work: they answer from the web and the knowledge base, and say
"no access" instead of guessing when a task needs data they cannot reach.

## Add keys or tools later

1. Put the keys in `.env` (gitignored). Variable names are in `.env.example`.
2. `robin tools enable posthog` (or notion, gmail, calendar, bigquery, github). A tool loads only when it is
   enabled **and** its keys are set; otherwise it is skipped.
3. `robin doctor` to confirm it shows `ready`.
4. New tool: copy a block in `config/integrations.yaml` (http `url` or stdio `command`), write keys as `${VAR}`.
5. Company context: drop `.md` files in `harness/private/` (gitignored), then `robin tools enable company_context`.

Write tools stay blocked by the approval gate even when a tool is enabled. To let an agent do one write:
`robin approve <task-id> <tool> [--scope once|task|until:YYYY-MM-DD] [--match channel=C123]`. Money, credentials,
permissions, deploys, deletes and publishing can never be approved for an agent. Standing rules live in
`config/action_rules.yaml` (auto | when_told | ask | handoff); `send: false` makes a connector read-only.

## Run on Claude Code cloud (claude.ai/code)

- Open the repo in a cloud session: `.claude/hooks/session-start.sh` installs Robin, and the agents and skills in
  `.claude/` load automatically. Ask the chief of staff or a department agent directly; no API key needed.
- Safety in cloud sessions: `guard/claude_code_hook.py` (registered in `.claude/settings.json`) sends every company
  connector write (Slack, Gmail, Notion, Drive, ...) through the approval gate, with the session id as task id.
  Reads and repo work are untouched. Approve one write: `robin approve <session-id> <tool>`.
- Daily routine: a cloud scheduled task "Robin daily knowledge scan" runs at 06:06 (Asia/Ho_Chi_Minh) in a fresh
  session: knowledge-scan as research-lead, web only, knowledge commits to branch `robin/knowledge-updates`,
  then `robin checkin`; it messages only when something crosses a threshold. Manage it in claude.ai under
  scheduled tasks.

## Add to the org

- New skill: copy a `SKILL.md`, keep "Use when ..." in `description`, add ≥ 2 examples, list it in an agent.
- New agent/department: copy an agent file; "Use for ..." description, ≥ 3 examples, least-privilege tools.
- New business unit: copy `org/units/_template.md`.
- Then: `robin validate && robin registry && robin eval routing`.

## Status

See `HANDOVER.md`. Decisions: `DECISIONS.md`. Hard rules: `CLAUDE.md`.
