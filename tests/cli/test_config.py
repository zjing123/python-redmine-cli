"""Tests for config module."""

import os
import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from redmine_cli.config import load_config, create_redmine, _extract_profile_name
from redmine_cli.main import cli


def parse_output(output):
    import json

    return json.loads(output)


def test_load_config_from_env(monkeypatch):
    monkeypatch.setenv("REDMINE_URL", "https://env.test")
    monkeypatch.setenv("REDMINE_API_KEY", "envkey123")
    config = load_config()
    assert config["url"] == "https://env.test"
    assert config["key"] == "envkey123"


def test_load_config_from_file(monkeypatch, tmp_path):
    config_file = tmp_path / ".redmine-cli.yaml"
    config_file.write_text(
        yaml.dump(
            {
                "default": {
                    "url": "https://file.test",
                    "api_key": "filekey123",
                }
            }
        )
    )
    monkeypatch.setenv("REDMINE_CONFIG", str(config_file))
    monkeypatch.delenv("REDMINE_URL", raising=False)
    monkeypatch.delenv("REDMINE_API_KEY", raising=False)
    config = load_config()
    assert config["url"] == "https://file.test"
    assert config["key"] == "filekey123"


def test_load_config_profile(monkeypatch, tmp_path):
    config_file = tmp_path / ".redmine-cli.yaml"
    config_file.write_text(
        yaml.dump(
            {
                "default": {"url": "https://default.test"},
                "profiles": {
                    "staging": {"url": "https://staging.test", "api_key": "stagingkey"},
                },
            }
        )
    )
    monkeypatch.setenv("REDMINE_CONFIG", str(config_file))
    monkeypatch.delenv("REDMINE_URL", raising=False)
    monkeypatch.delenv("REDMINE_API_KEY", raising=False)
    config = load_config(profile="staging")
    assert config["url"] == "https://staging.test"
    assert config["key"] == "stagingkey"


def test_load_config_env_overrides_file(monkeypatch, tmp_path):
    config_file = tmp_path / ".redmine-cli.yaml"
    config_file.write_text(
        yaml.dump({"default": {"url": "https://file.test", "api_key": "filekey"}})
    )
    monkeypatch.setenv("REDMINE_CONFIG", str(config_file))
    monkeypatch.setenv("REDMINE_URL", "https://env.test")
    monkeypatch.setenv("REDMINE_API_KEY", "envkey")
    config = load_config()
    assert config["url"] == "https://env.test"
    assert config["key"] == "envkey"


def test_create_redmine_missing_url(monkeypatch, tmp_path):
    monkeypatch.setenv("REDMINE_CONFIG", str(tmp_path / "nonexistent.yaml"))
    monkeypatch.delenv("REDMINE_URL", raising=False)
    monkeypatch.delenv("REDMINE_API_KEY", raising=False)
    with pytest.raises(SystemExit):
        create_redmine()


def test_extract_profile_name():
    assert (
        _extract_profile_name("http://redminetest.kettle.net.cn:7777/redmine2/")
        == "redminetest"
    )
    assert _extract_profile_name("https://staging.example.com/") == "staging"


# --- config set / unset CLI tests ---


def _config_file(tmp_path, data=None):
    p = tmp_path / "config.yaml"
    p.write_text(yaml.dump(data or {}))
    return p


def test_config_set_new_profile_with_api_key(tmp_path, monkeypatch):
    cf = _config_file(tmp_path)
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["config", "set", "--url", "https://staging.test", "--api-key", "secret123"],
    )
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["data"]["set"] is True
    assert data["data"]["profile"] == "staging"
    saved = yaml.safe_load(cf.read_text())
    assert "staging" in saved["profiles"]
    assert saved["profiles"]["staging"]["api_key"] == "secret123"


def test_config_set_new_profile_with_username_password(tmp_path, monkeypatch):
    cf = _config_file(tmp_path)
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "config",
            "set",
            "--url",
            "https://staging.test",
            "--username",
            "admin",
            "--password",
            "secret",
        ],
    )
    assert result.exit_code == 0
    saved = yaml.safe_load(cf.read_text())
    assert saved["profiles"]["staging"]["username"] == "admin"
    assert saved["profiles"]["staging"]["password"] == "secret"


def test_config_set_named_profile(tmp_path, monkeypatch):
    cf = _config_file(tmp_path)
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "config",
            "set",
            "--url",
            "https://staging.test",
            "--api-key",
            "secret",
            "-p",
            "myserver",
        ],
    )
    assert result.exit_code == 0
    saved = yaml.safe_load(cf.read_text())
    assert "myserver" in saved["profiles"]


def test_config_set_api_key_and_username_mutually_exclusive(tmp_path, monkeypatch):
    cf = _config_file(tmp_path)
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "config",
            "set",
            "--url",
            "https://staging.test",
            "--api-key",
            "k",
            "--username",
            "admin",
        ],
    )
    assert result.exit_code != 0


def test_config_set_username_requires_password(tmp_path, monkeypatch):
    cf = _config_file(tmp_path)
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    runner = CliRunner()
    result = runner.invoke(
        cli, ["config", "set", "--url", "https://staging.test", "--username", "admin"]
    )
    assert result.exit_code != 0


def test_config_set_url_required_for_new(tmp_path, monkeypatch):
    cf = _config_file(tmp_path)
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "set", "--api-key", "secret"])
    assert result.exit_code != 0


def test_config_set_rejects_existing_profile(tmp_path, monkeypatch):
    initial = {
        "profiles": {"staging": {"url": "https://old.test", "api_key": "oldkey"}}
    }
    cf = _config_file(tmp_path, initial)
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "config",
            "set",
            "--url",
            "https://new.test",
            "--api-key",
            "k",
            "-p",
            "staging",
        ],
    )
    assert result.exit_code != 0


def test_config_update_existing_profile(tmp_path, monkeypatch):
    initial = {
        "profiles": {"staging": {"url": "https://old.test", "api_key": "oldkey"}}
    }
    cf = _config_file(tmp_path, initial)
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    runner = CliRunner()
    result = runner.invoke(
        cli, ["config", "update", "--api-key", "newkey", "-p", "staging"]
    )
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["data"]["updated"] is True
    saved = yaml.safe_load(cf.read_text())
    assert saved["profiles"]["staging"]["api_key"] == "newkey"
    assert saved["profiles"]["staging"]["url"] == "https://old.test"


def test_config_update_switch_to_username(tmp_path, monkeypatch):
    initial = {
        "profiles": {"staging": {"url": "https://staging.test", "api_key": "oldkey"}}
    }
    cf = _config_file(tmp_path, initial)
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "config",
            "update",
            "--username",
            "admin",
            "--password",
            "secret",
            "-p",
            "staging",
        ],
    )
    assert result.exit_code == 0
    saved = yaml.safe_load(cf.read_text())
    assert saved["profiles"]["staging"]["username"] == "admin"
    assert saved["profiles"]["staging"]["password"] == "secret"
    assert "api_key" not in saved["profiles"]["staging"]


def test_config_update_nonexistent_profile(tmp_path, monkeypatch):
    cf = _config_file(tmp_path, {"profiles": {}})
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    runner = CliRunner()
    result = runner.invoke(
        cli, ["config", "update", "--api-key", "secret", "-p", "nope"]
    )
    assert result.exit_code != 0


def test_config_list_shows_all_profiles_as_table(tmp_path, monkeypatch):
    initial = {
        "default": {"url": "https://default.test", "api_key": "defaultkey"},
        "profiles": {
            "staging": {"url": "https://staging.test", "api_key": "stagingkey"},
            "prod": {
                "url": "https://prod.test",
                "username": "admin",
                "password": "secret",
            },
        },
    }
    cf = _config_file(tmp_path, initial)
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "list"])
    assert result.exit_code == 0
    assert "PROFILE" in result.output
    assert "default" in result.output
    assert "staging" in result.output
    assert "prod" in result.output
    assert "****gkey" in result.output
    assert "stagingkey" not in result.output
    assert "secret" not in result.output


def test_config_list_json(tmp_path, monkeypatch):
    initial = {
        "profiles": {
            "staging": {"url": "https://staging.test", "api_key": "stagingkey"},
            "prod": {
                "url": "https://prod.test",
                "username": "admin",
                "password": "secret",
            },
        }
    }
    cf = _config_file(tmp_path, initial)
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "list", "--json"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["ok"] is True
    assert data["data"]["profiles"] == [
        {
            "profile": "prod",
            "url": "https://prod.test",
            "auth": "password",
            "api_key": "",
            "username": "admin",
            "password": "****cret",
        },
        {
            "profile": "staging",
            "url": "https://staging.test",
            "auth": "api_key",
            "api_key": "****gkey",
            "username": "",
            "password": "",
        },
    ]


def test_config_list_json_specific_profile(tmp_path, monkeypatch):
    initial = {
        "profiles": {
            "staging": {"url": "https://staging.test", "api_key": "stagingkey"},
            "prod": {"url": "https://prod.test", "api_key": "prodkey"},
        }
    }
    cf = _config_file(tmp_path, initial)
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "list", "-p", "prod", "--json"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["data"]["profiles"] == [
        {
            "profile": "prod",
            "url": "https://prod.test",
            "auth": "api_key",
            "api_key": "****dkey",
            "username": "",
            "password": "",
        }
    ]


def test_config_list_json_default_profile(tmp_path, monkeypatch):
    initial = {
        "default": {"url": "https://default.test", "api_key": "defaultkey"},
        "profiles": {
            "prod": {"url": "https://prod.test", "api_key": "prodkey"},
        },
    }
    cf = _config_file(tmp_path, initial)
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "list", "-p", "default", "--json"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["data"]["profiles"] == [
        {
            "profile": "default",
            "url": "https://default.test",
            "auth": "api_key",
            "api_key": "****tkey",
            "username": "",
            "password": "",
        }
    ]


def test_config_unset_profile(tmp_path, monkeypatch):
    initial = {
        "profiles": {
            "staging": {"url": "https://staging.test", "api_key": "key"},
            "prod": {"url": "https://prod.test"},
        }
    }
    cf = _config_file(tmp_path, initial)
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "unset", "-p", "staging"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["data"]["unset"] is True
    assert data["data"]["profile"] == "staging"
    saved = yaml.safe_load(cf.read_text())
    assert "staging" not in saved["profiles"]
    assert "prod" in saved["profiles"]


def test_config_unset_nonexistent_profile(tmp_path, monkeypatch):
    cf = _config_file(tmp_path, {"profiles": {}})
    monkeypatch.setenv("REDMINE_CONFIG", str(cf))
    runner = CliRunner()
    result = runner.invoke(cli, ["config", "unset", "-p", "nope"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["data"]["unset"] is False
