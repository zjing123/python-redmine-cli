"""Generic resource CRUD - dynamic routing for any registered Redmine resource.

Uses redminelib.resources.registry to discover all available resource types.
Provides a uniform interface for agents that don't need resource-specific commands.
"""

import click

from ..output import emit, handle_errors, emit_dry_run
from ..utils import parse_json_input, resourceset_to_list, resolve_json_data
from ..context import get_redmine, resolve_ref, build_dry_run_url, DRY_RUN_METHODS
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

    \b
    Use 'resource types' to discover all available resource types.
    Resource arguments (RESOURCE_REF) accept:
      - Integer ID or identifier (requires -p):  redmine-cli -p prod resource get issue 123
      - Full URL (auto-detects profile):         redmine-cli resource get issue https://prod.example.com/issues/123
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
@click.option(
    "--fields",
    help="Comma-separated fields to include in output. Reduces output size for agents.",
)
@click.pass_context
@handle_errors
def resource_get(ctx, resource_name, resource_ref, fields):
    """Get a single resource by ID or URL.

    \b
    RESOURCE_REF accepts an integer ID or string identifier (requires -p),
    or a full Redmine URL (auto-detects profile).

    \b
    Examples:
      redmine-cli -p redminex resource get issue 123
      redmine-cli resource get issue https://redminex.silksoftware.com/issues/123
      redmine-cli -p redminex resource get project my-project
      redmine-cli -p redminex resource get user 5
      redmine-cli -p redminex resource get issue 123 --fields id,subject,status
    """
    resource_id = resolve_ref(ctx, resource_ref)
    rm = get_redmine(ctx)
    manager = _get_manager(rm, resource_name)
    result = manager.get(resource_id)
    emit(result.raw(), fields=fields.split(",") if fields else None)


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
      redmine-cli -p redminex resource list issue
      redmine-cli -p redminex resource list project
      redmine-cli -p redminex resource list user
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
    "--json", "json_data", help="JSON object with filter fields"
)
@click.option("--stdin", "stdin_mode", is_flag=True, help="Read JSON from stdin")
@click.option("--limit", "-l", type=int, default=0, help="Max results (0=no limit)")
@click.option("--offset", type=int, default=0, help="Result offset for pagination")
@click.option(
    "--fields",
    help="Comma-separated fields to include in output. Reduces output size for agents.",
)
@click.pass_context
@handle_errors
def resource_filter(ctx, resource_name, json_data, stdin_mode, limit, offset, fields):
    """Filter resources by fields.

    \b
    Either --json or --stdin is required.

    \b
    Examples:
      redmine-cli -p redminex resource filter issue --json '{"project_id": 1}'
      redmine-cli -p redminex resource filter user --json '{"status": 1}'
      echo '{"project_id": 1}' | redmine-cli -p redminex resource filter issue --stdin
    """
    rm = get_redmine(ctx)
    manager = _get_manager(rm, resource_name)
    filters = resolve_json_data(json_data, stdin_mode, required=True)
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
    "--json", "json_data", help="JSON object with creation fields"
)
@click.option("--stdin", "stdin_mode", is_flag=True, help="Read JSON from stdin")
@click.pass_context
@handle_errors
def resource_create(ctx, resource_name, json_data, stdin_mode):
    """Create a new resource.

    \b
    Either --json or --stdin is required.

    \b
    Examples:
      redmine-cli -p redminex resource create issue --json '{"project_id": 1, "subject": "Bug report"}'
      redmine-cli -p redminex resource create project --json '{"name": "Test", "identifier": "test"}'
      echo '{"project_id":1,"subject":"Bug report"}' | redmine-cli -p redminex resource create issue --stdin
    """
    rm = get_redmine(ctx)
    manager = _get_manager(rm, resource_name)
    fields = resolve_json_data(json_data, stdin_mode, required=True)
    if ctx.obj.get("_dry_run"):
        url = build_dry_run_url(rm.url, resource_name, "create")
        emit_dry_run("create", resource_name, DRY_RUN_METHODS["create"], url, payload=fields)
        return
    result = manager.create(**fields)
    emit(result.raw())


@generic_group.command("update")
@click.argument("resource_name")
@click.argument("resource_ref")
@click.option(
    "--json", "json_data", help="JSON object with update fields"
)
@click.option("--stdin", "stdin_mode", is_flag=True, help="Read JSON from stdin")
@click.pass_context
@handle_errors
def resource_update(ctx, resource_name, resource_ref, json_data, stdin_mode):
    """Update an existing resource.

    \b
    RESOURCE_REF accepts an integer ID (requires -p) or a full Redmine URL.
    Either --json or --stdin is required.

    \b
    Examples:
      redmine-cli -p redminex resource update issue 123 --json '{"status_id": 3}'
      redmine-cli resource update issue https://redminex.silksoftware.com/issues/123 --json '{"status_id": 3}'
      redmine-cli -p redminex resource update project test --json '{"name": "New Name"}'
      echo '{"status_id": 3}' | redmine-cli -p redminex resource update issue 123 --stdin
    """
    resource_id = resolve_ref(ctx, resource_ref)
    rm = get_redmine(ctx)
    manager = _get_manager(rm, resource_name)
    fields = resolve_json_data(json_data, stdin_mode, required=True)
    if ctx.obj.get("_dry_run"):
        url = build_dry_run_url(rm.url, resource_name, "update", id=resource_id)
        emit_dry_run("update", resource_name, DRY_RUN_METHODS["update"], url, payload=fields)
        return
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
    RESOURCE_REF accepts an integer ID (requires -p) or a full Redmine URL.

    \b
    Examples:
      redmine-cli -p redminex resource delete issue 123
      redmine-cli resource delete issue https://redminex.silksoftware.com/issues/123
      redmine-cli -p redminex resource delete version 5
    """
    resource_id = resolve_ref(ctx, resource_ref)
    rm = get_redmine(ctx)
    manager = _get_manager(rm, resource_name)
    if ctx.obj.get("_dry_run"):
        url = build_dry_run_url(rm.url, resource_name, "delete", id=resource_id)
        emit_dry_run("delete", resource_name, DRY_RUN_METHODS["delete"], url)
        return
    manager.delete(resource_id)
    emit({"deleted": True, "resource": resource_name, "id": resource_id})


@generic_group.command("fields")
@click.argument("resource_name")
@click.pass_context
@handle_errors
def resource_fields(ctx, resource_name):
    """Show available fields for any resource type.

    No connection required. Reads metadata from the python-redmine library.

    \b
    Examples:
      redmine-cli resource fields issue
      redmine-cli resource fields project
      redmine-cli resource fields wiki_page
      redmine-cli resource fields tracker
    """
    from ..fields import get_resource_fields

    try:
        emit(get_resource_fields(resource_name))
    except ValueError as e:
        raise click.BadParameter(str(e))


@generic_group.command("schema")
@click.argument("resource_name")
@click.option(
    "--live",
    is_flag=True,
    help="Fetch live enum values (trackers, statuses, priorities) from Redmine",
)
@click.pass_context
@handle_errors
def resource_schema(ctx, resource_name, live):
    """Show creation schema for a resource type.

    Returns required fields, optional fields, read-only fields, and ID fields.
    Use --live to also fetch enum values (trackers, statuses, priorities) from
    the connected Redmine instance.

    No connection required without --live.

    \b
    Examples:
      redmine-cli resource schema issue
      redmine-cli resource schema project
      redmine-cli -p prod resource schema issue --live
      redmine-cli resource schema wiki_page
    """
    from ..schema import get_resource_schema, get_live_enums

    try:
        schema = get_resource_schema(resource_name)
    except ValueError as e:
        raise click.BadParameter(str(e))

    if live:
        rm = get_redmine(ctx)
        from ..schema import get_live_enums as _get_enums
        schema["enums"] = _get_enums(rm, resource_name)

    emit(schema)
