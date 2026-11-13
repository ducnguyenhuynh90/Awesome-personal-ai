# Org — how the agent company works

Robin is a company of agents. One front door, a department agent per function, a shared skill library,
one knowledge base, one independent reviewer.

```
David / any team ──► chief-of-staff ──► department agent(s) ──► skills ──► reviewer ──► answer
                         │  router shortlist (BM25, offline)          ▲
                         └── task-plan for cross-team work ───────────┘
                   knowledge/ (shared facts)   harness/ (goals, context, voice)   outbox/ (drafts)
```

## Departments

Read `org/REGISTRY.md` (generated) for the full who-does-what table. Summary:

| Department | Agent | Typical asks |
|---|---|---|
| Executive / CEO | exec-strategy | decisions, OKRs, board/investor updates |
| Product | product-lead | hypotheses, PRDs, prioritisation |
| Marketing | marketing-lead | campaigns, content, copy |
| Market research | research-lead | markets, competitors, customer voice |
| Data | data-analyst | KPIs, why metrics moved, test readouts |
| Sales / BD | sales-bd-lead | prospects, partners, pitches |
| Support | support-lead | triage, themes, help articles |
| Operations | ops-lead | SOPs, vendors, meeting actions |
| Engineering | eng-lead | spec reviews, postmortems |
| Finance (restricted) | finance-analyst | budget variance, unit economics |
| People (restricted) | people-partner | JDs, interview loops, onboarding |
| Legal / compliance (restricted) | compliance-officer | regulation, KYC/AML, ad rules, contract summaries |

Staff roles: `chief-of-staff` (routes, plans, merges) and `reviewer` (independent check; David owns it).

## How a request finds the right agent and skill

1. `robin route "<ask>"` scores every department agent and skill by BM25 over their descriptions,
   handles, tags and examples. No API call. Top 3 agents + top 5 skills go into the prompt.
2. The chief of staff delegates to the top agent (Agent tool). Low confidence → it asks one question.
3. The department agent picks the skill from its own short list (two-level routing).
4. Cross-team asks: chief of staff runs `task-plan`, delegates sub-tasks in parallel, merges.
5. Every routing miss is fixable in files: improve the agent/skill `description` and `examples`,
   then `robin eval routing` must stay ≥ 85%.

## Add a department, agent or skill

- Agent: copy any file in `.claude/agents/`; keep `description` starting "Use for ...", ≥ 3 examples,
  least-privilege `tools`, `model` tier, `metadata.department`.
- Skill: copy any `.claude/skills/*/SKILL.md`; `description` must contain "Use when ...", ≥ 2 examples,
  body has `## Steps`, `## Output`, `## Quality checks`. List it in an agent's `skills`.
- Business unit: copy `org/units/_template.md`.
- Then: `robin validate && robin registry && robin eval routing`.

One owner per capability: if two agents' descriptions overlap, routing gets worse. Merge instead of adding.
