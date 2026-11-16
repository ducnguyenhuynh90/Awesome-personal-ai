"""Free social listening: find people describing a problem, score them, queue them for review.

Method adapted from github.com/yangyixxxx/lead-signal-listener (MIT): buyer-phrase keywords, transparent rule
scoring, dedup queue, human review of the top 20, every false positive becomes a negative rule.

Free sources only (no keys): Hacker News (Algolia API), any RSS/Atom feed (subreddit, Reddit search, hnrss,
Google Alerts, Google News, blogs, job boards), Stack Exchange API, Apple App Store reviews, and file import.

Safety:
- Read-only. Fetches only hosts in `allowed_hosts`. Never posts, replies or messages anyone.
- Fetched text is untrusted data: secrets are redacted before storage; agent-facing output is wrapped.
- Lead rows (authors, posts) are personal data: they live only in work/listen/ (gitignored).
  `pains` output is aggregated, with handles, emails and links stripped.
- Config: config/listen.yaml (generic example, public). Real keywords go in harness/private/listen.yaml
  (gitignored), which overrides it key by key.
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import re
import sqlite3
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from pathlib import Path

import yaml

from guard import secret_scanner, untrusted

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config" / "listen.yaml"
PRIVATE_CONFIG = ROOT / "harness" / "private" / "listen.yaml"
DATA = ROOT / "work" / "listen"
USER_AGENT = "robin-listen/0.1 (read-only research)"
STATUSES = ("new", "qualified", "contacted", "replied", "ignored")
GOOD = ("qualified", "contacted", "replied")


# ---------------------------------------------------------------- config

def _merge(dst: dict, src: dict) -> dict:
    for k, v in (src or {}).items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict) and k != "rules":
            _merge(dst[k], v)
        else:
            dst[k] = v
    return dst


def load_config(path: Path = CONFIG, private: Path = PRIVATE_CONFIG) -> dict:
    cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if private and private.exists():
        _merge(cfg, yaml.safe_load(private.read_text(encoding="utf-8")) or {})
    return cfg


def validate_config(cfg: dict) -> list[str]:
    errs = []
    for k in ("focus", "lookback_days", "allowed_hosts", "sources", "rules"):
        if k not in cfg:
            errs.append(f"'{k}' missing")
    rules = cfg.get("rules") or {}
    for k in ("pain", "intent", "persona", "negative"):
        if not isinstance(rules.get(k, {}), dict):
            errs.append(f"rules.{k} must be a mapping")
    for phrase, w in (rules.get("negative") or {}).items():
        if not isinstance(w, (int, float)) or w > 0:
            errs.append(f"rules.negative '{phrase}' must have a weight <= 0")
    for name in (cfg.get("sources") or {}):
        if name not in FETCHERS:
            errs.append(f"unknown source '{name}' (known: {', '.join(sorted(FETCHERS))})")
    return errs


# ---------------------------------------------------------------- scoring

def _pattern(phrase: str) -> re.Pattern:
    p = re.escape(phrase.lower())
    # ASCII phrases match on word edges; scripts without spaces (Thai, CJK...) match as substrings.
    return re.compile(rf"(?<![a-z0-9]){p}(?![a-z0-9])" if phrase.isascii() else p)


def _hits(text: str, table: dict) -> tuple[list[str], float]:
    found, total = [], 0.0
    for phrase, weight in (table or {}).items():
        if _pattern(phrase).search(text):
            found.append(phrase)
            total += weight
    return found, total


def score(sig: dict, rules: dict) -> dict:
    """0-100: base(hiring 30 / funding 35) + pain<=45 + intent<=30 + persona*3<=10 + engagement/10<=10
    + 5 if a question + negatives. Returns score, persona and the matched terms (explainable)."""
    text = f"{sig.get('title', '')} {sig.get('text', '')} {sig.get('community', '')}".lower()
    pain_f, pain = _hits(text, rules.get("pain"))
    intent_f, intent = _hits(text, rules.get("intent"))
    neg_f, neg = _hits(text, rules.get("negative"))
    persona, best = "other", 0
    for name, words in (rules.get("persona") or {}).items():
        n = sum(1 for w in words if _pattern(w).search(text))
        if n > best:
            persona, best = name, n
    base = {"hiring": 30, "funding": 35}.get(sig.get("kind"), 0)
    eng = min(10, int(sig.get("engagement") or 0) // 10)
    question = 5 if "?" in text else 0
    s = base + min(45, pain) + min(30, intent) + min(10, best * 3) + eng + question + neg
    return {"score": int(max(0, min(100, s))), "persona": persona, "pain": pain_f, "intent": intent_f,
            "negative": neg_f, "intent_weight": intent}


def classify(sig: dict, sc: dict, cfg: dict) -> str:
    """lead = someone asking for help (or a hiring/funding trigger) with no seller/noise phrase.
    need = describes a pain. other = neither."""
    lead_rules = cfg.get("lead") or {}
    if not sc["negative"] and sc["score"] >= lead_rules.get("min_score", 40) and (
            sc["intent_weight"] >= lead_rules.get("min_intent", 10) or sig.get("kind") in ("hiring", "funding")):
        return "lead"
    return "need" if sc["pain"] else "other"


# ---------------------------------------------------------------- fetching

def _get(url: str, cfg: dict, timeout: int = 20) -> bytes:
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    allowed = [h.lower() for h in cfg.get("allowed_hosts") or []]
    if not any(host == h or host.endswith("." + h) for h in allowed):
        raise PermissionError(f"host '{host}' not in allowed_hosts (config/listen.yaml)")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310 - host allowlisted above
        return r.read(2_000_000)


def _ts(value) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, (int, float)):
        return dt.datetime.fromtimestamp(value, dt.timezone.utc).isoformat(timespec="seconds")
    v = str(value).strip()
    for parse in (lambda x: dt.datetime.fromisoformat(x.replace("Z", "+00:00")), parsedate_to_datetime):
        try:
            d = parse(v)
            d = d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
            return d.astimezone(dt.timezone.utc).isoformat(timespec="seconds")
        except (ValueError, TypeError, IndexError):
            continue
    return ""


TAG = re.compile(r"<[^>]+>")


def _clean(s: str, n: int = 4000) -> str:
    import html as _h
    return re.sub(r"\s+", " ", _h.unescape(TAG.sub(" ", s or ""))).strip()[:n]


def parse_hn(payload: bytes) -> list[dict]:
    out = []
    for h in json.loads(payload).get("hits", []):
        is_comment = bool(h.get("comment_text"))
        oid = h.get("objectID")
        out.append({
            "source": "hn", "kind": "pain",
            "url": h.get("url") if (h.get("url") and not is_comment) else f"https://news.ycombinator.com/item?id={oid}",
            "title": _clean(h.get("title") or h.get("story_title") or ""),
            "text": _clean(h.get("comment_text") or h.get("story_text") or ""),
            "author": h.get("author") or "", "community": "Hacker News",
            "created": _ts(h.get("created_at_i") or h.get("created_at")),
            "engagement": (h.get("points") or 0) + (h.get("num_comments") or 0),
        })
    return out


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_feed(payload: bytes, source: str = "rss", community: str = "") -> list[dict]:
    """RSS 2.0 and Atom (Reddit, hnrss, Google Alerts/News, blogs, job boards)."""
    root = ET.fromstring(payload)
    title = ""
    for el in root.iter():
        if _local(el.tag) == "title":
            title = _clean(el.text or "")
            break
    out = []
    for item in root.iter():
        if _local(item.tag) not in ("item", "entry"):
            continue
        f = {"title": "", "text": "", "url": "", "author": "", "created": ""}
        for ch in item:
            t = _local(ch.tag)
            if t == "title":
                f["title"] = _clean(ch.text or "")
            elif t in ("description", "summary", "content", "encoded") and not f["text"]:
                f["text"] = _clean(ch.text or "")
            elif t == "link":
                f["url"] = f["url"] or ch.get("href") or (ch.text or "").strip()
            elif t in ("author", "creator"):
                name = next((_clean(g.text or "") for g in ch if _local(g.tag) == "name"), "") or _clean(ch.text or "")
                f["author"] = f["author"] or name
            elif t in ("pubDate", "published", "updated", "date") and not f["created"]:
                f["created"] = _ts(ch.text)
        out.append({"source": source, "kind": "pain", "community": community or title, "engagement": 0, **f})
    return out


def parse_stackexchange(payload: bytes, site: str) -> list[dict]:
    return [{
        "source": "stackexchange", "kind": "pain", "url": q.get("link", ""), "title": _clean(q.get("title", "")),
        "text": _clean(q.get("body", "")), "author": (q.get("owner") or {}).get("display_name", ""),
        "community": site, "created": _ts(q.get("creation_date")),
        "engagement": (q.get("score") or 0) + (q.get("answer_count") or 0) * 2 + (q.get("view_count") or 0) // 100,
    } for q in json.loads(payload).get("items", [])]


def parse_appstore(payload: bytes, app_id: str, country: str) -> list[dict]:
    entries = ((json.loads(payload).get("feed") or {}).get("entry")) or []
    entries = [entries] if isinstance(entries, dict) else entries
    out = []
    for e in entries:
        if "im:rating" not in e:      # the first entry can be the app itself
            continue
        rating = int((e.get("im:rating") or {}).get("label") or 0)
        out.append({
            "source": "appstore", "kind": "review",
            "url": f"https://apps.apple.com/{country}/app/id{app_id}#review-{(e.get('id') or {}).get('label', '')}",
            "title": _clean((e.get("title") or {}).get("label", "")),
            "text": _clean((e.get("content") or {}).get("label", "")),
            "author": ((e.get("author") or {}).get("name") or {}).get("label", ""),
            "community": f"App Store {country.upper()} {app_id} ★{rating}", "rating": rating,
            "created": _ts((e.get("updated") or {}).get("label")),
            "engagement": int((e.get("im:voteSum") or {}).get("label") or 0),
        })
    return out


def _q(s: str) -> str:
    return urllib.parse.quote_plus(s)


def fetch_hn(src: dict, cfg: dict, days: int) -> list[dict]:
    since = int(time.time()) - days * 86400
    out = []
    for q in src.get("queries") or []:
        for tags in src.get("tags", ["story", "comment"]):
            url = (f"https://hn.algolia.com/api/v1/search_by_date?query={_q(q)}&tags={tags}"
                   f"&numericFilters=created_at_i>{since}&hitsPerPage={src.get('per_query', 30)}")
            out += parse_hn(_get(url, cfg))
    return out


def _feed_urls(src: dict) -> list[tuple[str, str]]:
    """(url, community) for every feed this source expands to."""
    urls = [(u, "") for u in src.get("feeds") or []]
    for sub in src.get("subreddits") or []:
        urls.append((f"https://www.reddit.com/r/{sub}/new/.rss", f"r/{sub}"))
    for q in src.get("reddit_search") or []:
        urls.append((f"https://www.reddit.com/search.rss?q={_q(q)}&sort=new&t=week", "Reddit search"))
    for q in src.get("hnrss") or []:
        urls.append((f"https://hnrss.org/newest?q={_q(q)}", "Hacker News"))
    gl = src.get("google_news_locale") or {}
    for q in src.get("google_news") or []:
        urls.append((f"https://news.google.com/rss/search?q={_q(q)}&hl={gl.get('hl', 'en')}"
                     f"&gl={gl.get('gl', 'US')}&ceid={gl.get('gl', 'US')}:{gl.get('hl', 'en')}", "Google News"))
    return urls


def fetch_rss(src: dict, cfg: dict, days: int) -> list[dict]:
    out = []
    for url, community in _feed_urls(src):
        out += parse_feed(_get(url, cfg), "rss", community)
        time.sleep(src.get("delay_s", 1))
    kws = [k.lower() for k in src.get("keywords") or []]
    if kws:   # optional filter: keep items that mention any keyword
        out = [s for s in out if any(k in f"{s['title']} {s['text']}".lower() for k in kws)]
    return out


def fetch_stackexchange(src: dict, cfg: dict, days: int) -> list[dict]:
    since = int(time.time()) - days * 86400
    out = []
    for site in src.get("sites") or ["stackoverflow"]:
        for q in src.get("queries") or []:
            url = (f"https://api.stackexchange.com/2.3/search/advanced?order=desc&sort=creation&q={_q(q)}"
                   f"&site={_q(site)}&fromdate={since}&pagesize={src.get('per_query', 30)}&filter=withbody")
            out += parse_stackexchange(_get(url, cfg), site)
    return out


def fetch_appstore(src: dict, cfg: dict, days: int) -> list[dict]:
    out = []
    for app in src.get("apps") or []:
        app_id, country = str(app["id"]), app.get("country", "us").lower()
        for page in range(1, int(src.get("pages", 2)) + 1):
            url = (f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}"
                   f"/sortby=mostrecent/json")
            got = parse_appstore(_get(url, cfg), app_id, country)
            out += got
            if not got:
                break
    max_rating = src.get("max_rating", 5)
    return [s for s in out if s.get("rating", 0) <= max_rating]


FETCHERS = {"hn": fetch_hn, "rss": fetch_rss, "stackexchange": fetch_stackexchange, "appstore": fetch_appstore}


# ---------------------------------------------------------------- store

SCHEMA = """
create table if not exists signals(
  id integer primary key, key text unique, content_hash text, source text, kind text, url text, title text,
  text text, author text, community text, created text, engagement integer, rating integer,
  score integer, persona text, matched text, class text, status text default 'new', note text default '',
  first_seen text, run_id integer);
create index if not exists ix_content on signals(content_hash);
create table if not exists runs(id integer primary key, ts text, fetched integer, new integer,
  errors text, sources text);
"""
TRACKING = re.compile(r"^(utm_|ref$|ref_src$|fbclid$|gclid$)")


def norm_url(u: str) -> str:
    p = urllib.parse.urlsplit((u or "").strip())
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query) if not TRACKING.match(k)]
    host = p.netloc.lower().removeprefix("www.").removeprefix("old.")
    return urllib.parse.urlunsplit((p.scheme.lower(), host, p.path.rstrip("/"), urllib.parse.urlencode(q), ""))


def _content_hash(sig: dict) -> str:
    body = re.sub(r"\W+", " ", f"{sig.get('title', '')} {sig.get('text', '')}".lower()).strip()[:500]
    body = body or norm_url(sig.get("url", "")) or json.dumps(sig, sort_keys=True, default=str)
    return hashlib.sha256(body.encode()).hexdigest()[:20]


class Store:
    def __init__(self, path: Path | None = None):
        self.path = path or DATA / "signals.db"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def start_run(self, sources: list[str]) -> int:
        cur = self.db.execute("insert into runs(ts, fetched, new, errors, sources) values(?,?,?,?,?)",
                              (dt.datetime.now().isoformat(timespec="seconds"), 0, 0, "[]", json.dumps(sources)))
        self.db.commit()
        return cur.lastrowid

    def finish_run(self, run_id: int, fetched: int, new: int, errors: list[str]) -> None:
        self.db.execute("update runs set fetched=?, new=?, errors=? where id=?",
                        (fetched, new, json.dumps(errors), run_id))
        self.db.commit()

    def add(self, sig: dict, sc: dict, cls: str, run_id: int | None) -> bool:
        """Insert unless the same URL or the same text (cross-post) is already stored."""
        key = norm_url(sig.get("url", "")) or _content_hash(sig)
        ch = _content_hash(sig)
        if self.db.execute("select 1 from signals where key=? or content_hash=?", (key, ch)).fetchone():
            return False
        self.db.execute(
            "insert into signals(key, content_hash, source, kind, url, title, text, author, community, created,"
            " engagement, rating, score, persona, matched, class, first_seen, run_id)"
            " values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (key, ch, sig.get("source", ""), sig.get("kind", "pain"), sig.get("url", ""), sig.get("title", ""),
             sig.get("text", ""), sig.get("author", ""), sig.get("community", ""), sig.get("created", ""),
             int(sig.get("engagement") or 0), sig.get("rating"), sc["score"], sc["persona"],
             json.dumps({k: sc[k] for k in ("pain", "intent", "negative")}), cls,
             dt.datetime.now().isoformat(timespec="seconds"), run_id))
        return True

    def rows(self, where: str = "1=1", args: tuple = (), order: str = "score desc, id desc",
             limit: int = 1000) -> list[sqlite3.Row]:
        return self.db.execute(f"select * from signals where {where} order by {order} limit ?",  # noqa: S608
                               (*args, limit)).fetchall()

    def mark(self, sid: int, status: str, note: str = "") -> bool:
        if status not in STATUSES:
            raise ValueError(f"status must be one of {STATUSES}")
        cur = self.db.execute("update signals set status=?, note=case when ?='' then note else ? end where id=?",
                              (status, note, note, sid))
        self.db.commit()
        return cur.rowcount == 1

    def last_run(self) -> dict | None:
        r = self.db.execute("select * from runs order by id desc limit 1").fetchone()
        return dict(r) if r else None


# ---------------------------------------------------------------- pipeline

def prepare(sig: dict) -> dict:
    """Redact secrets from fetched text before anything is stored."""
    for f in ("title", "text"):
        sig[f], findings = secret_scanner.redact(sig.get(f) or "")
        if findings:
            sig.setdefault("_secrets", []).extend(x.kind for x in findings)
    return sig


def _too_old(sig: dict, days: int) -> bool:
    if not sig.get("created"):
        return False
    return dt.datetime.fromisoformat(sig["created"]) < dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)


def ingest(signals: list[dict], cfg: dict, store: Store, run_id: int | None = None) -> dict:
    rules, days, keep = cfg.get("rules") or {}, int(cfg.get("lookback_days", 7)), int(cfg.get("min_score_to_keep", 10))
    new = kept_low = old = 0
    secrets = []
    for sig in signals:
        sig = prepare(dict(sig))
        if sig.get("_secrets"):
            secrets.append(f"{sig.get('source')}: {sig.get('url') or sig.get('title', '')[:60]}")
        if sig.get("kind") != "import" and _too_old(sig, days):
            old += 1
            continue
        sc = score(sig, rules)
        if sc["score"] < keep:
            kept_low += 1
            continue
        new += store.add(sig, sc, classify(sig, sc, cfg), run_id)
    store.db.commit()
    return {"new": new, "below_min_score": kept_low, "too_old": old, "secrets_redacted_at": secrets}


def run(cfg: dict | None = None, store: Store | None = None, only: str | None = None,
        fetchers: dict | None = None) -> dict:
    cfg = cfg or load_config()
    store = store or Store()
    fetchers = fetchers or FETCHERS
    sources = {k: v for k, v in (cfg.get("sources") or {}).items() if v.get("enabled") and (not only or k == only)}
    if not sources:
        return {"run_id": None, "sources": [], "fetched": 0, "errors": [], "new": 0, "below_min_score": 0,
                "too_old": 0, "secrets_redacted_at": []}
    run_id = store.start_run(sorted(sources))
    days, fetched, errors, sigs = int(cfg.get("lookback_days", 7)), 0, [], []
    max_items = int(cfg.get("max_items_per_run", 2000))
    for name, src in sources.items():
        try:
            got = fetchers[name](src, cfg, days)
        except Exception as e:  # noqa: BLE001 - one source down must not stop the run; it is reported
            errors.append(f"{name}: {type(e).__name__}: {str(e)[:120]}")
            continue
        fetched += len(got)
        sigs += got
    res = ingest(sigs[:max_items], cfg, store, run_id)
    store.finish_run(run_id, fetched, res["new"], errors)
    write_pains(cfg, store)
    return {"run_id": run_id, "sources": sorted(sources), "fetched": fetched, "errors": errors, **res}


def rescore(cfg: dict, store: Store) -> int:
    n = 0
    for r in store.rows(limit=10**9):
        sig = dict(r)
        sc = score(sig, cfg.get("rules") or {})
        store.db.execute("update signals set score=?, persona=?, matched=?, class=? where id=?",
                         (sc["score"], sc["persona"], json.dumps({k: sc[k] for k in ("pain", "intent", "negative")}),
                          classify(sig, sc, cfg), r["id"]))
        n += 1
    store.db.commit()
    write_pains(cfg, store)
    return n


def import_file(path: Path, cfg: dict, store: Store) -> dict:
    """JSON list / {"signals": [...]} or CSV with url,title,text[,author,community,created]."""
    if path.suffix.lower() == ".csv":
        with open(path, encoding="utf-8", newline="") as fh:
            items = list(csv.DictReader(fh))
    else:
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data.get("signals", []) if isinstance(data, dict) else data
    sigs = [{"source": it.get("source") or "import", "kind": it.get("kind") or "import", **{
        k: it.get(k, "") for k in ("url", "title", "text", "author", "community", "created")},
        "engagement": int(it.get("engagement") or 0)} for it in items]
    for s in sigs:
        s["created"] = _ts(s["created"]) if s["created"] else ""
    return ingest(sigs, cfg, store)


# ---------------------------------------------------------------- outputs

ANON = [(re.compile(r"https?://\S+"), "[link]"), (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "[email]"),
        (re.compile(r"(?<!\w)@[A-Za-z0-9_.]{2,}|(?<![\w/])/?u/[A-Za-z0-9_-]{3,}"), "[user]"), (re.compile(r"\+?\d[\d\s().-]{7,}\d"), "[phone]")]


def anonymise(text: str, n: int = 160) -> str:
    for rx, rep in ANON:
        text = rx.sub(rep, text or "")
    return text[:n] + ("…" if len(text) > n else "")


def pains(store: Store, days: int = 30) -> list[dict]:
    """Aggregated pains: phrase -> count, sources, average score, one anonymised example. No usernames."""
    since = (dt.datetime.now() - dt.timedelta(days=days)).isoformat()
    agg: dict[str, dict] = {}
    for r in store.rows("first_seen >= ? and status != 'ignored'", (since,), limit=10**9):
        for p in json.loads(r["matched"] or "{}").get("pain", []):
            a = agg.setdefault(p, {"pain": p, "count": 0, "sources": set(), "score_sum": 0, "example": "", "best": -1})
            a["count"] += 1
            a["sources"].add(r["source"])
            a["score_sum"] += r["score"]
            if r["score"] > a["best"]:
                a["best"], a["example"] = r["score"], anonymise(f"{r['title']} — {r['text']}")
    out = [{"pain": a["pain"], "count": a["count"], "sources": sorted(a["sources"]),
            "avg_score": round(a["score_sum"] / a["count"]), "example": a["example"]} for a in agg.values()]
    return sorted(out, key=lambda x: (-x["count"], -x["avg_score"]))


def pains_markdown(cfg: dict, store: Store, days: int = 30) -> str:
    rows = pains(store, days)
    total = store.db.execute("select count(*) from signals where first_seen >= ?",
                             ((dt.datetime.now() - dt.timedelta(days=days)).isoformat(),)).fetchone()[0]
    lines = [f"Focus: {cfg.get('focus') or '(not set)'}",
             f"Window: last {days} days · signals kept: {total} · generated {dt.date.today().isoformat()}",
             "", "| pain phrase | count | sources | avg score | example (anonymised) |", "|---|---|---|---|---|"]
    lines += [f"| {r['pain']} | {r['count']} | {', '.join(r['sources'])} | {r['avg_score']} | "
              f"{r['example'].replace('|', '/')} |" for r in rows] or ["| (none yet) | | | | |"]
    return "\n".join(lines)


def write_pains(cfg: dict, store: Store, days: int = 30) -> Path:
    """work/listen/pains.md — what agents read. Wrapped as untrusted: it quotes public posts."""
    path = store.path.parent / "pains.md"
    body = untrusted.wrap("robin listen (public posts, aggregated)", pains_markdown(cfg, store, days))
    path.write_text("# Listening: pains (aggregated, no personal data)\n\n" + body + "\n", encoding="utf-8")
    return path


def precision_at(store: Store, k: int = 20) -> dict:
    """Of the top-k reviewed signals by score, the share marked qualified/contacted/replied."""
    rows = store.rows("status != 'new'", limit=k)
    good = sum(1 for r in rows if r["status"] in GOOD)
    return {"k": k, "reviewed": len(rows), "good": good, "precision": round(good / len(rows), 2) if rows else None}


def export(store: Store, fmt: str = "csv", where: str = "1=1", args: tuple = ()) -> Path:
    rows = [dict(r) for r in store.rows(where, args, limit=10**9)]
    path = store.path.parent / f"leads-{dt.date.today().isoformat()}.{fmt}"
    if fmt == "json":
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    else:
        with open(path, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["id"])
            w.writeheader()
            w.writerows(rows)
    return path


def new_leads_since(store: Store, hours: float = 24, min_score: int = 60) -> int:
    since = (dt.datetime.now() - dt.timedelta(hours=hours)).isoformat()
    return store.db.execute("select count(*) from signals where class='lead' and status='new' and score>=? "
                            "and first_seen>=?", (min_score, since)).fetchone()[0]
