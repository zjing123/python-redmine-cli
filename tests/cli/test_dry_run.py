"""Tests for --dry-run mode across all mutation commands."""

import json
import pytest
from unittest.mock import MagicMock, call

from redmine_cli.main import cli
from tests.cli.conftest import parse_output


# ---------------------------------------------------------------------------
# Issue dry-run tests
# ---------------------------------------------------------------------------


class TestIssueDryRun:
    """Dry-run tests for issue mutation commands."""

    def test_issue_create_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(
            cli,
            [
                "--dry-run",
                "issue",
                "create",
                "--project-id",
                "1",
                "--subject",
                "Bug report",
            ],
        )
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["ok"] is True
        assert data["dry_run"] is True
        assert data["data"]["operation"] == "create"
        assert data["data"]["resource_type"] == "issue"
        assert data["data"]["method"] == "POST"
        assert "/issues.json" in data["data"]["url"]
        assert data["data"]["payload"]["project_id"] == 1
        assert data["data"]["payload"]["subject"] == "Bug report"
        # No actual API call made
        mock_redmine.issue.create.assert_not_called()

    def test_issue_create_dry_run_with_json(self, runner, mock_redmine, set_env):
        result = runner.invoke(
            cli,
            [
                "--dry-run",
                "issue",
                "create",
                "--json",
                '{"project_id": 1, "subject": "JSON issue"}',
            ],
        )
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["dry_run"] is True
        assert data["data"]["payload"]["project_id"] == 1
        assert data["data"]["payload"]["subject"] == "JSON issue"
        mock_redmine.issue.create.assert_not_called()

    def test_issue_update_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(
            cli,
            ["--dry-run", "issue", "update", "123", "--status-id", "3", "--notes", "Fixed"],
        )
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["dry_run"] is True
        assert data["data"]["operation"] == "update"
        assert data["data"]["method"] == "PUT"
        assert "/issues/123.json" in data["data"]["url"]
        assert data["data"]["payload"]["status_id"] == 3
        assert data["data"]["payload"]["notes"] == "Fixed"
        mock_redmine.issue.update.assert_not_called()

    def test_issue_delete_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(cli, ["--dry-run", "issue", "delete", "456"])
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["dry_run"] is True
        assert data["data"]["operation"] == "delete"
        assert data["data"]["method"] == "DELETE"
        assert "/issues/456.json" in data["data"]["url"]
        assert "payload" not in data["data"]
        mock_redmine.issue.delete.assert_not_called()

    def test_issue_add_watcher_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(
            cli, ["--dry-run", "issue", "add-watcher", "123", "--user-id", "5"]
        )
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["dry_run"] is True
        assert data["data"]["operation"] == "add_watcher"
        assert data["data"]["method"] == "POST"
        assert "/issues/123/watchers.json" in data["data"]["url"]
        assert data["data"]["payload"]["user_id"] == 5
        # Should not call issue.get() either
        mock_redmine.issue.get.assert_not_called()

    def test_issue_remove_watcher_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(
            cli, ["--dry-run", "issue", "remove-watcher", "123", "--user-id", "5"]
        )
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["dry_run"] is True
        assert data["data"]["operation"] == "remove_watcher"
        assert data["data"]["method"] == "DELETE"
        assert "/issues/123/watchers/5.json" in data["data"]["url"]
        mock_redmine.issue.get.assert_not_called()

    def test_issue_copy_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(
            cli,
            [
                "--dry-run",
                "issue",
                "copy",
                "123",
                "--project-id",
                "2",
                "--no-link-original",
                "--include",
                "subtasks",
            ],
        )
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["dry_run"] is True
        assert data["data"]["operation"] == "copy"
        assert data["data"]["method"] == "POST"
        assert data["data"]["payload"]["copy_from"] == 123
        assert data["data"]["payload"]["project_id"] == 2
        mock_redmine.issue.get.assert_not_called()


# ---------------------------------------------------------------------------
# Project dry-run tests
# ---------------------------------------------------------------------------


class TestProjectDryRun:
    """Dry-run tests for project mutation commands."""

    def test_project_create_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(
            cli,
            [
                "--dry-run",
                "project",
                "create",
                "--name",
                "Test Project",
                "--identifier",
                "test-proj",
            ],
        )
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["dry_run"] is True
        assert data["data"]["operation"] == "create"
        assert data["data"]["resource_type"] == "project"
        assert data["data"]["method"] == "POST"
        assert "/projects.json" in data["data"]["url"]
        assert data["data"]["payload"]["name"] == "Test Project"
        assert data["data"]["payload"]["identifier"] == "test-proj"
        mock_redmine.project.create.assert_not_called()

    def test_project_update_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(
            cli, ["--dry-run", "project", "update", "my-proj", "--name", "New Name"]
        )
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["dry_run"] is True
        assert data["data"]["operation"] == "update"
        assert data["data"]["method"] == "PUT"
        assert "/projects/my-proj.json" in data["data"]["url"]
        assert data["data"]["payload"]["name"] == "New Name"
        mock_redmine.project.update.assert_not_called()

    def test_project_delete_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(cli, ["--dry-run", "project", "delete", "my-proj"])
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["dry_run"] is True
        assert data["data"]["operation"] == "delete"
        assert "/projects/my-proj.json" in data["data"]["url"]
        mock_redmine.project.delete.assert_not_called()

    def test_project_close_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(cli, ["--dry-run", "project", "close", "my-proj"])
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["dry_run"] is True
        assert data["data"]["operation"] == "close"
        assert data["data"]["method"] == "PUT"
        assert "/projects/my-proj/close.json" in data["data"]["url"]
        mock_redmine.project.close.assert_not_called()

    def test_project_reopen_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(cli, ["--dry-run", "project", "reopen", "my-proj"])
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["data"]["operation"] == "reopen"
        assert "/projects/my-proj/reopen.json" in data["data"]["url"]

    def test_project_archive_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(cli, ["--dry-run", "project", "archive", "my-proj"])
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["data"]["operation"] == "archive"
        assert "/projects/my-proj/archive.json" in data["data"]["url"]

    def test_project_unarchive_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(cli, ["--dry-run", "project", "unarchive", "my-proj"])
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["data"]["operation"] == "unarchive"
        assert "/projects/my-proj/unarchive.json" in data["data"]["url"]


# ---------------------------------------------------------------------------
# User dry-run tests
# ---------------------------------------------------------------------------


class TestUserDryRun:
    """Dry-run tests for user mutation commands."""

    def test_user_create_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(
            cli,
            [
                "--dry-run",
                "user",
                "create",
                "--login",
                "testuser",
                "--firstname",
                "Test",
                "--lastname",
                "User",
                "--mail",
                "test@example.com",
            ],
        )
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["dry_run"] is True
        assert data["data"]["resource_type"] == "user"
        assert data["data"]["method"] == "POST"
        assert "/users.json" in data["data"]["url"]
        assert data["data"]["payload"]["login"] == "testuser"
        mock_redmine.user.create.assert_not_called()

    def test_user_update_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(
            cli, ["--dry-run", "user", "update", "5", "--firstname", "NewName"]
        )
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["dry_run"] is True
        assert data["data"]["operation"] == "update"
        assert "/users/5.json" in data["data"]["url"]
        assert data["data"]["payload"]["firstname"] == "NewName"
        mock_redmine.user.update.assert_not_called()

    def test_user_delete_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(cli, ["--dry-run", "user", "delete", "5"])
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["dry_run"] is True
        assert data["data"]["operation"] == "delete"
        assert "/users/5.json" in data["data"]["url"]
        mock_redmine.user.delete.assert_not_called()


# ---------------------------------------------------------------------------
# Time entry dry-run tests
# ---------------------------------------------------------------------------


class TestTimeEntryDryRun:
    """Dry-run tests for time entry mutation commands."""

    def test_time_entry_create_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(
            cli,
            [
                "--dry-run",
                "time-entry",
                "create",
                "--issue-id",
                "123",
                "--hours",
                "2.5",
                "--activity-id",
                "1",
            ],
        )
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["dry_run"] is True
        assert data["data"]["resource_type"] == "time_entry"
        assert data["data"]["method"] == "POST"
        assert "/time_entries.json" in data["data"]["url"]
        assert data["data"]["payload"]["issue_id"] == 123
        assert data["data"]["payload"]["hours"] == 2.5
        mock_redmine.time_entry.create.assert_not_called()

    def test_time_entry_update_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(
            cli, ["--dry-run", "time-entry", "update", "456", "--hours", "3.0"]
        )
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["dry_run"] is True
        assert data["data"]["operation"] == "update"
        assert "/time_entries/456.json" in data["data"]["url"]
        assert data["data"]["payload"]["hours"] == 3.0
        mock_redmine.time_entry.update.assert_not_called()

    def test_time_entry_delete_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(cli, ["--dry-run", "time-entry", "delete", "456"])
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["dry_run"] is True
        assert data["data"]["operation"] == "delete"
        assert "/time_entries/456.json" in data["data"]["url"]
        mock_redmine.time_entry.delete.assert_not_called()


# ---------------------------------------------------------------------------
# Wiki page dry-run tests
# ---------------------------------------------------------------------------


class TestWikiPageDryRun:
    """Dry-run tests for wiki page mutation commands."""

    def test_wiki_page_create_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(
            cli,
            [
                "--dry-run",
                "wiki-page",
                "create",
                "TestPage",
                "--project-id",
                "1",
                "--text",
                "Hello world",
            ],
        )
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["dry_run"] is True
        assert data["data"]["resource_type"] == "wiki_page"
        assert data["data"]["method"] == "POST"
        assert "/projects/1/wiki/TestPage.json" in data["data"]["url"]
        assert data["data"]["payload"]["text"] == "Hello world"
        mock_redmine.wiki_page.create.assert_not_called()

    def test_wiki_page_update_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(
            cli,
            [
                "--dry-run",
                "wiki-page",
                "update",
                "TestPage",
                "--project-id",
                "1",
                "--text",
                "Updated content",
            ],
        )
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["dry_run"] is True
        assert data["data"]["operation"] == "update"
        assert "/projects/1/wiki/TestPage.json" in data["data"]["url"]
        assert data["data"]["payload"]["text"] == "Updated content"
        mock_redmine.wiki_page.update.assert_not_called()

    def test_wiki_page_delete_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(
            cli, ["--dry-run", "wiki-page", "delete", "TestPage", "--project-id", "1"]
        )
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["dry_run"] is True
        assert data["data"]["operation"] == "delete"
        assert "/projects/1/wiki/TestPage.json" in data["data"]["url"]
        mock_redmine.wiki_page.delete.assert_not_called()


# ---------------------------------------------------------------------------
# Generic resource dry-run tests
# ---------------------------------------------------------------------------


class TestGenericDryRun:
    """Dry-run tests for generic resource mutation commands."""

    def test_generic_create_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(
            cli,
            [
                "--dry-run",
                "resource",
                "create",
                "issue",
                "--json",
                '{"project_id": 1, "subject": "Via generic"}',
            ],
        )
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["dry_run"] is True
        assert data["data"]["resource_type"] == "issue"
        assert data["data"]["method"] == "POST"
        assert data["data"]["payload"]["subject"] == "Via generic"
        mock_redmine.issue.create.assert_not_called()

    def test_generic_update_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(
            cli,
            [
                "--dry-run",
                "resource",
                "update",
                "issue",
                "123",
                "--json",
                '{"status_id": 3}',
            ],
        )
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["dry_run"] is True
        assert data["data"]["operation"] == "update"
        assert data["data"]["payload"]["status_id"] == 3
        mock_redmine.issue.update.assert_not_called()

    def test_generic_delete_dry_run(self, runner, mock_redmine, set_env):
        result = runner.invoke(
            cli, ["--dry-run", "resource", "delete", "issue", "123"]
        )
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["dry_run"] is True
        assert data["data"]["operation"] == "delete"
        mock_redmine.issue.delete.assert_not_called()


# ---------------------------------------------------------------------------
# Non-mutation commands ignore dry-run
# ---------------------------------------------------------------------------


class TestDryRunIgnored:
    """Non-mutation commands should ignore --dry-run and work normally."""

    def test_issue_get_with_dry_run(self, runner, mock_redmine, set_env):
        mock_redmine.issue.get.return_value = MagicMock(
            raw=lambda: {"id": 1, "subject": "Test"}
        )
        result = runner.invoke(cli, ["--dry-run", "issue", "get", "1"])
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["ok"] is True
        assert "dry_run" not in data
        mock_redmine.issue.get.assert_called_once()

    def test_issue_list_with_dry_run(self, runner, mock_redmine, set_env):
        mock_set = MagicMock()
        mock_set.total_count = 1
        mock_set.__iter__ = lambda self: iter(
            [MagicMock(raw=lambda: {"id": 1, "subject": "Test"})]
        )
        mock_redmine.issue.all.return_value = mock_set
        result = runner.invoke(cli, ["--dry-run", "issue", "list"])
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["ok"] is True
        assert "dry_run" not in data
        mock_redmine.issue.all.assert_called_once()


# ---------------------------------------------------------------------------
# Validation still runs in dry-run mode
# ---------------------------------------------------------------------------


class TestDryRunValidation:
    """Parameter validation should still catch errors in dry-run mode."""

    def test_issue_create_dry_run_invalid_json(self, runner, mock_redmine, set_env):
        result = runner.invoke(
            cli, ["--dry-run", "issue", "create", "--json", "not-valid-json"]
        )
        assert result.exit_code != 0

    def test_generic_create_dry_run_invalid_json(self, runner, mock_redmine, set_env):
        result = runner.invoke(
            cli,
            ["--dry-run", "resource", "create", "issue", "--json", "bad json"],
        )
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# Dry-run sensitive data masking
# ---------------------------------------------------------------------------


class TestDryRunSensitiveMasking:
    """Sensitive fields must be masked in dry-run output."""

    def test_user_create_dry_run_masks_password(self, runner, mock_redmine, set_env):
        result = runner.invoke(
            cli,
            [
                "--dry-run",
                "user",
                "create",
                "--login",
                "testuser",
                "--firstname",
                "Test",
                "--lastname",
                "User",
                "--mail",
                "test@example.com",
                "--password",
                "supersecret123",
            ],
        )
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["data"]["payload"]["password"] == "****"
        assert "supersecret123" not in result.output

    def test_user_update_dry_run_masks_password(self, runner, mock_redmine, set_env):
        result = runner.invoke(
            cli,
            ["--dry-run", "user", "update", "5", "--password", "mysecret"],
        )
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["data"]["payload"]["password"] == "****"
        assert "mysecret" not in result.output

    def test_generic_create_dry_run_masks_nested_sensitive(self, runner, mock_redmine, set_env):
        """Nested sensitive keys should also be masked."""
        result = runner.invoke(
            cli,
            [
                "--dry-run",
                "resource",
                "create",
                "user",
                '--json',
                '{"login":"admin","password":"secret","firstname":"Admin"}',
            ],
        )
        assert result.exit_code == 0
        data = parse_output(result.output)
        assert data["data"]["payload"]["password"] == "****"
        assert data["data"]["payload"]["login"] == "admin"
        assert "secret" not in result.output
