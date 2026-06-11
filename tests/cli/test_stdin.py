"""Tests for --stdin pipe mode across all resource commands."""

import json
import pytest
from unittest.mock import MagicMock

from redmine_cli.main import cli
from tests.cli.conftest import parse_output


# ---------------------------------------------------------------------------
# Issue commands (Pattern A: optional --json with flag fallback)
# ---------------------------------------------------------------------------


def test_issue_create_with_stdin(runner, mock_redmine, set_env):
    mock_redmine.issue.create.return_value = MagicMock(
        raw=lambda: {"id": 2, "subject": "Stdin issue", "project": {"id": 1}}
    )
    result = runner.invoke(
        cli,
        ["issue", "create", "--stdin"],
        input='{"project_id": 1, "subject": "Stdin issue"}',
    )
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["ok"] is True
    assert data["data"]["subject"] == "Stdin issue"
    mock_redmine.issue.create.assert_called_with(project_id=1, subject="Stdin issue")


def test_issue_update_with_stdin(runner, mock_redmine, set_env):
    result = runner.invoke(
        cli,
        ["issue", "update", "123", "--stdin"],
        input='{"status_id": 3, "notes": "Fixed via stdin"}',
    )
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["ok"] is True
    assert data["data"]["updated"] is True
    mock_redmine.issue.update.assert_called_with(
        123, status_id=3, notes="Fixed via stdin"
    )


def test_issue_create_json_and_stdin_exclusive(runner, mock_redmine, set_env):
    result = runner.invoke(
        cli,
        ["issue", "create", "--json", '{"a": 1}', "--stdin"],
        input='{"b": 2}',
    )
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output


def test_issue_create_stdin_empty(runner, mock_redmine, set_env):
    result = runner.invoke(
        cli,
        ["issue", "create", "--stdin"],
        input="",
    )
    assert result.exit_code != 0
    assert "No data received on stdin" in result.output


def test_issue_create_stdin_invalid_json(runner, mock_redmine, set_env):
    result = runner.invoke(
        cli,
        ["issue", "create", "--stdin"],
        input="not valid json",
    )
    assert result.exit_code != 0


def test_issue_create_stdin_dry_run(runner, mock_redmine, set_env):
    result = runner.invoke(
        cli,
        ["--dry-run", "issue", "create", "--stdin"],
        input='{"project_id": 1, "subject": "Dry run"}',
    )
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["ok"] is True
    assert data["data"]["dry_run"] is True
    assert data["data"]["payload"]["project_id"] == 1
    mock_redmine.issue.create.assert_not_called()


# ---------------------------------------------------------------------------
# Project commands
# ---------------------------------------------------------------------------


def test_project_create_with_stdin(runner, mock_redmine, set_env):
    mock_redmine.project.create.return_value = MagicMock(
        raw=lambda: {"id": 1, "name": "Stdin Project", "identifier": "stdin-proj"}
    )
    result = runner.invoke(
        cli,
        ["project", "create", "--stdin"],
        input='{"name": "Stdin Project", "identifier": "stdin-proj"}',
    )
    assert result.exit_code == 0
    mock_redmine.project.create.assert_called_with(
        name="Stdin Project", identifier="stdin-proj"
    )


def test_project_update_with_stdin(runner, mock_redmine, set_env):
    result = runner.invoke(
        cli,
        ["project", "update", "test-proj", "--stdin"],
        input='{"name": "Updated Name"}',
    )
    assert result.exit_code == 0
    mock_redmine.project.update.assert_called_with("test-proj", name="Updated Name")


# ---------------------------------------------------------------------------
# User commands
# ---------------------------------------------------------------------------


def test_user_create_with_stdin(runner, mock_redmine, set_env):
    mock_redmine.user.create.return_value = MagicMock(
        raw=lambda: {"id": 5, "login": "stdinuser"}
    )
    result = runner.invoke(
        cli,
        ["user", "create", "--stdin"],
        input='{"login": "stdinuser", "firstname": "Std", "lastname": "User"}',
    )
    assert result.exit_code == 0
    mock_redmine.user.create.assert_called_with(
        login="stdinuser", firstname="Std", lastname="User"
    )


def test_user_update_with_stdin(runner, mock_redmine, set_env):
    result = runner.invoke(
        cli,
        ["user", "update", "5", "--stdin"],
        input='{"firstname": "NewFirst"}',
    )
    assert result.exit_code == 0
    mock_redmine.user.update.assert_called_with(5, firstname="NewFirst")


# ---------------------------------------------------------------------------
# Time entry commands
# ---------------------------------------------------------------------------


def test_time_entry_create_with_stdin(runner, mock_redmine, set_env):
    mock_redmine.time_entry.create.return_value = MagicMock(
        raw=lambda: {"id": 10, "hours": 2.5}
    )
    result = runner.invoke(
        cli,
        ["time-entry", "create", "--stdin"],
        input='{"issue_id": 123, "hours": 2.5}',
    )
    assert result.exit_code == 0
    mock_redmine.time_entry.create.assert_called_with(issue_id=123, hours=2.5)


def test_time_entry_update_with_stdin(runner, mock_redmine, set_env):
    result = runner.invoke(
        cli,
        ["time-entry", "update", "10", "--stdin"],
        input='{"hours": 3.0}',
    )
    assert result.exit_code == 0
    mock_redmine.time_entry.update.assert_called_with(10, hours=3.0)


# ---------------------------------------------------------------------------
# Wiki page commands
# ---------------------------------------------------------------------------


def test_wiki_page_create_with_stdin(runner, mock_redmine, set_env):
    mock_redmine.wiki_page.create.return_value = MagicMock(
        raw=lambda: {"title": "StdinPage", "version": 1}
    )
    result = runner.invoke(
        cli,
        ["wiki-page", "create", "StdinPage", "--project-id", "1", "--stdin"],
        input='{"text": "Hello from stdin"}',
    )
    assert result.exit_code == 0
    mock_redmine.wiki_page.create.assert_called_with(
        title="StdinPage", project_id=1, text="Hello from stdin"
    )


def test_wiki_page_update_with_stdin(runner, mock_redmine, set_env):
    result = runner.invoke(
        cli,
        ["wiki-page", "update", "MyPage", "--project-id", "1", "--stdin"],
        input='{"text": "Updated content"}',
    )
    assert result.exit_code == 0
    mock_redmine.wiki_page.update.assert_called_with(
        "MyPage", project_id=1, text="Updated content"
    )


# ---------------------------------------------------------------------------
# Generic resource commands (Pattern B: --json was required, now --stdin alternative)
# ---------------------------------------------------------------------------


def test_resource_create_with_stdin(runner, mock_redmine, set_env):
    mock_redmine.issue.create.return_value = MagicMock(
        raw=lambda: {"id": 99, "subject": "Via generic stdin"}
    )
    result = runner.invoke(
        cli,
        ["resource", "create", "issue", "--stdin"],
        input='{"project_id": 1, "subject": "Via generic stdin"}',
    )
    assert result.exit_code == 0
    mock_redmine.issue.create.assert_called_with(
        project_id=1, subject="Via generic stdin"
    )


def test_resource_update_with_stdin(runner, mock_redmine, set_env):
    result = runner.invoke(
        cli,
        ["resource", "update", "issue", "123", "--stdin"],
        input='{"status_id": 5}',
    )
    assert result.exit_code == 0
    mock_redmine.issue.update.assert_called_with(123, status_id=5)


def test_resource_filter_with_stdin(runner, mock_redmine, set_env):
    mock_set = MagicMock()
    mock_set.total_count = 1
    mock_set.__iter__ = lambda self: iter(
        [MagicMock(raw=lambda: {"id": 1, "subject": "Filtered"})]
    )
    mock_redmine.issue.filter.return_value = mock_set

    result = runner.invoke(
        cli,
        ["resource", "filter", "issue", "--stdin"],
        input='{"project_id": 1}',
    )
    assert result.exit_code == 0
    mock_redmine.issue.filter.assert_called_with(project_id=1)


def test_resource_create_no_json_no_stdin(runner, mock_redmine, set_env):
    """Pattern B: neither --json nor --stdin should error."""
    result = runner.invoke(
        cli,
        ["resource", "create", "issue"],
    )
    assert result.exit_code != 0
    assert "Either --json or --stdin is required" in result.output


def test_resource_create_json_and_stdin_exclusive(runner, mock_redmine, set_env):
    """Pattern B: --json and --stdin together should error."""
    result = runner.invoke(
        cli,
        ["resource", "create", "issue", "--json", '{"a": 1}', "--stdin"],
        input='{"b": 2}',
    )
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output
