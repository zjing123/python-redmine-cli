"""Root CLI entry point and global options."""

import click

from .output import emit, handle_errors
from .context import get_redmine
from .config import (
    load_config_file,
    save_config_file,
    list_profiles,
    DEFAULT_CONFIG_PATH,
    _extract_profile_name,
)
from .utils import resourceset_to_list
from .resources import issue, project, user, time_entry, wiki_page, generic


@click.group()
@click.option(
    "--profile", "-p", envvar="REDMINE_PROFILE", help="Config file profile name"
)
@click.option("--url", envvar="REDMINE_URL", help="Redmine server URL")
@click.option("--api-key", envvar="REDMINE_API_KEY", help="Redmine API key")
@click.pass_context
def cli(ctx, profile, url, api_key):
    """Redmine CLI - Agent-friendly command line interface for Redmine."""
    ctx.ensure_object(dict)
    ctx.obj["_profile"] = profile
    ctx.obj["_url"] = url
    ctx.obj["_api_key"] = api_key


# --- config commands ---


@cli.group("config")
def config_group():
    """Configuration management."""
    pass


@config_group.command("path")
def config_path():
    """Show config file path."""
    emit({"path": str(DEFAULT_CONFIG_PATH), "exists": DEFAULT_CONFIG_PATH.exists()})


@config_group.command("profiles")
def config_profiles():
    """List all configured profiles."""
    data = load_config_file()
    default = data.get("default", {})
    profiles = data.get("profiles", {})
    result = {}
    if default:
        result["default"] = {"url": default.get("url", "")}
    for name, conf in profiles.items():
        result[name] = {"url": conf.get("url", "")}
    emit({"profiles": result})


@config_group.command("show")
@click.pass_context
def config_show(ctx):
    """Show current connection settings (URL only, no secrets)."""
    rm = get_redmine(ctx)
    emit({"url": rm.url})


@config_group.command("test")
@click.pass_context
@handle_errors
def config_test(ctx):
    """Test connection to Redmine."""
    rm = get_redmine(ctx)
    user = rm.auth()
    emit({"connected": True, "user": user.raw()})


@config_group.command("list")
@click.option(
    "--profile",
    "-p",
    default=None,
    help="Show specific profile (default section if omitted)",
)
def config_list(profile):
    """List all config values (secrets masked)."""
    data = load_config_file()
    section = (
        data.get("profiles", {}).get(profile, {})
        if profile
        else data.get("default", {})
    )
    if not section:
        emit({})
        return
    masked = {}
    for k, v in section.items():
        if k in ("api_key", "key", "password"):
            masked[k] = "****" + str(v)[-4:] if v else ""
        else:
            masked[k] = v
    emit({"profile": profile or "default", "values": masked})


@config_group.command("set")
@click.option("--url", required=False, help="Redmine server URL")
@click.option(
    "--api-key",
    default=None,
    help="API key (mutually exclusive with --username/--password)",
)
@click.option("--username", default=None, help="Username (requires --password)")
@click.option("--password", default=None, help="Password (requires --username)")
@click.option(
    "--profile",
    "-p",
    default=None,
    help="Profile name (auto-derived from URL if omitted)",
)
@click.pass_context
def config_set(ctx, url, api_key, username, password, profile):
    """Create a new profile configuration.

    \b
    Auto name from URL:
      redmine-cli config set --url https://staging.test --api-key secret
      redmine-cli config set --url https://staging.test --username admin --password secret

    \b
    Named profile:
      redmine-cli config set --url https://staging.test --api-key secret -p staging
    """
    data = load_config_file()

    if profile and profile in data.get("profiles", {}):
        raise click.UsageError(
            f"Profile '{profile}' already exists. Use 'config update' to modify it."
        )

    if not url:
        raise click.UsageError("--url is required.")
    if api_key and (username or password):
        raise click.UsageError(
            "--api-key and --username/--password are mutually exclusive."
        )
    if (username and not password) or (password and not username):
        raise click.UsageError("--username and --password must be used together.")

    if profile is None:
        profile = _extract_profile_name(url)

    section = {"url": url}
    if api_key:
        section["api_key"] = api_key
    elif username and password:
        section["username"] = username
        section["password"] = password

    data.setdefault("profiles", {})[profile] = section
    save_config_file(data)

    masked = {}
    for k, v in data["profiles"][profile].items():
        if k in ("api_key", "password"):
            masked[k] = "****" + str(v)[-4:] if v else ""
        else:
            masked[k] = v
    emit({"set": True, "profile": profile, "config": masked})


@config_group.command("update")
@click.option("--url", required=False, help="Redmine server URL")
@click.option(
    "--api-key",
    default=None,
    help="API key (mutually exclusive with --username/--password)",
)
@click.option("--username", default=None, help="Username (requires --password)")
@click.option("--password", default=None, help="Password (requires --username)")
@click.option(
    "--profile",
    "-p",
    required=True,
    help="Profile name to update",
)
@click.pass_context
def config_update(ctx, url, api_key, username, password, profile):
    """Update an existing profile configuration.

    \b
    Examples:
      redmine-cli config update --url https://new.test -p staging
      redmine-cli config update --username admin --password secret -p staging
      redmine-cli config update --api-key secret -p staging
    """
    data = load_config_file()

    if profile not in data.get("profiles", {}):
        raise click.UsageError(
            f"Profile '{profile}' not found. Use 'config set' to create it."
        )

    if not any([url, api_key, username, password]):
        raise click.UsageError(
            "At least one option (--url, --api-key, --username, --password) is required."
        )
    if api_key and (username or password):
        raise click.UsageError(
            "--api-key and --username/--password are mutually exclusive."
        )
    if password and not username:
        raise click.UsageError("--password requires --username.")

    section = data["profiles"][profile]
    if url:
        section["url"] = url
    if api_key:
        section["api_key"] = api_key
        section.pop("username", None)
        section.pop("password", None)
    if username:
        section["username"] = username
        section["password"] = password
        section.pop("api_key", None)

    save_config_file(data)

    masked = {}
    for k, v in data["profiles"][profile].items():
        if k in ("api_key", "password"):
            masked[k] = "****" + str(v)[-4:] if v else ""
        else:
            masked[k] = v
    emit({"updated": True, "profile": profile, "config": masked})


@config_group.command("get")
@click.argument("key")
@click.option("--profile", "-p", default=None, help="Get from specific profile")
def config_get(key, profile):
    """Get a config value."""
    data = load_config_file()
    section = (
        data.get("profiles", {}).get(profile, {})
        if profile
        else data.get("default", {})
    )
    value = section.get(key)
    if value is None:
        emit({"key": key, "value": None})
    else:
        if key in ("api_key", "key", "password"):
            value = "****" + str(value)[-4:]
        emit({"key": key, "value": value, "profile": profile or "default"})


@config_group.command("unset")
@click.option(
    "--profile",
    "-p",
    required=True,
    help="Profile name to remove",
)
def config_unset(profile):
    """Remove an entire profile configuration."""
    data = load_config_file()
    profiles = data.get("profiles", {})
    if profile not in profiles:
        emit({"unset": False, "profile": profile, "note": "profile not found"})
        return
    del profiles[profile]
    save_config_file(data)
    emit({"unset": True, "profile": profile})


# --- search command ---


@cli.command("search")
@click.argument("query")
@click.option("--resources", "-r", help="Comma-separated resource types to search")
@click.pass_context
@handle_errors
def search(ctx, query, resources):
    """Search Redmine resources."""
    rm = get_redmine(ctx)
    opts = {}
    if resources:
        opts["resources"] = [r.strip() for r in resources.split(",")]
    results = rm.search(query, **opts)
    if not results:
        emit({})
        return
    serialized = {}
    for key, value in results.items():
        if (
            hasattr(value, "__iter__")
            and hasattr(value, "__len__")
            and hasattr(value, "__getitem__")
        ):
            serialized[key] = resourceset_to_list(value)
        elif isinstance(value, dict):
            serialized[key] = value
        else:
            serialized[key] = value
    emit(serialized)


# --- register resource subcommands ---

cli.add_command(issue.issue_group, "issue")
cli.add_command(project.project_group, "project")
cli.add_command(user.user_group, "user")
cli.add_command(time_entry.time_entry_group, "time-entry")
cli.add_command(wiki_page.wiki_page_group, "wiki-page")
cli.add_command(generic.generic_group, "resource")
