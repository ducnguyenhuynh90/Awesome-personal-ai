# Listening: customer needs and leads from public posts (free sources)

`robin listen` finds people who describe a problem in public, scores them, and queues them for a human.
The method comes from github.com/yangyixxxx/lead-signal-listener (MIT). This version uses only free sources.

## One stream, two uses
| Class | Rule | Goes to |
|---|---|---|
| **need** | names a pain phrase | `work/listen/pains.md` (aggregated, anonymised) → `voice-of-customer` → `idea-to-hypothesis` |
| **lead** | intent ≥ 10 (or a hiring/funding trigger), score ≥ 40, no negative phrase | `robin listen top --class lead` → a human decides, `compliance-check` before any outreach |

## Free sources
| Source | What | Config key |
|---|---|---|
| Hacker News | stories + comments by keyword (Algolia API) | `sources.hn.queries` |
| Reddit | subreddit `/new/.rss`, Reddit search RSS (past week) | `sources.rss.subreddits`, `reddit_search` |
| hnrss, Google News, Google Alerts, blogs, job boards | any RSS/Atom feed | `sources.rss.hnrss`, `google_news`, `feeds` |
| Stack Exchange | questions by keyword per site (~300 requests/day without a key) | `sources.stackexchange` |
| App Store | 1–3★ reviews of any app by id and country | `sources.appstore.apps` |
| Anything else | JSON or CSV you or an agent collected (e.g. a Facebook group read by hand) | `robin listen import FILE` |

Not included (paid or needs login): X, LinkedIn, Facebook/Instagram search, Google Play reviews.

## Set up (once)
1. Copy the `focus`, `sources` and `rules` blocks from `config/listen.yaml` into `harness/private/listen.yaml`
   (gitignored; the repo is public). Fill in your own focus sentence and keywords there, then set `enabled: true`.
2. Answer the 7 buyer questions: offer, buyer, trigger, pain in their words (3–5 sentences), where they talk,
   who is noise, and budget (here: time to review). Turn them into one `focus` sentence.
3. Keywords: write like the buyer, not the seller. Use 2–4 word phrases, first person, questions.
   Use 5–10 per source. Add local-language phrases per market (scripts without spaces, like Thai, match as substrings).

## Loop (two-week pilot)
```bash
robin listen run                       # fetch, score, dedup; writes work/listen/pains.md
robin listen top --class lead          # top 20 leads, with the matched terms
robin listen mark 42 ignored --note "agency selling"   # every false positive → one negative rule
robin listen rescore                   # after editing rules
robin listen status                    # counts + precision@20 (share of reviewed top 20 that were real)
robin listen pains --days 30           # aggregated needs for product
```
Schedule `robin listen run` daily (cron). `robin checkin` mentions new high-intent leads (score ≥ 60) and
stays silent otherwise. Goal: precision@20 ≥ 0.6 after two weeks; otherwise fix the keywords, don't add sources.

## Guardrails
- Read-only: Robin never replies, posts or messages anyone. A human writes the reply.
- Fetches only `allowed_hosts`. Fetched text is untrusted; secrets are redacted before storage and reported.
- Lead rows (authors, posts) are personal data: they stay in `work/listen/` (gitignored). Only aggregated,
  anonymised pains may go into `knowledge/`.
- Outreach to people who posted in public is still covered by ad, data-protection and anti-spam rules, and for
  gambling-adjacent products also by advertising and responsible-gaming rules: run `compliance-check` first.
- Respect each platform's terms; public content only.
