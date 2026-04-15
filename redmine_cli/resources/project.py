"""Project subcommands for redmine-cli."""

import click

from ..output import emit, handle_errors
from ..utils import parse_json_input, resourceset_to_list, build_fields
from ..context import get_redmine


@click.group("project")
@click.pass_context
def project_group(ctx):
    """Project operations."""
    pass


@project_group.command("get")
@click.argument("project_id")
@click.pass_context
@handle_errors
def project_get(ctx, project_id):
    """Get a single project by ID or identifier."""
    rm = get_redmine(ctx)
    try:
        pid = int(project_id)
    except ValueError:
        pid = project_id
    result = rm.project.get(pid)
    emit(result.raw())


@project_group.command("list")
@click.option("--limit", "-l", type=int, default=0, help="Max results (0=all)")
@click.option("--offset", type=int, default=0, help="Result offset")
@click.option(
    "--include",
    "-i",
    "includes",
    help="Comma-separated: trackers,issue_categories,enabled_modules,time_entry_activities",
)
@click.pass_context
@handle_errors
def project_list(ctx, limit, offset, includes):
    """List all projects."""
    rm = get_redmine(ctx)
    kwargs = {}
    if includes:
        kwargs["include"] = includes.split(",")

    rs = rm.project.all(**kwargs)

    if limit:
        rs = rs[offset : offset + limit] if offset else rs[:limit]
    elif offset:
        rs = rs[offset:]

    data = resourceset_to_list(rs)
    emit(data, total_count=rs.total_count, limit=limit, offset=offset)


@project_group.command("create")
@click.option("--json", "json_data", help="JSON string with all fields")
@click.option("--name", help="Project name")
@click.option("--identifier", help="Project identifier")
@click.option("--description", help="Project description")
@click.option("--is-public", type=bool, help="Public project")
@click.option("--inherit-members", type=bool, help="Inherit members")
@click.option("--parent-id", type=int, help="Parent project ID")
@click.option("--tracker-ids", help="Comma-separated tracker IDs")
@click.pass_context
@handle_errors
def project_create(
    ctx,
    json_data,
    name,
    identifier,
    description,
    is_public,
    inherit_members,
    parent_id,
    tracker_ids,
):
    """Create a new project."""
    rm = get_redmine(ctx)
    if json_data:
        fields = parse_json_input(json_data)
    else:
        fields = build_fields(
            name=name,
            identifier=identifier,
            description=description,
            is_public=is_public,
            inherit_members=inherit_members,
            parent_id=parent_id,
        )
        if tracker_ids:
            fields["tracker_ids"] = [int(x) for x in tracker_ids.split(",")]

    result = rm.project.create(**fields)
    emit(result.raw())


@project_group.command("update")
@click.argument("project_id")
@click.option("--json", "json_data", help="JSON string with fields to update")
@click.option("--name", help="New name")
@click.option("--description", help="New description")
@click.option("--is-public", type=bool, help="Public project")
@click.option("--parent-id", type=int, help="New parent project ID")
@click.pass_context
@handle_errors
def project_update(ctx, project_id, json_data, name, description, is_public, parent_id):
    """Update an existing project."""
    rm = get_redmine(ctx)
    try:
        pid = int(project_id)
    except ValueError:
        pid = project_id
    if json_data:
        fields = parse_json_input(json_data)
    else:
        fields = build_fields(
            name=name,
            description=description,
            is_public=is_public,
            parent_id=parent_id,
        )

    rm.project.update(pid, **fields)
    emit({"updated": True, "project_id": project_id})


@project_group.command("delete")
@click.argument("project_id")
@click.pass_context
@handle_errors
def project_delete(ctx, project_id):
    """Delete a project."""
    rm = get_redmine(ctx)
    try:
        pid = int(project_id)
    except ValueError:
        pid = project_id
    rm.project.delete(pid)
    emit({"deleted": True, "project_id": project_id})


@project_group.command("close")
@click.argument("project_id")
@click.pass_context
@handle_errors
def project_close(ctx, project_id):
    """Close a project (Redmine >= 5.0)."""
    rm = get_redmine(ctx)
    try:
        pid = int(project_id)
    except ValueError:
        pid = project_id
    rm.project.close(pid)
    emit({"closed": True, "project_id": project_id})


@project_group.command("reopen")
@click.argument("project_id")
@click.pass_context
@handle_errors
def project_reopen(ctx, project_id):
    """Reopen a project (Redmine >= 5.0)."""
    rm = get_redmine(ctx)
    try:
        pid = int(project_id)
    except ValueError:
        pid = project_id
    rm.project.reopen(pid)
    emit({"reopened": True, "project_id": project_id})


@project_group.command("archive")
@click.argument("project_id")
@click.pass_context
@handle_errors
def project_archive(ctx, project_id):
    """Archive a project (Redmine >= 5.0)."""
    rm = get_redmine(ctx)
    try:
        pid = int(project_id)
    except ValueError:
        pid = project_id
    rm.project.archive(pid)
    emit({"archived": True, "project_id": project_id})


@project_group.command("unarchive")
@click.argument("project_id")
@click.pass_context
@handle_errors
def project_unarchive(ctx, project_id):
    """Unarchive a project (Redmine >= 5.0)."""
    rm = get_redmine(ctx)
    try:
        pid = int(project_id)
    except ValueError:
        pid = project_id
    rm.project.unarchive(pid)
    emit({"unarchived": True, "project_id": project_id})
