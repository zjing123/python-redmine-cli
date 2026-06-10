"""Generic resource CRUD - dynamic routing for any registered Redmine resource.

Uses redminelib.resources.registry to discover all available resource types.
Provides a uniform interface for agents that don't need resource-specific commands.
"""

import click

from ..output import emit, handle_errors
from ..utils import parse_json_input, resourceset_to_list
from ..context import get_redmine, resolve_ref
from redminelib.resources import registry as resource_registry


def _get_manager(rm, resource_name):
    """Get a resource manager by snake_case name (e.g. 'issue', 'wiki_page')."""
    try:
        return getattr(rm, resource_name)
    except AttributeError:
        raise click.BadParameter(
            f"Unknown resource '{resource_name}'. "
            f"Use 'redmine-cli resource types' to see available resources."
        )


@click.group("resource")
@click.pass_context
def generic_group(ctx):
    """Generic resource CRUD for any registered Redmine resource type.

    Use 'resource types' to discover all available resource types.
    """
    pass


@generic_group.command("types")
@click.pass_context
def resource_types(ctx):
    """List all available resource types.

    Returns the names of all Redmine resource types supported by the library,
    e.g. issue, project, user, version, time_entry, wiki_page, etc.
    """
    emit({"resource_types": sorted(resource_registry.keys())})


@generic_group.command("get")
@click.argument("resource_name")
@click.argument("resource_ref")
@click.pass_context
@handle_errors
def resource_get(ctx, resource_name, resource_ref):
    """Get a single resource by ID or URL.

    \b
    Accepts an integer ID, a string identifier, or a full Redmine URL.
    When a URL is given, the profile is auto-detected from the URL.

    \b
    Examples:
      redmine-cli resource get issue 123
      redmine-cli resource get issue https://redmine.example.com/issues/123
      redmine-cli resource get project my-project
      redmine-cli resource get user 5
    """
    resource_id = resolve_ref(ctx, resource_ref)
    rm = get_redmine(ctx)
    manager = _get_manager(rm, resource_name)
    result = manager.get(resource_id)
    emit(result.raw())


@generic_group.command("list")
@click.argument("resource_name")
@click.option("--limit", "-l", type=int, default=0, help="Max results (0=no limit)")
@click.option("--offset", type=int, default=0, help="Result offset for pagination")
@click.option(
    "--fields",
    help="Comma-separated fields to include in output. Reduces output size for agents.",
)
@click.pass_context
@handle_errors
def resource_list(ctx, resource_name, limit, offset, fields):
    """List all resources of a given type.

    \b
    Examples:
      redmine-cli resource list issue
      redmine-cli resource list project
      redmine-cli resource list user
    """
    rm = get_redmine(ctx)
    manager = _get_manager(rm, resource_name)
    rs = manager.all()

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


@generic_group.command("filter")
@click.argument("resource_name")
@click.option(
    "--json", "json_data", required=True, help="JSON object with filter fields"
)
@click.option("--limit", "-l", type=int, default=0, help="Max results (0=no limit)")
@click.option("--offset", type=int, default=0, help="Result offset for pagination")
@click.option(
    "--fields",
    help="Comma-separated fields to include in output. Reduces output size for agents.",
)
@click.pass_context
@handle_errors
def resource_filter(ctx, resource_name, json_data, limit, offset, fields):
    """Filter resources by fields.

    \b
    Examples:
      redmine-cli resource filter issue --json '{"project_id": 1}'
      redmine-cli resource filter user --json '{"status": 1}'
      redmine-cli resource filter time-entry --json '{"project_id": 1, "from_date": "2025-01-01"}'
    """
    rm = get_redmine(ctx)
    manager = _get_manager(rm, resource_name)
    filters = parse_json_input(json_data)
    rs = manager.filter(**filters)

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


@generic_group.command("create")
@click.argument("resource_name")
@click.option(
    "--json", "json_data", required=True, help="JSON object with creation fields"
)
@click.pass_context
@handle_errors
def resource_create(ctx, resource_name, json_data):
    """Create a new resource.

    \b
    Examples:
      redmine-cli resource create issue --json '{"project_id": 1, "subject": "Bug report"}'
      redmine-cli resource create project --json '{"name": "Test", "identifier": "test"}'
    """
    rm = get_redmine(ctx)
    manager = _get_manager(rm, resource_name)
    fields = parse_json_input(json_data)
    result = manager.create(**fields)
    emit(result.raw())


@generic_group.command("update")
@click.argument("resource_name")
@click.argument("resource_ref")
@click.option(
    "--json", "json_data", required=True, help="JSON object with update fields"
)
@click.pass_context
@handle_errors
def resource_update(ctx, resource_name, resource_ref, json_data):
    """Update an existing resource.

    \b
    Accepts an integer ID or a full Redmine URL for the resource reference.

    \b
    Examples:
      redmine-cli resource update issue 123 --json '{"status_id": 3, "notes": "Fixed"}'
      redmine-cli resource update issue https://redmine.example.com/issues/123 --json '{"status_id": 3}'
      redmine-cli resource update project test --json '{"name": "New Name"}'
    """
    resource_id = resolve_ref(ctx, resource_ref)
    rm = get_redmine(ctx)
    manager = _get_manager(rm, resource_name)
    fields = parse_json_input(json_data)
    manager.update(resource_id, **fields)
    emit({"updated": True, "resource": resource_name, "id": resource_id})


@generic_group.command("delete")
@click.argument("resource_name")
@click.argument("resource_ref")
@click.pass_context
@handle_errors
def resource_delete(ctx, resource_name, resource_ref):
    """Delete a resource.

    \b
    Accepts an integer ID or a full Redmine URL for the resource reference.

    \b
    Examples:
      redmine-cli resource delete issue 123
      redmine-cli resource delete issue https://redmine.example.com/issues/123
      redmine-cli resource delete version 5
    """
    resource_id = resolve_ref(ctx, resource_ref)
    rm = get_redmine(ctx)
    manager = _get_manager(rm, resource_name)
    manager.delete(resource_id)
    emit({"deleted": True, "resource": resource_name, "id": resource_id})
