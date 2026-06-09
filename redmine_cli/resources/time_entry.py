"""Time entry subcommands for redmine-cli."""

import click

from ..output import emit, handle_errors
from ..utils import parse_json_input, resourceset_to_list, build_fields
from ..context import get_redmine


@click.group("time-entry")
@click.pass_context
def time_entry_group(ctx):
    """Time entry operations: CRUD with date range and project/issue filters."""
    pass


@time_entry_group.command("get")
@click.argument("entry_id", type=int)
@click.pass_context
@handle_errors
def time_entry_get(ctx, entry_id):
    """Get a single time entry by ID."""
    rm = get_redmine(ctx)
    result = rm.time_entry.get(entry_id)
    emit(result.raw())


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

    Filter by project, issue, user, activity, or date range (--from, --to as YYYY-MM-DD).
    Supports pagination with --limit and --offset.
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
@click.option("--issue-id", type=int, help="Issue ID")
@click.option("--project-id", type=int, help="Project ID (alternative to issue-id)")
@click.option("--spent-on", help="Date (YYYY-MM-DD), defaults to today")
@click.option("--hours", type=float, help="Hours spent")
@click.option("--activity-id", type=int, help="Activity ID")
@click.option("--comments", help="Comments")
@click.pass_context
@handle_errors
def time_entry_create(
    ctx, json_data, issue_id, project_id, spent_on, hours, activity_id, comments
):
    """Create a new time entry.

    Provide either --issue-id or --project-id, along with --hours.
    Use --json to pass all fields at once.
    """
    rm = get_redmine(ctx)
    if json_data:
        fields = parse_json_input(json_data)
    else:
        fields = build_fields(
            issue_id=issue_id,
            project_id=project_id,
            spent_on=spent_on,
            hours=hours,
            activity_id=activity_id,
            comments=comments,
        )

    result = rm.time_entry.create(**fields)
    emit(result.raw())


@time_entry_group.command("update")
@click.argument("entry_id", type=int)
@click.option("--json", "json_data", help="JSON string with fields to update")
@click.option("--hours", type=float, help="New hours")
@click.option("--activity-id", type=int, help="New activity ID")
@click.option("--comments", help="New comments")
@click.option("--spent-on", help="New date (YYYY-MM-DD)")
@click.pass_context
@handle_errors
def time_entry_update(ctx, entry_id, json_data, hours, activity_id, comments, spent_on):
    """Update an existing time entry's fields."""
    rm = get_redmine(ctx)
    if json_data:
        fields = parse_json_input(json_data)
    else:
        fields = build_fields(
            hours=hours,
            activity_id=activity_id,
            comments=comments,
            spent_on=spent_on,
        )

    rm.time_entry.update(entry_id, **fields)
    emit({"updated": True, "time_entry_id": entry_id})


@time_entry_group.command("delete")
@click.argument("entry_id", type=int)
@click.pass_context
@handle_errors
def time_entry_delete(ctx, entry_id):
    """Delete a time entry permanently."""
    rm = get_redmine(ctx)
    rm.time_entry.delete(entry_id)
    emit({"deleted": True, "time_entry_id": entry_id})
