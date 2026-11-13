# Research: AI agent teams for a whole company (2026-11-13)

Method: GitHub search API for existence, stars and last push; READMEs read from raw.githubusercontent.com
(read-only, nothing cloned or executed). Star counts as of 2026-11-13. Patterns borrowed, no code copied.

| Repo | Stars | Last push | Pattern worth borrowing | Used here as |
|---|---|---|---|---|
| FoundationAgents/MetaGPT | 71k | 2026-01 | `Code = SOP(Team)`: roles follow written SOPs | agent body = role, deliverables, metrics, escalation |
| OpenBMB/ChatDev (2.0) | 35k | 2026-11 | workflows as schema-validated YAML | `robin validate` on agent/skill frontmatter |
| crewAIInc/crewAI | 61k | 2026-11 | role/goal per agent; hierarchical manager that delegates + validates | chief-of-staff + reviewer |
| microsoft/autogen | 62k | 2026-11 | — (maintenance mode; MS points to Agent Framework) | reason to avoid framework lock-in |
| langchain-ai/langgraph-supervisor-py | 1.7k, archived | 2026-07 | hierarchical supervisors (top → department) | two-level routing |
| openai/swarm, openai-agents-python | 22k / 31k | 2026 | triage agent → specialist; handoff vs agent-as-tool | agent-as-tool (Agent tool), chief-of-staff merges |
| wshobson/agents | 43k | 2026-11 | single-source markdown, domain bundles, CI + plugin evals | `robin eval routing` in tests |
| VoltAgent/awesome-claude-code-subagents | 27k | 2026-11 | per-agent least-privilege `tools:` + `model:` tier | agent frontmatter |
| contains-studio/agents | 12k | 2025-07 (stale) | department folders; "when to use" + examples in description | `description` + `metadata.examples` |
| msitarzewski/agency-agents | 168k | 2026-11 | deliverables, success metrics per agent | agent body sections |
| anthropics/skills, agentskills.io | 194k / 27k | 2026-11 | SKILL.md = name + "what + when" description; progressive disclosure | all 38 skills |
| kyegomez/swarms | 7k | 2026-11 | director plans → distributes → reviews loop | task-plan skill |
| camel-ai/camel | 18k | 2026-11 | human-in-the-loop approval of tool use | approval gate |
| letta-ai/letta | 25k | 2026-10 | persistent agent memory | knowledge base (git-backed) |
| NousResearch/hermes-agent | 263k | 2026-11 | write a skill from experience after complex tasks | skill-author (PR, David approves) |
| kayba-ai/agentic-context-engine (ACE) | 2.6k | 2026-09 | reflector + skill manager curate a skillbook from traces | P3 craft loop (planned) |
| paperclipai/paperclip | 114k | 2026-11 | "AI company": org chart, budgets, approval gates, heartbeats | limits.yaml, approvals/ |
| userFRM/agent-dispatch | 4 | 2026-02 | compact generated keyword→agent index (~2k tokens) | `org/REGISTRY.md` + BM25 router |
| simonlin1212/Agent-Staff | 54 | 2026-10 | one agent per department + chief of staff | org shape |

UNVERIFIED: the ACE paper authors' official repo; Letta details beyond its short README.

## Patterns adopted
1. Descriptions are written for routing: what, when ("Use for/when"), ≥ 2–3 example requests. Enforced by `robin validate`.
2. Keep the catalogue out of context: generated `org/REGISTRY.md` + offline BM25 shortlist (top 3 agents, top 5 skills).
3. Two-level routing: chief of staff → department agent → skill.
4. Agent-as-tool (not handoff): the chief of staff must merge and send results to the reviewer.
5. SOPs as files: agents = roles; skills = procedures with Steps / Output / Quality checks / Pitfalls.
6. Least privilege + cost tier in frontmatter; external writes behind an approval gate.
7. Learning via review: skill changes are PRs David approves; nothing self-merges.
8. Routing evals in CI, with a held-out set that is never tuned on.

## Anti-patterns avoided
1. Persona bloat: one owner per capability; overlapping descriptions get merged.
2. Loading every agent's full prompt at startup (agent-dispatch cites ~211k tokens for 130 agents).
3. Framework lock-in: files are the source of truth; the orchestration layer is ~150 lines.
