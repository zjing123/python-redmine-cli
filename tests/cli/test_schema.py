"""Tests for resource schema discovery commands."""

from unittest.mock import MagicMock

from redmine_cli.main import cli
from tests.cli.conftest import parse_output


# --- Per-resource schema commands (no connection needed) ---


def test_issue_schema(runner):
    """issue schema returns creation schema without connection."""
    result = runner.invoke(cli, ["issue", "schema"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["ok"] is True
    d = data["data"]
    assert d["resource"] == "issue"
    assert d["creatable"] is True
    assert d["updatable"] is True
    assert "project_id" in d["required_url_params"]
    assert "project_id" in d["required_fields"]
    assert "subject" in d["required_fields"]
    assert "tracker_id" in d["optional_fields"]
    assert "id" in d["create_readonly"]
    assert "tracker_id" in d["id_fields"]
    assert "project" in d["related_objects"]


def test_project_schema(runner):
    """project schema returns creation schema without connection."""
    result = runner.invoke(cli, ["project", "schema"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    d = data["data"]
    assert d["resource"] == "project"
    assert d["creatable"] is True
    assert d["required_url_params"] == []
    assert "name" in d["required_fields"]
    assert "identifier" in d["required_fields"]
    assert "description" in d["optional_fields"]


def test_user_schema(runner):
    """user schema returns creation schema without connection."""
    result = runner.invoke(cli, ["user", "schema"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    d = data["data"]
    assert d["resource"] == "user"
    assert d["creatable"] is True
    assert "login" in d["required_fields"]
    assert "mail" in d["required_fields"]
    assert "api_key" in d["create_readonly"]


def test_time_entry_schema(runner):
    """time-entry schema returns creation schema without connection."""
    result = runner.invoke(cli, ["time-entry", "schema"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    d = data["data"]
    assert d["resource"] == "time_entry"
    assert d["creatable"] is True
    assert "issue_id" in d["required_fields"]
    assert "hours" in d["required_fields"]


def test_wiki_page_schema(runner):
    """wiki-page schema returns creation schema without connection."""
    result = runner.invoke(cli, ["wiki-page", "schema"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    d = data["data"]
    assert d["resource"] == "wiki_page"
    assert d["creatable"] is True
    assert "project_id" in d["required_url_params"]
    assert "title" in d["required_url_params"]
    assert "title" in d["required_fields"]
    assert "text" in d["required_fields"]


# --- Generic resource schema command ---


def test_resource_schema_issue(runner):
    """resource schema works for issue."""
    result = runner.invoke(cli, ["resource", "schema", "issue"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["data"]["resource"] == "issue"
    assert data["data"]["creatable"] is True


def test_resource_schema_project(runner):
    """resource schema works for project."""
    result = runner.invoke(cli, ["resource", "schema", "project"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["data"]["resource"] == "project"


def test_resource_schema_tracker_readonly(runner):
    """resource schema shows tracker as not creatable."""
    result = runner.invoke(cli, ["resource", "schema", "tracker"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    d = data["data"]
    assert d["resource"] == "tracker"
    assert d["creatable"] is False
    assert d["required_fields"] == []
    assert d["optional_fields"] == []


def test_resource_schema_version(runner):
    """resource schema works for version with required URL param."""
    result = runner.invoke(cli, ["resource", "schema", "version"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    d = data["data"]
    assert d["resource"] == "version"
    assert d["creatable"] is True
    assert "project_id" in d["required_url_params"]
    assert "name" in d["required_fields"]


def test_resource_schema_unknown(runner):
    """resource schema fails for unknown resource type."""
    result = runner.invoke(cli, ["resource", "schema", "nonexistent"])
    assert result.exit_code != 0


def test_resource_schema_wiki_page(runner):
    """resource schema handles multi-word resource names."""
    result = runner.invoke(cli, ["resource", "schema", "wiki_page"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert data["data"]["resource"] == "wiki_page"


# --- --live flag tests ---


def test_issue_schema_live(runner, mock_redmine, set_env):
    """issue schema --live fetches trackers, statuses, priorities."""
    mock_tracker = MagicMock(raw=lambda: {"id": 1, "name": "Bug"})
    mock_status = MagicMock(raw=lambda: {"id": 1, "name": "New"})
    mock_priority = MagicMock(raw=lambda: {"id": 2, "name": "Normal"})

    mock_redmine.tracker.all.return_value = [mock_tracker]
    mock_redmine.issue_status.all.return_value = [mock_status]
    mock_redmine.enumeration.filter.return_value = [mock_priority]

    result = runner.invoke(cli, ["issue", "schema", "--live"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    d = data["data"]
    assert d["resource"] == "issue"
    assert "enums" in d
    assert "trackers" in d["enums"]
    assert "statuses" in d["enums"]
    assert "priorities" in d["enums"]
    assert d["enums"]["trackers"][0]["name"] == "Bug"
    assert d["enums"]["statuses"][0]["name"] == "New"
    assert d["enums"]["priorities"][0]["name"] == "Normal"


def test_project_schema_live(runner, mock_redmine, set_env):
    """project schema --live fetches trackers."""
    mock_tracker = MagicMock(raw=lambda: {"id": 1, "name": "Bug"})
    mock_redmine.tracker.all.return_value = [mock_tracker]

    result = runner.invoke(cli, ["project", "schema", "--live"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert "enums" in data["data"]
    assert "trackers" in data["data"]["enums"]


def test_time_entry_schema_live(runner, mock_redmine, set_env):
    """time-entry schema --live fetches activities."""
    mock_activity = MagicMock(raw=lambda: {"id": 8, "name": "Development"})
    mock_redmine.enumeration.filter.return_value = [mock_activity]

    result = runner.invoke(cli, ["time-entry", "schema", "--live"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert "enums" in data["data"]
    assert "activities" in data["data"]["enums"]
    assert data["data"]["enums"]["activities"][0]["name"] == "Development"


def test_resource_schema_live(runner, mock_redmine, set_env):
    """resource schema --live works for issue via generic command."""
    mock_tracker = MagicMock(raw=lambda: {"id": 1, "name": "Bug"})
    mock_redmine.tracker.all.return_value = [mock_tracker]
    mock_redmine.issue_status.all.return_value = []
    mock_redmine.enumeration.filter.return_value = []

    result = runner.invoke(cli, ["resource", "schema", "issue", "--live"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert "enums" in data["data"]
    assert "trackers" in data["data"]["enums"]


def test_schema_live_handles_api_failure(runner, mock_redmine, set_env):
    """schema --live gracefully handles API errors."""
    mock_redmine.tracker.all.side_effect = Exception("API error")
    mock_redmine.issue_status.all.side_effect = Exception("API error")
    mock_redmine.enumeration.filter.side_effect = Exception("API error")

    result = runner.invoke(cli, ["issue", "schema", "--live"])
    assert result.exit_code == 0
    data = parse_output(result.output)
    assert "enums" in data["data"]
    # Failed enums should be empty lists, not errors
    assert data["data"]["enums"]["trackers"] == []
    assert data["data"]["enums"]["statuses"] == []
    assert data["data"]["enums"]["priorities"] == []
