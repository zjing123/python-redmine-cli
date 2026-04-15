"""Tests for generic resource CLI commands."""

import json
import pytest
from unittest.mock import MagicMock

from tests.cli.conftest import parse_output


def test_resource_types(runner, mock_redmine, set_env):
    result = runner.invoke(cli, ["resource", "types"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["ok"] is True
    assert "Issue" in data["data"]["resource_types"]
    assert "Project" in data["data"]["resource_types"]
    assert "User" in data["data"]["resource_types"]


def test_resource_get(runner, mock_redmine, set_env):
    mock_redmine.issue.get.return_value = MagicMock(
        raw=lambda: {"id": 1, "subject": "Test"}
    )
    result = runner.invoke(cli, ["resource", "get", "issue", "1"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["data"]["id"] == 1


def test_resource_create(runner, mock_redmine, set_env):
    mock_redmine.issue.create.return_value = MagicMock(
        raw=lambda: {"id": 5, "subject": "Created"}
    )
    result = runner.invoke(
        cli,
        [
            "resource",
            "create",
            "issue",
            "--json",
            '{"project_id": 1, "subject": "Created"}',
        ],
    )
    assert result.exit_code == 0
    mock_redmine.issue.create.assert_called_with(project_id=1, subject="Created")


def test_resource_update(runner, mock_redmine, set_env):
    result = runner.invoke(
        cli, ["resource", "update", "issue", "123", "--json", '{"status_id": 3}']
    )
    assert result.exit_code == 0
    mock_redmine.issue.update.assert_called_with(123, status_id=3)


def test_resource_delete(runner, mock_redmine, set_env):
    result = runner.invoke(cli, ["resource", "delete", "issue", "123"])
    assert result.exit_code == 0
    mock_redmine.issue.delete.assert_called_with(123)


def test_resource_filter(runner, mock_redmine, set_env):
    mock_set = []
    mock_set.total_count = 0
    mock_redmine.issue.filter.return_value = mock_set

    result = runner.invoke(
        cli, ["resource", "filter", "issue", "--json", '{"project_id": 1}']
    )
    assert result.exit_code == 0
    mock_redmine.issue.filter.assert_called_with(project_id=1)


def test_config_show(runner, mock_redmine, set_env):
    result = runner.invoke(cli, ["config", "show"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["ok"] is True
    assert data["data"]["url"] == "https://redmine.test"


def test_config_test(runner, mock_redmine, set_env):
    mock_redmine.auth.return_value = MagicMock(
        raw=lambda: {"id": 1, "login": "admin", "firstname": "Admin"}
    )
    result = runner.invoke(cli, ["config", "test"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["ok"] is True
    assert data["data"]["connected"] is True


def test_search(runner, mock_redmine, set_env):
    mock_redmine.search.return_value = {"issues": [{"id": 1}]}
    result = runner.invoke(cli, ["search", "test query"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["ok"] is True
