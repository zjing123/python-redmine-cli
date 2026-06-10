"""Shared context helpers for redmine-cli."""

import re
from urllib.parse import urlparse

import click

from .config import create_redmine, resolve_profile_by_url


def get_redmine(ctx):
    """Lazily create Redmine instance on first use."""
    if "redmine" not in ctx.obj:
        overrides = {}
        if ctx.obj.get("_url"):
            overrides["url"] = ctx.obj["_url"]
        if ctx.obj.get("_api_key"):
            overrides["key"] = ctx.obj["_api_key"]
        try:
            ctx.obj["redmine"] = create_redmine(
                profile=ctx.obj.get("_profile"), **overrides
            )
        except SystemExit:
            raise
        except Exception as e:
            click.echo(f'{{"ok": false, "error": "{e}"}}')
            raise click.Abort()
    return ctx.obj["redmine"]


def resolve_ref(ctx, ref):
    """Resolve a reference that can be an integer ID or a full Redmine URL.

    When a URL is detected:
    - Extracts the resource ID from the URL path
    - Resolves the profile by matching URL against configured profiles
    - Sets profile in ctx only if -p was not explicitly provided

    When a plain integer or identifier is given, returns it unchanged.

    :param ctx: Click context (ctx.obj must contain _profile key).
    :param ref: Integer, numeric string, string identifier, or full Redmine URL.
    :returns: Resource ID (int or str).
    """
    ref_str = str(ref).strip()

    # Try as URL
    parsed = urlparse(ref_str)
    if parsed.scheme and parsed.netloc:
        # Strip common trailing actions (/edit, /new)
        path = re.sub(r"/(edit|new|delete)$", "", parsed.path)
        segments = [s for s in path.split("/") if s]

        if segments:
            last = segments[-1]
            try:
                resource_id = int(last)
            except ValueError:
                resource_id = last  # String identifier (e.g. project identifier)

            # Resolve profile from URL only if -p not explicitly set
            if not ctx.obj.get("_profile"):
                profile = resolve_profile_by_url(ref_str)
                if profile:
                    ctx.obj["_profile"] = profile
                else:
                    raise click.UsageError(
                        f"No configured profile matches URL: {ref_str}\n"
                        f"Use 'redmine-cli config set --url <base_url> --api-key <key>' to add one."
                    )

            return resource_id

    # Non-URL reference (integer, string identifier):
    # requires explicit profile (-p / REDMINE_PROFILE) or URL override (--url / REDMINE_URL)
    if not ctx.obj.get("_profile") and not ctx.obj.get("_url"):
        raise click.UsageError(
            "Profile is required (-p or REDMINE_URL) when not using a full URL.\n"
            "Usage: redmine-cli -p <profile> issue get <id>\n"
            "   or: redmine-cli issue get <url>\n"
            "   or: REDMINE_URL=... redmine-cli issue get <id>"
        )

    # Pure numeric -> return as int
    if ref_str.isdigit():
        return int(ref_str)

    # Return as-is (string identifier like "current", "my-project")
    return ref_str
