"""Wiki page subcommands for redmine-cli."""

import click

from ..context import DRY_RUN_METHODS, build_dry_run_url, get_redmine
from ..output import emit, emit_dry_run, handle_errors
from ..utils import build_fields, resolve_json_data, resourceset_to_list


@click.group("wiki-page")
@click.pass_context
def wiki_page_group(ctx):
    """Wiki page operations: CRUD within a project. All commands require --project-id."""
    pass


@wiki_page_group.command("get")
@click.argument("title")
@click.option("--project-id", required=True, type=int, help="Project ID (required)")
@click.option(
    "--fields",
    help="Comma-separated fields to include in output (e.g. title,text,updated_on). Reduces output size for agents.",
)
@click.pass_context
@handle_errors
def wiki_page_get(ctx, title, project_id, fields):
    """Get a wiki page by title.

    \b
    Example:
      redmine-cli wiki-page get "PageTitle" --project-id 1
      redmine-cli wiki-page get "PageTitle" --project-id 1 --fields title,text,version
    """
    rm = get_redmine(ctx)
    result = rm.wiki_page.get(title, project_id=project_id)
    emit(result.raw(), fields=fields.split(",") if fields else None)


@wiki_page_group.command("list")
@click.option("--project-id", required=True, type=int, help="Project ID (required)")
@click.option("--limit", "-l", type=int, default=50, help="Max results (default: 50, use --all for unlimited)")
@click.option("--all", "fetch_all", is_flag=True, help="Fetch all results (no limit)")
@click.option("--offset", type=int, default=0, help="Result offset for pagination")
@click.option(
    "--fields",
    help="Comma-separated fields to include in output (e.g. title,updated_on). Reduces output size.",
)
@click.pass_context
@handle_errors
def wiki_page_list(ctx, project_id, limit, fetch_all, offset, fields):
    """List wiki pages in a project. --project-id is required."""
    rm = get_redmine(ctx)
    rs = rm.wiki_page.filter(project_id=project_id)

    effective_limit = None if fetch_all else limit
    total_count = rs.total_count
    if effective_limit is not None:
        rs = rs[offset : offset + effective_limit] if offset else rs[:effective_limit]
    elif offset:
        rs = rs[offset:]

    data = resourceset_to_list(rs)
    emit(
        data,
        total_count=total_count,
        limit=effective_limit,
        offset=offset,
        fields=fields.split(",") if fields else None,
    )


@wiki_page_group.command("create")
@click.argument("title")
@click.option("--project-id", required=True, type=int, help="Project ID (required)")
@click.option("--json", "json_data", help="JSON string with all fields")
@click.option("--stdin", "stdin_mode", is_flag=True, help="Read JSON from stdin")
@click.option(
    "--text", help="Page content (textile or markdown, depending on Redmine config)"
)
@click.option("--comments", help="Edit comment")
@click.pass_context
@handle_errors
def wiki_page_create(ctx, title, project_id, json_data, stdin_mode, text, comments):
    """Create a new wiki page with the given title.

    --project-id is required. Provide --text for the page content.
    Use --json or --stdin to pass all fields at once.
    """
    rm = get_redmine(ctx)
    json_fields = resolve_json_data(json_data, stdin_mode)
    if json_fields is not None:
        fields = json_fields
    else:
        fields = build_fields(text=text, comments=comments)

    if ctx.obj.get("_dry_run"):
        url = build_dry_run_url(rm.url, "wiki_page", "create", project_id=project_id, title=title)
        emit_dry_run("create", "wiki_page", DRY_RUN_METHODS["create"], url, payload=fields)
        return

    result = rm.wiki_page.create(title=title, project_id=project_id, **fields)
    emit(result.raw())


@wiki_page_group.command("update")
@click.argument("title")
@click.option("--project-id", required=True, type=int, help="Project ID (required)")
@click.option("--json", "json_data", help="JSON string with fields to update")
@click.option("--stdin", "stdin_mode", is_flag=True, help="Read JSON from stdin")
@click.option("--text", help="New page content")
@click.option("--comments", help="Edit comment for this update")
@click.pass_context
@handle_errors
def wiki_page_update(ctx, title, project_id, json_data, stdin_mode, text, comments):
    """Update an existing wiki page's content.

    Use --json or --stdin to pass all fields at once.
    """
    rm = get_redmine(ctx)
    json_fields = resolve_json_data(json_data, stdin_mode)
    if json_fields is not None:
        fields = json_fields
    else:
        fields = build_fields(text=text, comments=comments)

    if ctx.obj.get("_dry_run"):
        url = build_dry_run_url(rm.url, "wiki_page", "update", project_id=project_id, title=title)
        emit_dry_run("update", "wiki_page", DRY_RUN_METHODS["update"], url, payload=fields)
        return

    rm.wiki_page.update(title, project_id=project_id, **fields)
    emit({"updated": True, "resource": "wiki_page", "title": title, "project_id": project_id})


@wiki_page_group.command("delete")
@click.argument("title")
@click.option("--project-id", required=True, type=int, help="Project ID (required)")
@click.pass_context
@handle_errors
def wiki_page_delete(ctx, title, project_id):
    """Delete a wiki page permanently."""
    rm = get_redmine(ctx)
    if ctx.obj.get("_dry_run"):
        url = build_dry_run_url(rm.url, "wiki_page", "delete", project_id=project_id, title=title)
        emit_dry_run("delete", "wiki_page", DRY_RUN_METHODS["delete"], url)
        return
    rm.wiki_page.delete(title, project_id=project_id)
    emit({"deleted": True, "resource": "wiki_page", "title": title, "project_id": project_id})


@wiki_page_group.command("fields")
@click.pass_context
@handle_errors
def wiki_page_fields(ctx):
    """Show available fields for the wiki_page resource type.

    \b
    Example:
      redmine-cli wiki-page fields
    """
    from ..fields import get_resource_fields

    emit(get_resource_fields("wiki_page"))


@wiki_page_group.command("schema")
@click.pass_context
@handle_errors
def wiki_page_schema(ctx):
    """Show creation schema for wiki pages.

    Returns required fields, optional fields, read-only fields, and ID fields.

    \b
    Example:
      redmine-cli wiki-page schema
    """
    from ..schema import get_resource_schema

    emit(get_resource_schema("wiki_page"))
