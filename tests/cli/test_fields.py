"""Tests for resource fields discovery commands."""

from unittest.mock import MagicMock

from redmine_cli.main import cli
from tests.cli.conftest import parse_output

# --- Per-resource fields commands (no connection needed) ---


def test_issue_fields(runner):
    """issue fields command works without connection."""
    result = runner.invoke(cli, ["issue", "fields"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["ok"] is True
    assert data["data"]["resource"] == "issue"
    assert "object_fields" in data["data"]
    assert "project" in data["data"]["object_fields"]
    assert "collection_fields" in data["data"]
    assert "includable_fields" in data["data"]
    assert "children" in data["data"]["includable_fields"]


def test_project_fields(runner):
    """project fields command works without connection."""
    result = runner.invoke(cli, ["project", "fields"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["data"]["resource"] == "project"
    assert "object_fields" in data["data"]


def test_user_fields(runner):
    """user fields command works without connection."""
    result = runner.invoke(cli, ["user", "fields"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["data"]["resource"] == "user"
    assert "includable_fields" in data["data"]


def test_time_entry_fields(runner):
    """time-entry fields command works without connection."""
    result = runner.invoke(cli, ["time-entry", "fields"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["data"]["resource"] == "time_entry"
    assert "object_fields" in data["data"]


def test_wiki_page_fields(runner):
    """wiki-page fields command works without connection."""
    result = runner.invoke(cli, ["wiki-page", "fields"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["data"]["resource"] == "wiki_page"


# --- Generic resource fields command ---


def test_resource_fields_issue(runner):
    """resource fields works for issue."""
    result = runner.invoke(cli, ["resource", "fields", "issue"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["data"]["resource"] == "issue"


def test_resource_fields_tracker(runner):
    """resource fields works for resource types without dedicated commands."""
    result = runner.invoke(cli, ["resource", "fields", "tracker"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["data"]["resource"] == "tracker"


def test_resource_fields_wiki_page(runner):
    """resource fields handles multi-word resource names (snake_case)."""
    result = runner.invoke(cli, ["resource", "fields", "wiki_page"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["data"]["resource"] == "wiki_page"


def test_resource_fields_unknown(runner):
    """resource fields fails for unknown resource type."""
    result = runner.invoke(cli, ["resource", "fields", "nonexistent"])
    assert result.exit_code != 0


# --- --fields on get commands ---


def test_issue_get_with_fields(runner, mock_redmine, set_env):
    """issue get --fields filters output to specified fields."""
    mock_redmine.issue.get.return_value = MagicMock(
        raw=lambda: {
            "id": 1,
            "subject": "Test issue",
            "status": {"id": 1, "name": "New"},
            "description": "Long text",
        }
    )
    result = runner.invoke(cli, ["issue", "get", "1", "--fields", "id,subject"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["ok"] is True
    assert data["data"] == {"id": 1, "subject": "Test issue"}
    assert "status" not in data["data"]
    assert "description" not in data["data"]


def test_project_get_with_fields(runner, mock_redmine, set_env):
    """project get --fields filters output."""
    mock_redmine.project.get.return_value = MagicMock(
        raw=lambda: {
            "id": 1,
            "name": "Test Project",
            "identifier": "test",
            "description": "A project",
        }
    )
    result = runner.invoke(cli, ["project", "get", "1", "--fields", "id,name"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["data"] == {"id": 1, "name": "Test Project"}


def test_user_get_with_fields(runner, mock_redmine, set_env):
    """user get --fields filters output."""
    mock_redmine.user.get.return_value = MagicMock(
        raw=lambda: {
            "id": 5,
            "login": "jplang",
            "firstname": "Jean",
            "lastname": "Lang",
            "mail": "jp@example.com",
        }
    )
    result = runner.invoke(cli, ["user", "get", "5", "--fields", "id,login"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["data"] == {"id": 5, "login": "jplang"}


def test_time_entry_get_with_fields(runner, mock_redmine, set_env):
    """time-entry get --fields filters output."""
    mock_redmine.time_entry.get.return_value = MagicMock(
        raw=lambda: {
            "id": 10,
            "hours": 2.5,
            "comments": "dev work",
            "spent_on": "2024-01-15",
        }
    )
    result = runner.invoke(
        cli, ["time-entry", "get", "10", "--fields", "id,hours"]
    )
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["data"] == {"id": 10, "hours": 2.5}


def test_wiki_page_get_with_fields(runner, mock_redmine, set_env):
    """wiki-page get --fields filters output."""
    mock_redmine.wiki_page.get.return_value = MagicMock(
        raw=lambda: {
            "title": "Guide",
            "text": "h1. Guide content",
            "version": 3,
            "updated_on": "2024-01-01",
        }
    )
    result = runner.invoke(
        cli,
        ["wiki-page", "get", "Guide", "--project-id", "1", "--fields", "title,version"],
    )
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["data"] == {"title": "Guide", "version": 3}


def test_resource_get_with_fields(runner, mock_redmine, set_env):
    """resource get --fields filters output."""
    mock_redmine.issue.get.return_value = MagicMock(
        raw=lambda: {"id": 1, "subject": "Test", "status": {"id": 1}, "description": "x"}
    )
    result = runner.invoke(
        cli, ["resource", "get", "issue", "1", "--fields", "id,subject"]
    )
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["data"] == {"id": 1, "subject": "Test"}


def test_issue_get_without_fields_returns_all(runner, mock_redmine, set_env):
    """issue get without --fields returns all fields (backward compat)."""
    full_data = {"id": 1, "subject": "Test", "status": {"id": 1}, "description": "x"}
    mock_redmine.issue.get.return_value = MagicMock(raw=lambda: full_data)
    result = runner.invoke(cli, ["issue", "get", "1"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["data"] == full_data
