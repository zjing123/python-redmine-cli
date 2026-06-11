"""Issue subcommands for redmine-cli."""

import click

from ..output import emit, handle_errors, emit_dry_run
from ..utils import parse_json_input, resourceset_to_list, build_fields
from ..context import get_redmine, resolve_ref, build_dry_run_url, DRY_RUN_METHODS
from ..config import create_redmine, list_profiles, load_config_file


@click.group("issue")
@click.pass_context
def issue_group(ctx):
    """Issue operations: CRUD, watchers, copy, with filters and multi-profile support.

    \b
    Resource arguments (ISSUE_REF) accept:
      - Integer ID (requires -p or REDMINE_URL): redmine-cli -p prod issue get 123
      - Full URL (auto-detects profile): redmine-cli issue get https://prod.example.com/issues/123
    """
    pass


@issue_group.command("get")
@click.argument("issue_ref")
@click.option(
    "--include",
    "-i",
    "includes",
    help="Comma-separated related data to include: children,attachments,relations,journals,watchers,changesets",
)
@click.option(
    "--fields",
    help="Comma-separated fields to include in output (e.g. id,subject,status). Reduces output size for agents.",
)
@click.pass_context
@handle_errors
def issue_get(ctx, issue_ref, includes, fields):
    """Get a single issue by ID or URL.

    \b
    ISSUE_REF accepts:
      - Integer ID (requires -p):  redmine-cli -p prod issue get 123
      - Full URL (auto-detect):    redmine-cli issue get https://prod.example.com/issues/123

    \b
    Examples:
      redmine-cli -p redminex issue get 123
      redmine-cli issue get https://redminex.silksoftware.com/issues/123
      redmine-cli -p redminex issue get 123 -i journals,attachments,relations
      redmine-cli -p redminex issue get 123 --fields id,subject,status
    """
    issue_id = resolve_ref(ctx, issue_ref)
    rm = get_redmine(ctx)
    kwargs = {}
    if includes:
        kwargs["include"] = includes.split(",")
    result = rm.issue.get(issue_id, **kwargs)
    emit(result.raw(), fields=fields.split(",") if fields else None)


@issue_group.command("list")
@click.option("--project-id", type=int, help="Filter by project ID")
@click.option(
    "--status",
    "status_id",
    help="Filter by status: open, closed, * (all), or a numeric status ID",
)
@click.option("--assigned-to-id", type=int, help="Filter by assignee user ID")
@click.option(
    "--assigned-to-me",
    is_flag=True,
    help="Shortcut: filter issues assigned to the current authenticated user",
)
@click.option(
    "--all-profiles",
    is_flag=True,
    help="Query ALL configured profiles and merge results (adds _profile and _source_url fields)",
)
@click.option("--tracker-id", type=int, help="Filter by tracker ID")
@click.option("--priority-id", type=int, help="Filter by priority ID")
@click.option("--author-id", type=int, help="Filter by author user ID")
@click.option("--category-id", type=int, help="Filter by category ID")
@click.option("--fixed-version-id", type=int, help="Filter by target version ID")
@click.option("--parent-id", type=int, help="Filter by parent issue ID")
@click.option("--query-id", type=int, help="Use a saved Redmine query by ID")
@click.option("--sort", help="Sort expression, e.g. updated_on:desc or priority:asc")
@click.option("--limit", "-l", type=int, default=0, help="Max results (0=no limit)")
@click.option("--offset", type=int, default=0, help="Result offset for pagination")
@click.option(
    "--include",
    "-i",
    "includes",
    help="Comma-separated related data to include: children,attachments,relations,etc.",
)
@click.option(
    "--fields",
    help="Comma-separated fields to include in output (e.g. id,subject,status). Reduces output size for agents.",
)
@click.pass_context
@handle_errors
def issue_list(
    ctx,
    project_id,
    status_id,
    assigned_to_id,
    assigned_to_me,
    all_profiles,
    tracker_id,
    priority_id,
    author_id,
    category_id,
    fixed_version_id,
    parent_id,
    query_id,
    sort,
    limit,
    offset,
    includes,
    fields,
):
    """List issues with optional filters.

    \b
    Supports pagination (--limit, --offset), sorting (--sort), and many
    filter options. Use --assigned-to-me as a shortcut for current user's
    issues. Use --all-profiles to query all configured Redmine instances
    at once (results include _profile and _source_url fields).

    \b
    Examples:
      redmine-cli -p redminex issue list
      redmine-cli -p redminex issue list --assigned-to-me --status open
      redmine-cli -p redminex issue list --project-id 1 --status closed --limit 10
      redmine-cli issue list --assigned-to-me --all-profiles
      redmine-cli -p redminex issue list --sort updated_on:desc --limit 5
      redmine-cli -p redminex issue list --fields id,subject,status --limit 50
    """
    filter_kwargs = {}
    field_list = fields.split(",") if fields else None
    for key, val in [
        ("project_id", project_id),
        ("status_id", status_id),
        ("assigned_to_id", assigned_to_id),
        ("tracker_id", tracker_id),
        ("priority_id", priority_id),
        ("author_id", author_id),
        ("category_id", category_id),
        ("fixed_version_id", fixed_version_id),
        ("parent_id", parent_id),
        ("query_id", query_id),
        ("sort", sort),
    ]:
        if val is not None:
            filter_kwargs[key] = val
    if includes:
        filter_kwargs["include"] = includes.split(",")

    if all_profiles:
        _issue_list_all_profiles(
            ctx, assigned_to_me, filter_kwargs, limit, offset, field_list
        )
        return

    rm = get_redmine(ctx)
    if assigned_to_me:
        filter_kwargs["assigned_to_id"] = rm.auth().id

    if filter_kwargs:
        rs = rm.issue.filter(**filter_kwargs)
    else:
        rs = rm.issue.all()

    if limit:
        rs = rs[offset : offset + limit] if offset else rs[:limit]
    elif offset:
        rs = rs[offset:]

    data = resourceset_to_list(rs)
    emit(
        data, total_count=rs.total_count, limit=limit, offset=offset, fields=field_list
    )


def _issue_list_all_profiles(
    ctx, assigned_to_me, filter_kwargs, limit, offset, fields=None
):
    """Query issues from all profiles and merge results."""
    data = load_config_file()
    profiles_config = data.get("profiles", {})
    default_config = data.get("default", {})

    targets = {}
    if default_config:
        targets["default"] = default_config
    targets.update(profiles_config)

    all_issues = []
    per_profile = {}

    for profile_name, profile_conf in targets.items():
        try:
            if "api_key" in profile_conf:
                profile_conf["key"] = profile_conf.pop("api_key")
            rm = create_redmine(**profile_conf)
            local_kwargs = dict(filter_kwargs)
            if assigned_to_me:
                local_kwargs["assigned_to_id"] = rm.auth().id
            if local_kwargs:
                rs = rm.issue.filter(**local_kwargs)
            else:
                rs = rm.issue.all()
            issues = resourceset_to_list(rs)
            for issue in issues:
                issue["_profile"] = profile_name
                issue["_source_url"] = rm.url
            all_issues.extend(issues)
            per_profile[profile_name] = {
                "url": rm.url,
                "count": rs.total_count,
            }
        except Exception as e:
            per_profile[profile_name] = {"error": str(e)}

    emit(
        all_issues,
        total_count=len(all_issues),
        limit=limit,
        offset=offset,
        fields=fields,
    )


@issue_group.command("create")
@click.option("--json", "json_data", help="JSON string with all fields")
@click.option("--project-id", type=int, help="Project ID (required)")
@click.option("--subject", help="Issue subject")
@click.option("--description", help="Issue description")
@click.option("--tracker-id", type=int, help="Tracker ID")
@click.option("--status-id", type=int, help="Status ID")
@click.option("--priority-id", type=int, help="Priority ID")
@click.option("--assigned-to-id", type=int, help="Assignee user ID")
@click.option("--parent-issue-id", type=int, help="Parent issue ID")
@click.option("--fixed-version-id", type=int, help="Target version ID")
@click.option("--custom-fields", help="JSON array of custom fields")
@click.option("--watcher-user-ids", help="Comma-separated watcher user IDs")
@click.pass_context
@handle_errors
def issue_create(
    ctx,
    json_data,
    project_id,
    subject,
    description,
    tracker_id,
    status_id,
    priority_id,
    assigned_to_id,
    parent_issue_id,
    fixed_version_id,
    custom_fields,
    watcher_user_ids,
):
    """Create a new issue.

    \b
    Either use individual flags (--project-id, --subject, etc.) or --json
    to pass all fields at once. --project-id and --subject are the minimum
    required fields. Custom fields can be passed via --custom-fields as JSON.

    \b
    Examples:
      redmine-cli -p redminex issue create --project-id 1 --subject "Bug report"
      redmine-cli -p redminex issue create --project-id 1 --subject "Feature" --tracker-id 2
      redmine-cli -p redminex issue create --json '{"project_id":1,"subject":"Title"}'
    """
    rm = get_redmine(ctx)
    if json_data:
        fields = parse_json_input(json_data)
    else:
        fields = build_fields(
            project_id=project_id,
            subject=subject,
            description=description,
            tracker_id=tracker_id,
            status_id=status_id,
            priority_id=priority_id,
            assigned_to_id=assigned_to_id,
            parent_issue_id=parent_issue_id,
            fixed_version_id=fixed_version_id,
        )
        if custom_fields:
            fields["custom_fields"] = parse_json_input(custom_fields)
        if watcher_user_ids:
            fields["watcher_user_ids"] = [int(x) for x in watcher_user_ids.split(",")]

    if ctx.obj.get("_dry_run"):
        url = build_dry_run_url(rm.url, "issue", "create")
        emit_dry_run("create", "issue", DRY_RUN_METHODS["create"], url, payload=fields)
        return

    result = rm.issue.create(**fields)
    emit(result.raw())


@issue_group.command("update")
@click.argument("issue_ref")
@click.option("--json", "json_data", help="JSON string with fields to update")
@click.option("--subject", help="New subject")
@click.option("--description", help="New description")
@click.option("--status-id", type=int, help="New status ID")
@click.option("--assigned-to-id", type=int, help="New assignee user ID")
@click.option("--priority-id", type=int, help="New priority ID")
@click.option("--fixed-version-id", type=int, help="New target version ID")
@click.option("--notes", help="Add a note/comment with the update")
@click.option("--custom-fields", help="JSON array of custom fields")
@click.option("--private-notes", is_flag=True, help="Mark notes as private")
@click.pass_context
@handle_errors
def issue_update(
    ctx,
    issue_ref,
    json_data,
    subject,
    description,
    status_id,
    assigned_to_id,
    priority_id,
    fixed_version_id,
    notes,
    custom_fields,
    private_notes,
):
    """Update an existing issue.

    \b
    ISSUE_REF accepts an integer ID (requires -p) or a full Redmine URL.
    Only the fields you specify will be updated. Use --notes to add a comment.

    \b
    Examples:
      redmine-cli -p redminex issue update 123 --status-id 3 --notes "Fixed"
      redmine-cli issue update https://redminex.silksoftware.com/issues/123 --status-id 3
      redmine-cli -p redminex issue update 123 --json '{"status_id":3,"notes":"Bulk update"}'
    """
    issue_id = resolve_ref(ctx, issue_ref)
    rm = get_redmine(ctx)
    if json_data:
        fields = parse_json_input(json_data)
    else:
        fields = build_fields(
            subject=subject,
            description=description,
            status_id=status_id,
            assigned_to_id=assigned_to_id,
            priority_id=priority_id,
            fixed_version_id=fixed_version_id,
            notes=notes,
        )
        if custom_fields:
            fields["custom_fields"] = parse_json_input(custom_fields)
        if private_notes:
            fields["private_notes"] = True

    if ctx.obj.get("_dry_run"):
        url = build_dry_run_url(rm.url, "issue", "update", id=issue_id)
        emit_dry_run("update", "issue", DRY_RUN_METHODS["update"], url, payload=fields)
        return

    rm.issue.update(issue_id, **fields)
    emit({"updated": True, "resource": "issue", "id": issue_id})


@issue_group.command("delete")
@click.argument("issue_ref")
@click.pass_context
@handle_errors
def issue_delete(ctx, issue_ref):
    """Delete an issue permanently. This action cannot be undone.

    \b
    ISSUE_REF accepts an integer ID (requires -p) or a full Redmine URL.

    \b
    Examples:
      redmine-cli -p redminex issue delete 123
      redmine-cli issue delete https://redminex.silksoftware.com/issues/123
    """
    issue_id = resolve_ref(ctx, issue_ref)
    rm = get_redmine(ctx)
    if ctx.obj.get("_dry_run"):
        url = build_dry_run_url(rm.url, "issue", "delete", id=issue_id)
        emit_dry_run("delete", "issue", DRY_RUN_METHODS["delete"], url)
        return
    rm.issue.delete(issue_id)
    emit({"deleted": True, "resource": "issue", "id": issue_id})


@issue_group.command("add-watcher")
@click.argument("issue_ref")
@click.option("--user-id", required=True, type=int, help="User ID to add as watcher")
@click.pass_context
@handle_errors
def issue_add_watcher(ctx, issue_ref, user_id):
    """Add a watcher to an issue. The user will receive notifications for changes.

    \b
    ISSUE_REF accepts an integer ID (requires -p) or a full Redmine URL.

    \b
    Examples:
      redmine-cli -p redminex issue add-watcher 123 --user-id 5
      redmine-cli issue add-watcher https://redminex.silksoftware.com/issues/123 --user-id 5
    """
    issue_id = resolve_ref(ctx, issue_ref)
    rm = get_redmine(ctx)
    if ctx.obj.get("_dry_run"):
        url = build_dry_run_url(rm.url, "issue", "add_watcher", id=issue_id)
        emit_dry_run("add_watcher", "issue", DRY_RUN_METHODS["add_watcher"], url, payload={"user_id": user_id})
        return
    issue = rm.issue.get(issue_id)
    issue.watcher.add(user_id)
    emit({"resource": "issue", "id": issue_id, "watcher_added": user_id})


@issue_group.command("remove-watcher")
@click.argument("issue_ref")
@click.option("--user-id", required=True, type=int, help="User ID to remove")
@click.pass_context
@handle_errors
def issue_remove_watcher(ctx, issue_ref, user_id):
    """Remove a watcher from an issue. The user will stop receiving notifications.

    \b
    ISSUE_REF accepts an integer ID (requires -p) or a full Redmine URL.

    \b
    Examples:
      redmine-cli -p redminex issue remove-watcher 123 --user-id 5
      redmine-cli issue remove-watcher https://redminex.silksoftware.com/issues/123 --user-id 5
    """
    issue_id = resolve_ref(ctx, issue_ref)
    rm = get_redmine(ctx)
    if ctx.obj.get("_dry_run"):
        url = build_dry_run_url(rm.url, "issue", "remove_watcher", id=issue_id, user_id=user_id)
        emit_dry_run("remove_watcher", "issue", DRY_RUN_METHODS["remove_watcher"], url)
        return
    issue = rm.issue.get(issue_id)
    issue.watcher.remove(user_id)
    emit({"resource": "issue", "id": issue_id, "watcher_removed": user_id})


@issue_group.command("copy")
@click.argument("issue_ref")
@click.option("--project-id", type=int, help="Target project ID")
@click.option(
    "--link-original/--no-link-original", default=True, help="Link to original"
)
@click.option("--include", "includes", help="Comma-separated: subtasks,attachments")
@click.pass_context
@handle_errors
def issue_copy(ctx, issue_ref, project_id, link_original, includes):
    """Copy an issue to another project.

    \b
    ISSUE_REF accepts an integer ID (requires -p) or a full Redmine URL.
    By default links the copy to the original issue. Use --no-link-original to skip.
    Use --include to copy subtasks and/or attachments.

    \b
    Examples:
      redmine-cli -p redminex issue copy 123 --project-id 2
      redmine-cli issue copy https://redminex.silksoftware.com/issues/123 --project-id 2
    """
    issue_id = resolve_ref(ctx, issue_ref)
    rm = get_redmine(ctx)
    kwargs = {}
    if project_id:
        kwargs["project_id"] = project_id
    inc = tuple(includes.split(",")) if includes else ()
    if ctx.obj.get("_dry_run"):
        url = build_dry_run_url(rm.url, "issue", "copy")
        copy_fields = {"copy_from": issue_id}
        if project_id:
            copy_fields["project_id"] = project_id
        if link_original:
            copy_fields["link_copy"] = True
        for i in inc or ("subtasks", "attachments"):
            copy_fields[f"copy_{i}"] = True
        emit_dry_run("copy", "issue", DRY_RUN_METHODS["copy"], url, payload=copy_fields)
        return
    result = rm.issue.get(issue_id).copy(
        link_original=link_original, include=inc, **kwargs
    )
    emit(result.raw())


@issue_group.command("fields")
@click.pass_context
@handle_errors
def issue_fields(ctx):
    """Show available fields for the issue resource type.

    Displays object fields, collection fields, includable fields,
    and ID fields that can be used with --fields on get/list commands.

    \b
    Example:
      redmine-cli issue fields
    """
    from ..fields import get_resource_fields

    emit(get_resource_fields("issue"))
