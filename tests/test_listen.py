import datetime as dt
import json
import time

import pytest

from robin import listen

NOW = int(time.time())
ISO_NOW = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
RULES = {
    "pain": {"too many tickets": 12, "overwhelmed": 6},
    "intent": {"looking for": 10, "any recommendations": 12},
    "persona": {"shop": ["shopify", "store"], "saas": ["saas"]},
    "negative": {"we help": -15, "dm me": -12},
}
CFG = {"focus": "test", "lookback_days": 7, "min_score_to_keep": 10, "lead": {"min_score": 40, "min_intent": 10},
       "allowed_hosts": ["hn.algolia.com", "reddit.com"], "sources": {}, "rules": RULES}


@pytest.fixture
def store(tmp_path):
    return listen.Store(tmp_path / "signals.db")


def sig(title, text="", **kw):
    return {"source": "test", "kind": "pain", "url": kw.pop("url", f"https://x.test/{abs(hash(title))}"),
            "title": title, "text": text, "author": "someone", "community": "", "created": ISO_NOW, **kw}


def test_repo_config_valid_generic_and_off():
    cfg = listen.load_config(private=None)
    assert listen.validate_config(cfg) == []
    assert all(not s.get("enabled") for s in cfg["sources"].values())   # public repo: everything off
    assert cfg["focus"].startswith("Example")


def test_score_is_explainable_and_capped():
    s = listen.score(sig("Too many tickets, looking for a tool. Any recommendations?", "our Shopify store"), RULES)
    assert s["pain"] == ["too many tickets"] and set(s["intent"]) == {"looking for", "any recommendations"}
    assert s["persona"] == "shop" and s["score"] == 12 + 22 + 6 + 5
    assert listen.classify({}, s, CFG) == "lead"
    seller = listen.score(sig("Too many tickets? We help. DM me"), RULES)
    assert seller["negative"] and listen.classify({}, seller, CFG) != "lead"


def test_word_edges_ascii_and_substring_for_unspaced_scripts():
    rules = {"pain": {"cac": 6, "ถอนเงินช้า": 10}, "intent": {}, "persona": {}, "negative": {}}
    assert listen.score(sig("cache issue"), rules)["pain"] == []
    assert listen.score(sig("our CAC doubled"), rules)["pain"] == ["cac"]
    assert listen.score(sig("ทำไมถอนเงินช้ามาก"), rules)["pain"] == ["ถอนเงินช้า"]


def test_parse_hn_and_feed_and_stackexchange_and_appstore():
    hn = json.dumps({"hits": [{"objectID": "1", "title": "Ask HN: too many tickets", "story_text": "<p>help</p>",
                               "author": "a", "created_at_i": NOW, "points": 12, "num_comments": 3}]}).encode()
    h = listen.parse_hn(hn)[0]
    assert h["url"].endswith("item?id=1") and h["text"] == "help" and h["engagement"] == 15
    atom = b"""<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><title>r/shop</title>
      <entry><title>Overwhelmed</title><link href="https://www.reddit.com/r/shop/comments/abc/x/"/>
      <author><name>/u/bob</name></author><updated>2026-11-15T10:00:00+00:00</updated>
      <content type="html">&lt;p&gt;too many tickets&lt;/p&gt;</content></entry></feed>"""
    f = listen.parse_feed(atom, "rss", "r/shop")[0]
    assert f["text"] == "too many tickets" and f["author"] == "/u/bob" and f["created"].startswith("2026-11-15")
    rss = b"""<rss><channel><title>HN</title><item><title>Q</title><link>https://n.test/1</link>
      <pubDate>Sun, 15 Nov 2026 10:00:00 GMT</pubDate><description>d</description></item></channel></rss>"""
    assert listen.parse_feed(rss)[0]["url"] == "https://n.test/1"
    se = json.dumps({"items": [{"link": "https://s.test/q/1", "title": "t", "body": "b", "owner": {"display_name": "x"},
                                "creation_date": NOW, "score": 2, "answer_count": 1, "view_count": 300}]}).encode()
    assert listen.parse_stackexchange(se, "webapps")[0]["engagement"] == 7
    ap = json.dumps({"feed": {"entry": [{"im:name": {"label": "App"}},
        {"id": {"label": "9"}, "title": {"label": "Slow"}, "content": {"label": "withdrawal slow"},
         "author": {"name": {"label": "z"}}, "im:rating": {"label": "1"}, "updated": {"label": ISO_NOW}}]}}).encode()
    a = listen.parse_appstore(ap, "123", "ph")
    assert len(a) == 1 and a[0]["rating"] == 1 and "★1" in a[0]["community"]


def test_dedup_by_url_and_crosspost(store):
    a = sig("Too many tickets here", url="https://www.reddit.com/r/x/1/?utm_source=t")
    b = sig("Too many tickets here", url="https://reddit.com/r/x/1")           # same url, normalised
    c = sig("Too many tickets here", url="https://other.test/post")              # same text elsewhere
    assert listen.ingest([a, b, c], CFG, store)["new"] == 1


def test_drops_old_low_and_redacts_secrets(store):
    old = sig("too many tickets", created="2020-01-01T00:00:00+00:00")
    low = sig("nice weather")
    leak = sig("too many tickets", "my key sk-ant-" + "a" * 30, url="https://x.test/leak")
    res = listen.ingest([old, low, leak], CFG, store)
    assert (res["new"], res["too_old"], res["below_min_score"]) == (1, 1, 1)
    assert res["secrets_redacted_at"]
    assert "sk-ant-" not in store.rows()[0]["text"]


def test_host_allowlist():
    with pytest.raises(PermissionError):
        listen._get("https://evil.test/feed", CFG)


def test_run_reports_down_source_and_continues(store, tmp_path):
    def ok(src, cfg, days):
        return [sig("Looking for help: too many tickets. Any recommendations?", "our shopify store")]

    def down(src, cfg, days):
        raise OSError("403")
    cfg = {**CFG, "sources": {"hn": {"enabled": True}, "rss": {"enabled": True}}}
    res = listen.run(cfg, store, fetchers={"hn": ok, "rss": down})
    assert res["new"] == 1 and res["errors"] and "rss" in res["errors"][0]
    assert (store.path.parent / "pains.md").exists()
    assert listen.new_leads_since(store, min_score=40) == 1


def test_mark_rescore_precision(store):
    listen.ingest([sig("too many tickets, looking for", url="https://x.test/1"),
                   sig("overwhelmed by too many tickets?", url="https://x.test/2")], CFG, store)
    ids = [r["id"] for r in store.rows()]
    store.mark(ids[0], "qualified")
    store.mark(ids[1], "ignored", "seller")
    assert listen.precision_at(store)["precision"] == 0.5
    with pytest.raises(ValueError):
        store.mark(ids[0], "spam")
    cfg = {**CFG, "rules": {**RULES, "pain": {"too many tickets": 6}}}
    assert listen.rescore(cfg, store) == 2


def test_pains_are_aggregated_and_anonymised(store):
    listen.ingest([sig("too many tickets", "ping @bob or bob@mail.test, see https://x.test/a u/alice +63 912 345 6789",
                       url="https://x.test/1"),
                   sig("overwhelmed and too many tickets", url="https://x.test/2")], CFG, store)
    rows = listen.pains(store)
    assert rows[0]["pain"] == "too many tickets" and rows[0]["count"] == 2
    md = listen.pains_markdown(CFG, store)
    for leaked in ("@bob", "bob@mail.test", "https://x.test", "u/alice", "912 345", "someone"):
        assert leaked not in md
    wrapped = listen.write_pains(CFG, store).read_text(encoding="utf-8")
    assert "<untrusted" in wrapped


def test_import_csv(store, tmp_path):
    f = tmp_path / "in.csv"
    f.write_text("url,title,text\nhttps://g.test/1,Looking for a helpdesk,too many tickets\n", encoding="utf-8")
    assert listen.import_file(f, CFG, store)["new"] == 1
