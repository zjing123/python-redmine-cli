"""Time entry subcommands for redmine-cli."""

import click

from ..output import emit, handle_errors, emit_dry_run
from ..utils import parse_json_input, resourceset_to_list, build_fields, resolve_json_data
from ..context import get_redmine, resolve_ref, build_dry_run_url, DRY_RUN_METHODS


@click.group("time-entry")
@click.pass_context
def time_entry_group(ctx):
    """Time entry operations: CRUD with date range and project/issue filters.

    \b
    Resource arguments (ENTRY_REF) accept:
      - Integer ID (requires -p):  redmine-cli -p prod time-entry get 123
      - Full URL (auto-detects):   redmine-cli time-entry get https://prod.example.com/time_entries/123
    """
    pass


@time_entry_group.command("get")
@click.argument("entry_ref")
@click.option(
    "--fields",
    help="Comma-separated fields to include in output (e.g. id,hours,activity,comments). Reduces output size for agents.",
)
@click.pass_context
@handle_errors
def time_entry_get(ctx, entry_ref, fields):
    """Get a single time entry by ID or URL.

    \b
    ENTRY_REF accepts an integer ID (requires -p) or a full Redmine URL.

    \b
    Examples:
      redmine-cli -p redminex time-entry get 123
      redmine-cli time-entry get https://redminex.silksoftware.com/time_entries/123
      redmine-cli -p redminex time-entry get 123 --fields id,hours,spent_on
    """
    entry_id = resolve_ref(ctx, entry_ref)
    rm = get_redmine(ctx)
    result = rm.time_entry.get(int(entry_id))
    emit(result.raw(), fields=fields.split(",") if fields else None)


@time_entry_group.command("list")
@click.option("--project-id", type=int, help="Filter by project ID")
@click.option("--issue-id", type=int, help="Filter by issue ID")
@click.option("--user-id", type=int, help="Filter by user ID")
@click.option("--activity-id", type=int, help="Filter by activity ID")
@click.option("--from", "from_date", help="Start date (YYYY-MM-DD)")
@click.option("--to", "to_date", help="End date (YYYY-MM-DD)")
@click.option("--limit", "-l", type=int, default=0, help="Max results (0=no limit)")
@click.option("--offset", type=int, default=0, help="Result offset for pagination")
@click.option(
    "--fields",
    help="Comma-separated fields to include in output (e.g. id,hours,activity_id,comments). Reduces output size.",
)
@click.pass_context
@handle_errors
def time_entry_list(
    ctx,
    project_id,
    issue_id,
    user_id,
    activity_id,
    from_date,
    to_date,
    limit,
    offset,
    fields,
):
    """List time entries with optional filters.

    \b
    Filter by project, issue, user, activity, or date range (--from, --to as YYYY-MM-DD).
    Supports pagination with --limit and --offset.

    \b
    Examples:
      redmine-cli -p redminex time-entry list --issue-id 123
      redmine-cli -p redminex time-entry list --from 2025-01-01 --to 2025-01-31
    """
    rm = get_redmine(ctx)
    kwargs = {}
    for key, val in [
        ("project_id", project_id),
        ("issue_id", issue_id),
        ("user_id", user_id),
        ("activity_id", activity_id),
        ("from_date", from_date),
        ("to_date", to_date),
    ]:
        if val is not None:
            kwargs[key] = val

    if kwargs:
        rs = rm.time_entry.filter(**kwargs)
    else:
        rs = rm.time_entry.all()

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


@time_entry_group.command("create")
@click.option("--json", "json_data", help="JSON string with all fields")
@click.option("--stdin", "stdin_mode", is_flag=True, help="Read JSON from stdin")
@click.option("--issue-id", type=int, help="Issue ID")
@click.option("--project-id", type=int, help="Project ID (alternative to issue-id)")
@click.option("--spent-on", help="Date (YYYY-MM-DD), defaults to today")
@click.option("--hours", type=float, help="Hours spent")
@click.option("--activity-id", type=int, help="Activity ID")
@click.option("--comments", help="Comments")
@click.pass_context
@handle_errors
def time_entry_create(
    ctx, json_data, stdin_mode, issue_id, project_id, spent_on, hours, activity_id, comments
):
    """Create a new time entry.

    \b
    Provide either --issue-id or --project-id, along with --hours.
    Use --json or --stdin to pass all fields at once.

    \b
    Examples:
      redmine-cli -p redminex time-entry create --issue-id 123 --hours 2.5 --activity-id 1
      echo '{"issue_id":123,"hours":2.5}' | redmine-cli -p redminex time-entry create --stdin
    """
    rm = get_redmine(ctx)
    json_fields = resolve_json_data(json_data, stdin_mode)
    if json_fields is not None:
        fields = json_fields
    else:
        fields = build_fields(
            issue_id=issue_id,
            project_id=project_id,
            spent_on=spent_on,
            hours=hours,
            activity_id=activity_id,
            comments=comments,
        )

    if ctx.obj.get("_dry_run"):
        url = build_dry_run_url(rm.url, "time_entry", "create")
        emit_dry_run("create", "time_entry", DRY_RUN_METHODS["create"], url, payload=fields)
        return

    result = rm.time_entry.create(**fields)
    emit(result.raw())


@time_entry_group.command("update")
@click.argument("entry_ref")
@click.option("--json", "json_data", help="JSON string with fields to update")
@click.option("--stdin", "stdin_mode", is_flag=True, help="Read JSON from stdin")
@click.option("--hours", type=float, help="New hours")
@click.option("--activity-id", type=int, help="New activity ID")
@click.option("--comments", help="New comments")
@click.option("--spent-on", help="New date (YYYY-MM-DD)")
@click.pass_context
@handle_errors
def time_entry_update(ctx, entry_ref, json_data, stdin_mode, hours, activity_id, comments, spent_on):
    """Update an existing time entry's fields.

    \b
    ENTRY_REF accepts an integer ID (requires -p) or a full Redmine URL.

    \b
    Examples:
      redmine-cli -p redminex time-entry update 123 --hours 3.0
      redmine-cli time-entry update https://redminex.silksoftware.com/time_entries/123 --hours 3.0
      echo '{"hours":3.0}' | redmine-cli -p redminex time-entry update 123 --stdin
    """
    entry_id = resolve_ref(ctx, entry_ref)
    rm = get_redmine(ctx)
    json_fields = resolve_json_data(json_data, stdin_mode)
    if json_fields is not None:
        fields = json_fields
    else:
        fields = build_fields(
            hours=hours,
            activity_id=activity_id,
            comments=comments,
            spent_on=spent_on,
        )

    if ctx.obj.get("_dry_run"):
        url = build_dry_run_url(rm.url, "time_entry", "update", id=entry_id)
        emit_dry_run("update", "time_entry", DRY_RUN_METHODS["update"], url, payload=fields)
        return

    rm.time_entry.update(int(entry_id), **fields)
    emit({"updated": True, "resource": "time_entry", "id": entry_id})


@time_entry_group.command("delete")
@click.argument("entry_ref")
@click.pass_context
@handle_errors
def time_entry_delete(ctx, entry_ref):
    """Delete a time entry permanently.

    \b
    ENTRY_REF accepts an integer ID (requires -p) or a full Redmine URL.

    \b
    Examples:
      redmine-cli -p redminex time-entry delete 123
      redmine-cli time-entry delete https://redminex.silksoftware.com/time_entries/123
    """
    entry_id = resolve_ref(ctx, entry_ref)
    rm = get_redmine(ctx)
    if ctx.obj.get("_dry_run"):
        url = build_dry_run_url(rm.url, "time_entry", "delete", id=entry_id)
        emit_dry_run("delete", "time_entry", DRY_RUN_METHODS["delete"], url)
        return
    rm.time_entry.delete(int(entry_id))
    emit({"deleted": True, "resource": "time_entry", "id": entry_id})


@time_entry_group.command("fields")
@click.pass_context
@handle_errors
def time_entry_fields(ctx):
    """Show available fields for the time_entry resource type.

    \b
    Example:
      redmine-cli time-entry fields
    """
    from ..fields import get_resource_fields

    emit(get_resource_fields("time_entry"))


@time_entry_group.command("schema")
@click.option(
    "--live",
    is_flag=True,
    help="Fetch live activity enum from Redmine",
)
@click.pass_context
@handle_errors
def time_entry_schema(ctx, live):
    """Show creation schema for time entries.

    Returns required fields, optional fields, read-only fields, and ID fields.
    Use --live to also fetch time entry activities from Redmine.

    \b
    Examples:
      redmine-cli time-entry schema
      redmine-cli -p prod time-entry schema --live
    """
    from ..schema import get_resource_schema, get_live_enums

    schema = get_resource_schema("time_entry")
    if live:
        rm = get_redmine(ctx)
        schema["enums"] = get_live_enums(rm, "time_entry")
    emit(schema)
