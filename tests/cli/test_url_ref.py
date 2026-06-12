"""Tests for URL-based profile resolution and resolve_ref helper."""

import pytest
import yaml
from unittest.mock import MagicMock, patch
from click.testing import CliRunner

from redmine_cli.config import resolve_profile_by_url
from redmine_cli.context import resolve_ref
from redmine_cli.main import cli


def _config_file(tmp_path, data=None):
    p = tmp_path / "config.yaml"
    p.write_text(yaml.dump(data or {}))
    return p


def _mock_ctx(profile=None):
    """Create a minimal Click-like context object."""
    return MagicMock(obj={"_profile": profile})


# --- resolve_profile_by_url ---


def test_resolve_profile_by_url_exact_match(tmp_path, monkeypatch):
    cf = _config_file(tmp_path, {
        "profiles": {
            "redminex": {"url": "https://redminex.silksoftware.com/", "api_key": "key1"},
            "staging": {"url": "https://staging.example.com/", "api_key": "key2"},
        }
    })
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    assert resolve_profile_by_url("https://redminex.silksoftware.com/issues/123") == "redminex"
    assert resolve_profile_by_url("https://staging.example.com/issues/456") == "staging"


def test_resolve_profile_by_url_from_profiles(tmp_path, monkeypatch):
    cf = _config_file(tmp_path, {
        "profiles": {
            "staging": {"url": "https://staging.test/", "api_key": "key1"},
        }
    })
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    assert resolve_profile_by_url("https://staging.test/issues/2") == "staging"
    assert resolve_profile_by_url("https://unknown.test/issues/1") is None


def test_resolve_profile_by_url_longest_prefix(tmp_path, monkeypatch):
    """Longest prefix wins when two profiles could match."""
    cf = _config_file(tmp_path, {
        "profiles": {
            "general": {"url": "https://redmine.example.com/", "api_key": "key1"},
            "subpath": {"url": "https://redmine.example.com/redmine2/", "api_key": "key2"},
        }
    })
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    assert resolve_profile_by_url("https://redmine.example.com/redmine2/issues/5") == "subpath"
    assert resolve_profile_by_url("https://redmine.example.com/issues/5") == "general"


def test_resolve_profile_by_url_no_match(tmp_path, monkeypatch):
    cf = _config_file(tmp_path, {
        "profiles": {
            "staging": {"url": "https://staging.test/", "api_key": "key1"},
        }
    })
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    assert resolve_profile_by_url("https://unknown.test/issues/1") is None


# --- resolve_ref ---


def test_resolve_ref_integer():
    """Plain integer requires -p or REDMINE_URL to be set."""
    ctx = _mock_ctx(profile="staging")
    assert resolve_ref(ctx, "123") == 123
    assert resolve_ref(ctx, "99999") == 99999


def test_resolve_ref_integer_with_url_override():
    """Plain integer works when _url is set (via REDMINE_URL env var)."""
    ctx = _mock_ctx()
    ctx.obj["_url"] = "https://redmine.test/"
    assert resolve_ref(ctx, "123") == 123


def test_resolve_ref_integer_without_profile_or_url_raises():
    """Plain integer without -p and without REDMINE_URL should raise UsageError."""
    import click
    ctx = _mock_ctx()
    with pytest.raises(click.UsageError, match="Profile is required"):
        resolve_ref(ctx, "123")


def test_resolve_ref_string_identifier():
    """String identifier requires -p or REDMINE_URL to be set."""
    ctx = _mock_ctx(profile="staging")
    assert resolve_ref(ctx, "my-project") == "my-project"
    assert resolve_ref(ctx, "current") == "current"


def test_resolve_ref_string_without_profile_or_url_raises():
    """String identifier without -p and without REDMINE_URL should raise UsageError."""
    import click
    ctx = _mock_ctx()
    with pytest.raises(click.UsageError, match="Profile is required"):
        resolve_ref(ctx, "my-project")


def test_resolve_ref_url_extracts_id(tmp_path, monkeypatch):
    cf = _config_file(tmp_path, {
        "profiles": {
            "redminex": {"url": "https://redminex.silksoftware.com/", "api_key": "k"},
        }
    })
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))

    ctx = _mock_ctx()
    result = resolve_ref(ctx, "https://redminex.silksoftware.com/issues/456")
    assert result == 456
    assert ctx.obj["_profile"] == "redminex"


def test_resolve_ref_url_sets_profile_only_when_not_set(tmp_path, monkeypatch):
    cf = _config_file(tmp_path, {
        "profiles": {
            "redminex": {"url": "https://redminex.silksoftware.com/", "api_key": "k"},
        }
    })
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))

    # Profile already set via -p -> should NOT be overridden
    ctx = _mock_ctx(profile="explicit-profile")
    result = resolve_ref(ctx, "https://redminex.silksoftware.com/issues/123")
    assert result == 123
    assert ctx.obj["_profile"] == "explicit-profile"


def test_resolve_ref_url_no_matching_profile_raises(tmp_path, monkeypatch):
    cf = _config_file(tmp_path, {
        "profiles": {
            "other": {"url": "https://other.test/", "api_key": "k"},
        }
    })
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))

    import click
    ctx = _mock_ctx()
    with pytest.raises(click.UsageError, match="No configured profile matches"):
        resolve_ref(ctx, "https://unknown.test/issues/123")


def test_resolve_ref_url_with_edit_suffix(tmp_path, monkeypatch):
    cf = _config_file(tmp_path, {
        "profiles": {
            "redminex": {"url": "https://redminex.silksoftware.com/", "api_key": "k"},
        }
    })
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))

    ctx = _mock_ctx()
    result = resolve_ref(ctx, "https://redminex.silksoftware.com/issues/789/edit")
    assert result == 789


def test_resolve_ref_url_with_project_identifier(tmp_path, monkeypatch):
    cf = _config_file(tmp_path, {
        "profiles": {
            "redminex": {"url": "https://redminex.silksoftware.com/", "api_key": "k"},
        }
    })
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))

    ctx = _mock_ctx()
    result = resolve_ref(ctx, "https://redminex.silksoftware.com/projects/my-project")
    assert result == "my-project"
    assert ctx.obj["_profile"] == "redminex"


def test_resolve_ref_url_with_subpath_redmine(tmp_path, monkeypatch):
    cf = _config_file(tmp_path, {
        "profiles": {
            "kettle": {"url": "http://redminetest.kettle.net.cn:7777/redmine2/", "api_key": "k"},
        }
    })
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))

    ctx = _mock_ctx()
    result = resolve_ref(ctx, "http://redminetest.kettle.net.cn:7777/redmine2/issues/42")
    assert result == 42
    assert ctx.obj["_profile"] == "kettle"


# --- CLI integration: issue get with URL ---


def test_issue_get_by_url(tmp_path, monkeypatch):
    cf = _config_file(tmp_path, {
        "profiles": {
            "redminex": {"url": "https://redminex.silksoftware.com/", "api_key": "testkey"},
        }
    })
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    monkeypatch.delenv("REDMINE_URL", raising=False)
    monkeypatch.delenv("REDMINE_API_KEY", raising=False)

    with patch("redmine_cli.context.create_redmine") as mock_create:
        rm = MagicMock()
        rm.url = "https://redminex.silksoftware.com/"
        rm.issue.get.return_value = MagicMock(
            raw=lambda: {"id": 42, "subject": "URL-resolved issue"}
        )
        mock_create.return_value = rm

        runner = CliRunner()
        result = runner.invoke(cli, ["issue", "get", "https://redminex.silksoftware.com/issues/42"])
        assert result.exit_code == 0
        rm.issue.get.assert_called_with(42)
        # Verify create_redmine was called with profile="redminex"
        mock_create.assert_called_with(profile="redminex")


def test_issue_get_by_url_no_profile_error(tmp_path, monkeypatch):
    cf = _config_file(tmp_path, {
        "profiles": {
            "other": {"url": "https://other.test/", "api_key": "k"},
        }
    })
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    monkeypatch.delenv("REDMINE_URL", raising=False)
    monkeypatch.delenv("REDMINE_API_KEY", raising=False)

    runner = CliRunner()
    result = runner.invoke(cli, ["issue", "get", "https://unknown.test/issues/1"])
    assert result.exit_code != 0
    assert "No configured profile matches" in result.output


def test_issue_update_by_url(tmp_path, monkeypatch):
    cf = _config_file(tmp_path, {
        "profiles": {
            "redminex": {"url": "https://redminex.silksoftware.com/", "api_key": "testkey"},
        }
    })
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    monkeypatch.delenv("REDMINE_URL", raising=False)
    monkeypatch.delenv("REDMINE_API_KEY", raising=False)

    with patch("redmine_cli.context.create_redmine") as mock_create:
        rm = MagicMock()
        rm.url = "https://redminex.silksoftware.com/"
        mock_create.return_value = rm

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["issue", "update", "https://redminex.silksoftware.com/issues/100", "--status-id", "3"],
        )
        assert result.exit_code == 0
        rm.issue.update.assert_called_with(100, status_id=3)
        mock_create.assert_called_with(profile="redminex")


def test_issue_delete_by_url(tmp_path, monkeypatch):
    cf = _config_file(tmp_path, {
        "profiles": {
            "redminex": {"url": "https://redminex.silksoftware.com/", "api_key": "testkey"},
        }
    })
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    monkeypatch.delenv("REDMINE_URL", raising=False)
    monkeypatch.delenv("REDMINE_API_KEY", raising=False)

    with patch("redmine_cli.context.create_redmine") as mock_create:
        rm = MagicMock()
        rm.url = "https://redminex.silksoftware.com/"
        mock_create.return_value = rm

        runner = CliRunner()
        result = runner.invoke(cli, ["issue", "delete", "https://redminex.silksoftware.com/issues/200"])
        assert result.exit_code == 0
        rm.issue.delete.assert_called_with(200)
        mock_create.assert_called_with(profile="redminex")


def test_project_get_by_url(tmp_path, monkeypatch):
    cf = _config_file(tmp_path, {
        "profiles": {
            "redminex": {"url": "https://redminex.silksoftware.com/", "api_key": "testkey"},
        }
    })
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    monkeypatch.delenv("REDMINE_URL", raising=False)
    monkeypatch.delenv("REDMINE_API_KEY", raising=False)

    with patch("redmine_cli.context.create_redmine") as mock_create:
        rm = MagicMock()
        rm.url = "https://redminex.silksoftware.com/"
        rm.project.get.return_value = MagicMock(
            raw=lambda: {"id": 1, "name": "Test Project"}
        )
        mock_create.return_value = rm

        runner = CliRunner()
        result = runner.invoke(cli, ["project", "get", "https://redminex.silksoftware.com/projects/my-proj"])
        assert result.exit_code == 0
        rm.project.get.assert_called_with("my-proj")
        mock_create.assert_called_with(profile="redminex")


def test_explicit_profile_overrides_url(tmp_path, monkeypatch):
    """When -p is given, it should take priority over URL-based resolution."""
    cf = _config_file(tmp_path, {
        "profiles": {
            "redminex": {"url": "https://redminex.silksoftware.com/", "api_key": "key1"},
            "other": {"url": "https://other.test/", "api_key": "key2"},
        }
    })
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    monkeypatch.delenv("REDMINE_URL", raising=False)
    monkeypatch.delenv("REDMINE_API_KEY", raising=False)

    with patch("redmine_cli.context.create_redmine") as mock_create:
        rm = MagicMock()
        rm.url = "https://other.test/"
        rm.issue.get.return_value = MagicMock(raw=lambda: {"id": 1})
        mock_create.return_value = rm

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["-p", "other", "issue", "get", "https://redminex.silksoftware.com/issues/1"],
        )
        assert result.exit_code == 0
        # Should use explicit profile "other", not URL-resolved "redminex"
        mock_create.assert_called_with(profile="other")
