"""Wiki page subcommands for redmine-cli."""

import click

from ..output import emit, handle_errors
from ..utils import parse_json_input, resourceset_to_list, build_fields
from ..context import get_redmine


@click.group("wiki-page")
@click.pass_context
def wiki_page_group(ctx):
    """Wiki page operations: CRUD within a project. All commands require --project-id."""
    pass


@wiki_page_group.command("get")
@click.argument("title")
@click.option("--project-id", required=True, type=int, help="Project ID (required)")
@click.pass_context
@handle_errors
def wiki_page_get(ctx, title, project_id):
    """Get a wiki page by title.

    \b
    Example:
      redmine-cli wiki-page get "PageTitle" --project-id 1
    """
    rm = get_redmine(ctx)
    result = rm.wiki_page.get(title, project_id=project_id)
    emit(result.raw())


@wiki_page_group.command("list")
@click.option("--project-id", required=True, type=int, help="Project ID (required)")
@click.option("--limit", "-l", type=int, default=0, help="Max results (0=no limit)")
@click.option("--offset", type=int, default=0, help="Result offset for pagination")
@click.option(
    "--fields",
    help="Comma-separated fields to include in output (e.g. title,updated_on). Reduces output size.",
)
@click.pass_context
@handle_errors
def wiki_page_list(ctx, project_id, limit, offset, fields):
    """List wiki pages in a project. --project-id is required."""
    rm = get_redmine(ctx)
    rs = rm.wiki_page.filter(project_id=project_id)

    if limit:
        rs = rs[offset : offset + limit] if offset else rs[:limit]
    elif offset:
        rs = rs[offset:]

    data = resourceset_to_list(rs)
    emit(
        data,
        total_count=rs.total_count,
        limit=limit,
        offset=offset,
        fields=fields.split(",") if fields else None,
    )


@wiki_page_group.command("create")
@click.argument("title")
@click.option("--project-id", required=True, type=int, help="Project ID (required)")
@click.option("--json", "json_data", help="JSON string with all fields")
@click.option(
    "--text", help="Page content (textile or markdown, depending on Redmine config)"
)
@click.option("--comments", help="Edit comment")
@click.pass_context
@handle_errors
def wiki_page_create(ctx, title, project_id, json_data, text, comments):
    """Create a new wiki page with the given title.

    --project-id is required. Provide --text for the page content.
    """
    rm = get_redmine(ctx)
    if json_data:
        fields = parse_json_input(json_data)
    else:
        fields = build_fields(text=text, comments=comments)

    result = rm.wiki_page.create(title=title, project_id=project_id, **fields)
    emit(result.raw())


@wiki_page_group.command("update")
@click.argument("title")
@click.option("--project-id", required=True, type=int, help="Project ID (required)")
@click.option("--json", "json_data", help="JSON string with fields to update")
@click.option("--text", help="New page content")
@click.option("--comments", help="Edit comment for this update")
@click.pass_context
@handle_errors
def wiki_page_update(ctx, title, project_id, json_data, text, comments):
    """Update an existing wiki page's content."""
    rm = get_redmine(ctx)
    if json_data:
        fields = parse_json_input(json_data)
    else:
        fields = build_fields(text=text, comments=comments)

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
    rm.wiki_page.delete(title, project_id=project_id)
    emit({"deleted": True, "resource": "wiki_page", "title": title, "project_id": project_id})
