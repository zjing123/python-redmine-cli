"""Config subcommands for redmine-cli - manage connection profiles.

NOTE: this module (``redmine_cli.commands.config``) holds the ``config`` command
group. The profile read/write helpers live in ``redmine_cli.config`` (one level
up). They share the name "config" but differ by package path.
"""

import click

from ..config import (
    _deduplicate_profile_name,
    _extract_profile_name,
    _resolve_config_path,
    load_config_file,
    save_config_file,
)
from ..context import get_redmine
from ..output import emit, handle_errors


@click.group("config")
def config_group():
    """Manage Redmine connection profiles.

    \b
    Profiles store connection info (URL + credentials) in
    ~/.config/redmine-cli/config.yaml. Supports API key auth and
    username/password auth. Secrets are automatically masked in list/get output.
    """
    pass


@config_group.command("path")
@handle_errors
def config_path():
    """Show the config file path and whether it exists.

    \b
    Default path: ~/.config/redmine-cli/config.yaml
    Override with environment variable: REDMINE_CONFIG=/path/to/config.yaml
    """
    config_path = _resolve_config_path()
    emit({"path": str(config_path), "exists": config_path.exists()})


@config_group.command("profiles")
@handle_errors
def config_profiles():
    """List all configured profiles with their URLs.

    Shows profile names and server URLs. Does not expose credentials.
    """
    data = load_config_file()
    profiles = data.get("profiles", {})
    result = {}
    for name, conf in profiles.items():
        result[name] = {"url": conf.get("url", "")}
    emit({"profiles": result})


@config_group.command("show")
@click.pass_context
@handle_errors
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
@handle_errors
def config_list(profile, as_table):
    """List config values (secrets are masked).

    Default output is JSON. Use --print for a human-readable table.
    Without --profile, shows all profiles. Secrets (api_key, password) show only last 4 chars.
    """
    data = load_config_file()
    targets = {}
    if profile:
        targets[profile] = data.get("profiles", {}).get(profile, {})
    else:
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
@handle_errors
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

    if not url:
        raise click.UsageError("--url is required.")
    if api_key and (username or password):
        raise click.UsageError(
            "--api-key and --username/--password are mutually exclusive."
        )
    if (username and not password) or (password and not username):
        raise click.UsageError("--username and --password must be used together.")

    # Normalize URL: strip trailing slash
    url = url.rstrip("/")

    if profile is None:
        profile = _extract_profile_name(url)
        # Auto-deduplicate when deriving from URL
        profile = _deduplicate_profile_name(profile, data.get("profiles", {}))
    elif profile in data.get("profiles", {}):
        raise click.UsageError(
            f"Profile '{profile}' already exists. Use 'config update' to modify it."
        )

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
@handle_errors
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
    if username and not password:
        raise click.UsageError("--username requires --password.")

    section = data["profiles"][profile]
    if url:
        section["url"] = url.rstrip("/")
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
@handle_errors
def config_get(key, profile):
    """Get a single config value by key name.

    Keys: url, api_key, username, password. Secrets are automatically masked.
    Use -p to read from a specific profile.
    """
    data = load_config_file()
    section = data.get("profiles", {}).get(profile, {})
    value = section.get(key)
    if value is None:
        emit({"key": key, "value": None})
    else:
        if key in ("api_key", "key", "password"):
            value = "****" + str(value)[-4:]
        emit({"key": key, "value": value, "profile": profile or None})


@config_group.command("unset")
@click.option(
    "--profile",
    "-p",
    required=True,
    help="Profile name to remove",
)
@handle_errors
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
