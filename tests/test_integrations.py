import shutil
from pathlib import Path

from robin import integrations as integ

ROOT = Path(__file__).resolve().parent.parent


def _cfg(tmp_path):
    dst = tmp_path / "integrations.yaml"
    shutil.copy(ROOT / "config" / "integrations.yaml", dst)
    return dst


def test_everything_off_by_default():
    cfg = integ.config()
    assert all(not v.get("enabled") for v in cfg["mcp"].values())
    assert integ.mcp_servers(cfg) == {}


def test_enabled_tool_loads_only_when_keys_set(tmp_path, monkeypatch):
    path = _cfg(tmp_path)
    integ.set_enabled("posthog", True, path)
    cfg = integ.config(path)
    monkeypatch.delenv("POSTHOG_MCP_URL", raising=False)
    monkeypatch.delenv("POSTHOG_API_KEY", raising=False)
    assert "posthog" not in integ.mcp_servers(cfg)  # missing keys -> skipped, not broken
    monkeypatch.setenv("POSTHOG_MCP_URL", "https://example.invalid/mcp")
    monkeypatch.setenv("POSTHOG_API_KEY", "test-value")
    server = integ.mcp_servers(cfg)["posthog"]
    assert server["url"] == "https://example.invalid/mcp"
    assert server["headers"]["Authorization"] == "Bearer test-value"


def test_toggle_keeps_comments(tmp_path):
    path = _cfg(tmp_path)
    before = path.read_text()
    integ.set_enabled("notion", True, path)
    integ.set_enabled("notion", False, path)
    assert path.read_text() == before


def test_env_file_loads_without_overriding(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("# comment\nROBIN_TEST_A=one\nROBIN_TEST_B=\nROBIN_TEST_C=new\n")
    monkeypatch.delenv("ROBIN_TEST_A", raising=False)
    monkeypatch.setenv("ROBIN_TEST_C", "existing")
    loaded = integ.load_env_file(env)
    assert loaded == ["ROBIN_TEST_A"]
    import os
    assert os.environ["ROBIN_TEST_C"] == "existing"


def test_doctor_never_prints_key_values(monkeypatch, capsys):
    from robin.cli import main
    monkeypatch.setenv("ANTHROPIC_API_KEY", "value-that-must-not-print")
    main(["doctor"])
    out = capsys.readouterr().out
    assert "value-that-must-not-print" not in out
    assert "model      anthropic        ready" in out


def test_dry_run_needs_no_key(monkeypatch, capsys):
    from robin.cli import main
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert main(["ask", "--dry-run", "Why did FTD drop in Mexico?"]) == 0
    assert "route: data-analyst" in capsys.readouterr().out
