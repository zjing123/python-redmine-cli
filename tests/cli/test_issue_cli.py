"""Tests for issue CLI commands."""

from unittest.mock import MagicMock

from redmine_cli.main import cli
from tests.cli.conftest import parse_output


def test_issue_get(runner, mock_redmine, set_env):
    mock_redmine.issue.get.return_value = MagicMock(
        raw=lambda: {
            "id": 1,
            "subject": "Test issue",
            "status": {"id": 1, "name": "New"},
        }
    )
    result = runner.invoke(cli, ["issue", "get", "1"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["ok"] is True
    assert data["data"]["id"] == 1
    assert data["data"]["subject"] == "Test issue"


def test_issue_get_with_includes(runner, mock_redmine, set_env):
    mock_redmine.issue.get.return_value = MagicMock(
        raw=lambda: {"id": 1, "subject": "Test", "journals": []}
    )
    result = runner.invoke(cli, ["issue", "get", "1", "-i", "journals,attachments"])
    assert result.exit_code == 0
    mock_redmine.issue.get.assert_called_with(1, include=["journals", "attachments"])


def _make_mock_set(items):
    """Build a MagicMock ResourceSet-like object from a list of dicts."""
    mock_set = MagicMock()
    mock_set.total_count = len(items)
    mock_objs = [MagicMock(raw=lambda d=d: d) for d in items]
    mock_set.__iter__ = lambda self: iter(mock_objs)
    mock_set.__getitem__ = lambda self, key: mock_objs[key]
    return mock_set


def test_issue_list(runner, mock_redmine, set_env):
    mock_set = _make_mock_set([
        {"id": 1, "subject": "First"},
        {"id": 2, "subject": "Second"},
    ])
    mock_redmine.issue.all.return_value = mock_set
    mock_redmine.issue.filter.return_value = mock_set

    result = runner.invoke(cli, ["issue", "list"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["ok"] is True
    assert data["total_count"] == 2


def test_issue_list_with_filters(runner, mock_redmine, set_env):
    mock_set = MagicMock()
    mock_set.total_count = 0
    mock_set.__iter__ = lambda self: iter([])
    mock_redmine.issue.filter.return_value = mock_set

    result = runner.invoke(
        cli, ["issue", "list", "--project-id", "1", "--status", "open"]
    )
    assert result.exit_code == 0
    mock_redmine.issue.filter.assert_called()
    call_kwargs = mock_redmine.issue.filter.call_args[1]
    assert call_kwargs["project_id"] == 1
    assert call_kwargs["status_id"] == "open"


def test_issue_create_with_json(runner, mock_redmine, set_env):
    mock_redmine.issue.create.return_value = MagicMock(
        raw=lambda: {"id": 2, "subject": "New issue", "project": {"id": 1}}
    )
    result = runner.invoke(
        cli, ["issue", "create", "--json", '{"project_id": 1, "subject": "New issue"}']
    )
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["ok"] is True
    assert data["data"]["subject"] == "New issue"
    mock_redmine.issue.create.assert_called_with(project_id=1, subject="New issue")


def test_issue_create_with_flags(runner, mock_redmine, set_env):
    mock_redmine.issue.create.return_value = MagicMock(
        raw=lambda: {"id": 3, "subject": "Flag issue"}
    )
    result = runner.invoke(
        cli,
        [
            "issue",
            "create",
            "--project-id",
            "1",
            "--subject",
            "Flag issue",
            "--tracker-id",
            "2",
        ],
    )
    assert result.exit_code == 0
    mock_redmine.issue.create.assert_called_with(
        project_id=1, subject="Flag issue", tracker_id=2
    )


def test_issue_update(runner, mock_redmine, set_env):
    result = runner.invoke(
        cli, ["issue", "update", "123", "--status-id", "3", "--notes", "Fixed"]
    )
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["ok"] is True
    assert data["data"]["updated"] is True
    mock_redmine.issue.update.assert_called_with(123, status_id=3, notes="Fixed")


def test_issue_update_with_json(runner, mock_redmine, set_env):
    result = runner.invoke(
        cli, ["issue", "update", "123", "--json", '{"status_id": 3}']
    )
    assert result.exit_code == 0
    mock_redmine.issue.update.assert_called_with(123, status_id=3)


def test_issue_delete(runner, mock_redmine, set_env):
    result = runner.invoke(cli, ["issue", "delete", "123"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["ok"] is True
    assert data["data"]["deleted"] is True
    assert data["data"]["resource"] == "issue"
    assert data["data"]["id"] == 123
    mock_redmine.issue.delete.assert_called_with(123)


def test_issue_not_found(runner, mock_redmine, set_env):
    from redminelib.exceptions import ResourceNotFoundError

    mock_redmine.issue.get.side_effect = ResourceNotFoundError()
    result = runner.invoke(cli, ["issue", "get", "99999"])
    assert result.exit_code == 1
    data = parse_output(result.output)
    assert data["ok"] is False
    assert data["error_type"] == "ResourceNotFoundError"
