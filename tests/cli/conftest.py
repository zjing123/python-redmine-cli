"""Test fixtures for redmine-cli tests."""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_redmine():
    with patch("redmine_cli.context.create_redmine") as mock:
        rm = MagicMock()
        rm.url = "https://redmine.test"
        mock.return_value = rm
        yield rm


@pytest.fixture
def set_env(monkeypatch):
    monkeypatch.setenv("REDMINE_URL", "https://redmine.test")
    monkeypatch.setenv("REDMINE_API_KEY", "testkey123")


def parse_output(output):
    """Parse JSON output from CLI."""
    return json.loads(output)
