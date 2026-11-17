import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from robin import ui


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(ui, "ENV_FILE", tmp_path / ".env")
    monkeypatch.setattr(ui, "ORG", tmp_path / "org.yaml")
    (tmp_path / "org.yaml").write_text("# comment kept\nactive_departments: [product]\n")
    return tmp_path


def test_set_key_allowlist_and_never_echoed(env):
    with pytest.raises(ValueError):
        ui.set_key("EVIL", "x")
    assert ui.set_key("ANTHROPIC_API_KEY", "abc123secret") == "ANTHROPIC_API_KEY saved"
    assert ui.key_status()["ANTHROPIC_API_KEY"] is True
    assert (env / ".env").stat().st_mode & 0o077 == 0          # owner-only file
    ui.set_key("ANTHROPIC_API_KEY", "")
    assert ui.key_status()["ANTHROPIC_API_KEY"] is False


def test_departments_saved_and_comments_kept(env):
    ui.set_departments(["data", "marketing", "bogus"])
    text = (env / "org.yaml").read_text()
    assert "# comment kept" in text and "bogus" not in text and "data" in text


@pytest.fixture
def server(env, monkeypatch):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), ui.make_handler("tok"))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()


def test_token_required(server):
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(server + "/")
    assert e.value.code == 403
    body = urllib.request.urlopen(server + "/?t=tok").read().decode()
    assert "Setup checklist" in body and "Ask Robin" in body


def test_post_key_never_shows_value(server, env):
    data = urllib.parse.urlencode({"t": "tok", "name": "ANTHROPIC_API_KEY", "value": "sk-supersecret-value"}).encode()
    body = urllib.request.urlopen(server + "/key", data=data).read().decode()
    assert "sk-supersecret-value" not in body and "set" in body
    bad = urllib.parse.urlencode({"t": "wrong", "name": "ANTHROPIC_API_KEY", "value": "x"}).encode()
    with pytest.raises(urllib.error.HTTPError):
        urllib.request.urlopen(server + "/key", data=bad)


def test_preview_routes_without_model(server):
    data = urllib.parse.urlencode({"t": "tok", "q": "Why did FTD drop in Mexico?", "mode": "preview"}).encode()
    body = urllib.request.urlopen(server + "/ask", data=data).read().decode()
    assert "data-analyst" in body and "No model call" in body
