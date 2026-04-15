"""Shared context helpers for redmine-cli."""

import click

from .config import create_redmine


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
