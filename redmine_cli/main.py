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
@click.pass_context
def cli(ctx, profile, url, api_key):
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


# --- config commands ---


@cli.group("config")
def config_group():
    """Manage Redmine connection profiles.

    \b
    Profiles store connection info (URL + credentials) in
    ~/.config/redmine-cli/config.yaml. Supports API key auth and
    username/password auth. Secrets are automatically masked in list/get output.
    """
    pass


@config_group.command("path")
def config_path():
    """Show the config file path and whether it exists.

    \b
    Default path: ~/.config/redmine-cli/config.yaml
    Override with environment variable: REDMINE_CONFIG=/path/to/config.yaml
    """
    emit({"path": str(DEFAULT_CONFIG_PATH), "exists": DEFAULT_CONFIG_PATH.exists()})


@config_group.command("profiles")
def config_profiles():
    """List all configured profiles with their URLs.

    Shows profile names and server URLs. Does not expose credentials.
    """
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
    """Show the active connection URL (no secrets exposed).

    Useful to verify which Redmine instance the CLI is currently connected to.
    """
    rm = get_redmine(ctx)
    emit({"url": rm.url})


@config_group.command("test")
@click.pass_context
@handle_errors
def config_test(ctx):
    """Test connection to Redmine and return the authenticated user info.

    Returns user details (id, login, name) on success. Fails with error if connection or auth fails.
    """
    rm = get_redmine(ctx)
    user = rm.auth()
    emit({"connected": True, "user": user.raw()})


@config_group.command("list")
@click.option(
    "--profile",
    "-p",
    default=None,
    help="Show a specific profile's config. Shows all profiles if omitted.",
)
@click.option(
    "--print",
    "as_table",
    is_flag=True,
    help="Print a human-readable table instead of JSON.",
)
def config_list(profile, as_table):
    """List config values (secrets are masked).

    Default output is JSON. Use --print for a human-readable table.
    Without --profile, shows all profiles. Secrets (api_key, password) show only last 4 chars.
    """
    data = load_config_file()
    targets = {}
    if profile:
        if profile == "default":
            targets[profile] = data.get("default", {})
        else:
            targets[profile] = data.get("profiles", {}).get(profile, {})
    else:
        if data.get("default"):
            targets["default"] = data["default"]
        for name in sorted(data.get("profiles", {})):
            targets[name] = data["profiles"][name]

    rows = []
    for name, section in targets.items():
        if not section:
            continue
        api_key = section.get("api_key") or section.get("key") or ""
        password = section.get("password") or ""
        rows.append(
            {
                "profile": name,
                "url": section.get("url", ""),
                "auth": "api_key" if api_key else "password" if password else "",
                "api_key": "****" + str(api_key)[-4:] if api_key else "",
                "username": section.get("username", ""),
                "password": "****" + str(password)[-4:] if password else "",
            }
        )

    if not rows:
        if as_table:
            click.echo("No config profiles found.")
        else:
            emit({"profiles": []})
        return

    if as_table:
        headers = ["PROFILE", "URL", "AUTH", "API_KEY", "USERNAME", "PASSWORD"]
        keys = ["profile", "url", "auth", "api_key", "username", "password"]
        widths = [
            max(len(header), *(len(str(row[key])) for row in rows))
            for header, key in zip(headers, keys)
        ]
        border = "+" + "+".join("-" * (width + 2) for width in widths) + "+"
        click.echo(border)
        click.echo(
            "|"
            + "|".join(
                f" {header.ljust(width)} " for header, width in zip(headers, widths)
            )
            + "|"
        )
        click.echo(border)
        for row in rows:
            click.echo(
                "|"
                + "|".join(
                    f" {str(row[key]).ljust(width)} "
                    for key, width in zip(keys, widths)
                )
                + "|"
            )
            click.echo(border)
    else:
        emit({"profiles": rows})


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
    --url is required. Provide either --api-key for API key auth, or
    --username and --password together for basic auth. These two modes are
    mutually exclusive.
    If -p is omitted, the profile name is auto-derived from the URL hostname
    (e.g. https://staging.example.com -> staging).
    Use 'config update' to modify an existing profile.

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
    -p is required to specify which profile to update.
    Provide at least one of --url, --api-key, --username/--password.
    When switching auth mode (e.g. api-key -> username/password), the old
    credentials are automatically removed.
    Use 'config set' to create a new profile.

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
    """Get a single config value by key name.

    Keys: url, api_key, username, password. Secrets are automatically masked.
    Use -p to read from a specific profile.
    """
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
    """Remove an entire profile and all its configuration.

    -p is required. This deletes the whole profile (URL + credentials).
    To change individual values, use 'config update' instead.
    """
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
@click.option(
    "--resources",
    "-r",
    help="Comma-separated resource types to search (e.g. issues,wiki_pages,news)",
)
@click.pass_context
@handle_errors
def search(ctx, query, resources):
    """Full-text search across Redmine resources.

    \b
    Searches issues, wiki pages, news, documents, changesets, etc.
    Use -r to limit results to specific resource types.
    Returns matching resources with their basic fields.

    \b
    Examples:
      redmine-cli -p redminex search "login error"
      redmine-cli -p redminex search "部署" -r issues
      redmine-cli -p redminex search "API" -r issues,documents
    """
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
