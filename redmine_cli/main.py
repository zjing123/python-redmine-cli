"""Root CLI entry point and global options."""

import click

from .commands import config_group, search
from .resources import generic, issue, project, time_entry, user, wiki_page


@click.group()
@click.option(
    "--profile",
    "-p",
    envvar="REDMINE_PROFILE",
    help="Use a specific connection profile. Profiles are managed via 'config set/update/unset'.",
)
@click.option(
    "--url",
    envvar="REDMINE_URL",
    help="Override Redmine server URL for this invocation",
)
@click.option(
    "--api-key",
    envvar="REDMINE_API_KEY",
    help="Override Redmine API key for this invocation",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be sent to the API without executing",
)
@click.pass_context
def cli(ctx, profile, url, api_key, dry_run):
    """Redmine CLI - Agent-friendly command line interface for Redmine.

    \b
    All output is JSON with format: {"ok": true/false, "data": ..., "error": ...}
    Exit codes: 0=success, 1=business error, 2=argument error.

    \b
    Profile selection (in priority order):
      1. -p / REDMINE_PROFILE env var (explicit profile name)
      2. Full URL as argument (auto-detect profile from URL)
      3. --url / REDMINE_URL env var (direct URL override)

    \b
    Quick start:
      1. redmine-cli config set --url https://redmine.example.com --api-key xxx
      2. redmine-cli config test
      3. redmine-cli -p redmine issue list --assigned-to-me --status open
      4. redmine-cli issue get https://redmine.example.com/issues/123
    """
    ctx.ensure_object(dict)
    ctx.obj["_profile"] = profile
    ctx.obj["_url"] = url
    ctx.obj["_api_key"] = api_key
    ctx.obj["_dry_run"] = dry_run


cli.add_command(config_group, "config")
cli.add_command(search)
cli.add_command(issue.issue_group, "issue")
cli.add_command(project.project_group, "project")
cli.add_command(user.user_group, "user")
cli.add_command(time_entry.time_entry_group, "time-entry")
cli.add_command(wiki_page.wiki_page_group, "wiki-page")
cli.add_command(generic.generic_group, "resource")
