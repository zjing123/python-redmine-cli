"""Tests for config module."""

import os
import pytest
import tempfile
import yaml
from pathlib import Path

from redmine_cli.config import load_config, create_redmine


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
