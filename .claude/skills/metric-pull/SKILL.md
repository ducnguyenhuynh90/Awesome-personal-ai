---
name: metric-pull
description: 'Pulls a metric with a templated query; returns the number + query link. Aggregates only. Use when you need a number from analytics (PostHog/BigQuery/etc.): a KPI value, trend, funnel or cohort.'
metadata:
  department: data
  tags:
  - metric
  - kpi
  - number
  - dashboard
  - funnel
  - cohort
  - posthog
  - bigquery
  - query
  - data
  - how many
  examples:
  - What was D2 deposit retention for PH last week?
  - How many FTDs did we get yesterday by market?
  - Show the signup-to-deposit funnel for October
  context:
  - knowledge/metrics/
---

# metric-pull

Pulls a metric with a templated query; returns the number + query link. Aggregates only.

## Steps

1. Clarify metric definition, segment and date range; use the definition in knowledge/metrics/ if it exists.
2. Use a saved/templated query where possible; read-only connectors only.
3. Return aggregates only — never user-level rows or personal data.
4. Give the number, the comparison (vs previous period / target), and the query link.
5. If the number looks wrong (>3σ move), say so and check tracking before reporting.

## Output

Line 1: `<metric> = <value> (<change> vs <period>)`. Then definition, segment, date range, query link.

## Quality checks

- Line 1 answers the ask.
- Every number and claim has a source link or query link.
- Under the word cap; no preamble or restating.
- Query link included.
- Aggregates only.

## Pitfalls (learned)

- Comparing periods with different lengths or a tracking change in between.
