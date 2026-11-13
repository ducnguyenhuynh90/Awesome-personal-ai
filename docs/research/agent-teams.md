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

## Meta Muse and xAI Grok Bot (2026-11-13)

Both are closed products; patterns were read from open analogues and public notes: nano-muse/nanoMuse (3.4k★),
unicodef1wn/grokbot-field-notes (705★), nickvasilescu/grokbot-clone (191★). Primary vendor pages were not reachable
from the build session; Sentinel details are from press coverage (UNVERIFIED).

| Pattern | From | Adopted as |
|---|---|---|
| One agent, one job; description states owns / tools / source of truth / approvals | Grok Bot | agent contract fields, validated |
| Prefer a new skill over a new agent | Grok Bot | rule in every agent's "Verify before done" |
| Correction → principle, never the story; overfit test | Grok Bot field notes | `robin learn` overfit check |
| Self-improvement capped (≤ 1 suggestion/week) | Grok Bot | weekly cap in `robin learn` |
| `stay_silent` outcome | grokbot-clone | `SILENT` reply, logged not delivered |
| Proof attached; 2 failed attempts = stop | Grok Bot | "Verify before done" section |
| Readable, editable memory + forget | nanoMuse / Muse | `robin profile/remember/forget` |
| Separate guard agent; read/send split; allow once/always | Muse Sentinel, grokbot-clone | proposal (guard/ is David's) |
| Autonomy ladder investigate → draft → autopilot | Grok Bot | `metadata.autonomy` per agent |

## Deep dive: Meta Muse, xAI Grok Bot, OpenAI dots (2026-11-13, second pass)

Vendor sites (about.fb.com, ai.meta.com, x.ai, docs.x.ai, openai.com, help.openai.com) were blocked from the build
session; findings come from GitHub (nanoMuse, awesome-muse, grokbot-field-notes, grokbot-clone source,
awesome-dots, dots-second-brain, dots-vs-grok-bot paper) and search summaries of vendor posts.
"Verified" = vendor post via search summary or 2+ independent sources.

| Finding | Product | Status | Robin |
|---|---|---|---|
| Sentinel: separate agent approves all egress; surrogate credentials swapped at the boundary | Muse | verified | gate proposal |
| Taint: a process that read untrusted data loses auto-allow | Muse | verified | gate proposal (item 1) |
| Grants once / session / task / time-limited, exact match | Muse | unverified | gate proposal (item 3) |
| Background goals, "Ideas" from goals + history, agent decides if a result is worth a notification | Muse | unverified | routines + SILENT |
| Per-action rules: auto / when told / ask / hand off; money and passwords always human | dots | verified | gate proposal (item 2) |
| Proactive research is read-only | dots | verified | **built**: proactive mode |
| Typed schedules: what, when + tz + end date, notify-if, deliver-to | dots | verified | **built**: config/routines.yaml |
| No per-memory delete; learning survives disconnecting an app | dots | verified (weakness) | **built**: provenance + forget --source |
| Routines: one owner, event > schedule, run history, report failure instead of stale data, run limits | Grok Bot | verified | **built**: contract + run log |
| Long history in routines = biggest cost | Grok Bot | verified | proactive prompt is fresh per run |
| Check-in: digest in code, then one message or stay_silent; skip if user active | Grok clone | unverified | **built**: robin checkin (zero tokens when silent) |
| Handoffs with exact ids; debates ≤ 3 agents told to disagree | Grok field notes | unverified | **built**: handoff contract |
| Skills shared across bots, memory per bot | Grok Bot | verified | already: skills shared, knowledge base shared |

Not copied: Muse's hourly per-person profile pages (privacy; conflicts with HR rules).
