"""Project subcommands for redmine-cli."""

import click

from ..output import emit, handle_errors
from ..utils import parse_json_input, resourceset_to_list, build_fields
from ..context import get_redmine, resolve_ref


@click.group("project")
@click.pass_context
def project_group(ctx):
    """Project operations: CRUD with lifecycle management.

    \b
    Resource arguments (PROJECT_REF) accept:
      - Integer ID or identifier (requires -p): redmine-cli -p prod project get my-project
      - Full URL (auto-detects profile): redmine-cli project get https://prod.example.com/projects/my-project
    """
    pass


@project_group.command("get")
@click.argument("project_ref")
@click.pass_context
@handle_errors
def project_get(ctx, project_ref):
    """Get a single project by ID, identifier, or URL.

    \b
    PROJECT_REF accepts:
      - Integer ID or identifier (requires -p):  redmine-cli -p prod project get my-project
      - Full URL (auto-detect):                  redmine-cli project get https://prod.example.com/projects/my-project

    \b
    Examples:
      redmine-cli -p redminex project get 1
      redmine-cli -p redminex project get my-project-identifier
      redmine-cli project get https://redminex.silksoftware.com/projects/my-project
    """
    pid = resolve_ref(ctx, project_ref)
    rm = get_redmine(ctx)
    result = rm.project.get(pid)
    emit(result.raw())


@project_group.command("list")
@click.option("--limit", "-l", type=int, default=0, help="Max results (0=no limit)")
@click.option("--offset", type=int, default=0, help="Result offset for pagination")
@click.option(
    "--include",
    "-i",
    "includes",
    help="Comma-separated: trackers,issue_categories,enabled_modules,time_entry_activities",
)
@click.option(
    "--fields",
    help="Comma-separated fields to include in output (e.g. id,name,identifier). Reduces output size.",
)
@click.pass_context
@handle_errors
def project_list(ctx, limit, offset, includes, fields):
    """List all projects.

    \b
    Use -i to include related data (trackers, issue_categories, enabled_modules, etc.).
    Supports pagination with --limit and --offset.

    \b
    Examples:
      redmine-cli -p redminex project list
      redmine-cli -p redminex project list -i trackers,issue_categories
    """
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
    emit(
        data,
        total_count=rs.total_count,
        limit=limit,
        offset=offset,
        fields=fields.split(",") if fields else None,
    )


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
    """Create a new project.

    \b
    Name and identifier are required. Use --json to pass all fields at once.

    \b
    Examples:
      redmine-cli -p redminex project create --name "Test" --identifier test
      redmine-cli -p redminex project create --json '{"name":"Test","identifier":"test"}'
    """
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
@click.argument("project_ref")
@click.option("--json", "json_data", help="JSON string with fields to update")
@click.option("--name", help="New name")
@click.option("--description", help="New description")
@click.option("--is-public", type=bool, help="Public project")
@click.option("--parent-id", type=int, help="New parent project ID")
@click.pass_context
@handle_errors
def project_update(ctx, project_ref, json_data, name, description, is_public, parent_id):
    """Update an existing project's fields.

    \b
    PROJECT_REF accepts an integer ID, string identifier (requires -p),
    or a full Redmine URL.

    \b
    Examples:
      redmine-cli -p redminex project update my-project --name "New Name"
      redmine-cli project update https://redminex.silksoftware.com/projects/my-project --name "New Name"
    """
    pid = resolve_ref(ctx, project_ref)
    rm = get_redmine(ctx)
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
    emit({"updated": True, "project_id": pid})


@project_group.command("delete")
@click.argument("project_ref")
@click.pass_context
@handle_errors
def project_delete(ctx, project_ref):
    """Delete a project permanently. This action cannot be undone.

    \b
    PROJECT_REF accepts an integer ID, string identifier (requires -p),
    or a full Redmine URL.

    \b
    Examples:
      redmine-cli -p redminex project delete my-project
      redmine-cli project delete https://redminex.silksoftware.com/projects/my-project
    """
    pid = resolve_ref(ctx, project_ref)
    rm = get_redmine(ctx)
    rm.project.delete(pid)
    emit({"deleted": True, "project_id": pid})


@project_group.command("close")
@click.argument("project_ref")
@click.pass_context
@handle_errors
def project_close(ctx, project_ref):
    """Close a project (Redmine >= 5.0).

    \b
    PROJECT_REF accepts an integer ID, string identifier (requires -p),
    or a full Redmine URL.

    \b
    Examples:
      redmine-cli -p redminex project close my-project
      redmine-cli project close https://redminex.silksoftware.com/projects/my-project
    """
    pid = resolve_ref(ctx, project_ref)
    rm = get_redmine(ctx)
    rm.project.close(pid)
    emit({"closed": True, "project_id": pid})


@project_group.command("reopen")
@click.argument("project_ref")
@click.pass_context
@handle_errors
def project_reopen(ctx, project_ref):
    """Reopen a project (Redmine >= 5.0).

    \b
    PROJECT_REF accepts an integer ID, string identifier (requires -p),
    or a full Redmine URL.

    \b
    Examples:
      redmine-cli -p redminex project reopen my-project
      redmine-cli project reopen https://redminex.silksoftware.com/projects/my-project
    """
    pid = resolve_ref(ctx, project_ref)
    rm = get_redmine(ctx)
    rm.project.reopen(pid)
    emit({"reopened": True, "project_id": pid})


@project_group.command("archive")
@click.argument("project_ref")
@click.pass_context
@handle_errors
def project_archive(ctx, project_ref):
    """Archive a project (Redmine >= 5.0).

    \b
    PROJECT_REF accepts an integer ID, string identifier (requires -p),
    or a full Redmine URL.

    \b
    Examples:
      redmine-cli -p redminex project archive my-project
      redmine-cli project archive https://redminex.silksoftware.com/projects/my-project
    """
    pid = resolve_ref(ctx, project_ref)
    rm = get_redmine(ctx)
    rm.project.archive(pid)
    emit({"archived": True, "project_id": pid})


@project_group.command("unarchive")
@click.argument("project_ref")
@click.pass_context
@handle_errors
def project_unarchive(ctx, project_ref):
    """Unarchive a project (Redmine >= 5.0).

    \b
    PROJECT_REF accepts an integer ID, string identifier (requires -p),
    or a full Redmine URL.

    \b
    Examples:
      redmine-cli -p redminex project unarchive my-project
      redmine-cli project unarchive https://redminex.silksoftware.com/projects/my-project
    """
    pid = resolve_ref(ctx, project_ref)
    rm = get_redmine(ctx)
    rm.project.unarchive(pid)
    emit({"unarchived": True, "project_id": pid})
