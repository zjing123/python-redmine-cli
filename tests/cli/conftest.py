"""Test fixtures for redmine-cli tests."""

import json
import pytest
from click.testing import CliRunner
from unittest.mock import MagicMock, patch

from redmine_cli.main import cli


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
