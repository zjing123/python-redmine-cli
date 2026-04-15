"""Issue subcommands for redmine-cli."""

import click

from ..output import emit, handle_errors
from ..utils import parse_json_input, resourceset_to_list, build_fields
from ..context import get_redmine
from ..config import create_redmine, list_profiles, load_config_file


@click.group("issue")
@click.pass_context
def issue_group(ctx):
    """Issue operations."""
    pass


@issue_group.command("get")
@click.argument("issue_id", type=int)
@click.option(
    "--include",
    "-i",
    "includes",
    help="Comma-separated: children,attachments,relations,journals,watchers,changesets",
)
@click.pass_context
@handle_errors
def issue_get(ctx, issue_id, includes):
    """Get a single issue by ID."""
    rm = get_redmine(ctx)
    kwargs = {}
    if includes:
        kwargs["include"] = includes.split(",")
    result = rm.issue.get(issue_id, **kwargs)
    emit(result.raw())


@issue_group.command("list")
@click.option("--project-id", type=int, help="Filter by project ID")
@click.option("--status-id", help="Filter by status: open, closed, *, or numeric ID")
@click.option("--assigned-to-id", type=int, help="Filter by assignee user ID")
@click.option(
    "--assigned-to-me", is_flag=True, help="Shortcut for --assigned-to-id=current user"
)
@click.option(
    "--all-profiles",
    is_flag=True,
    help="Query all configured profiles and merge results",
)
@click.option("--tracker-id", type=int, help="Filter by tracker ID")
@click.option("--priority-id", type=int, help="Filter by priority ID")
@click.option("--author-id", type=int, help="Filter by author user ID")
@click.option("--category-id", type=int, help="Filter by category ID")
@click.option("--fixed-version-id", type=int, help="Filter by target version ID")
@click.option("--parent-id", type=int, help="Filter by parent issue ID")
@click.option("--query-id", type=int, help="Use a saved query")
@click.option("--sort", help="Sort expression, e.g. updated_on:desc")
@click.option("--limit", "-l", type=int, default=0, help="Max results (0=all)")
@click.option("--offset", type=int, default=0, help="Result offset")
@click.option(
    "--include", "-i", "includes", help="Comma-separated relations to include"
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
):
    """List issues with optional filters.

    Use --all-profiles to query all configured Redmine instances at once.
    """
    filter_kwargs = {}
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
        _issue_list_all_profiles(ctx, assigned_to_me, filter_kwargs, limit, offset)
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
    emit(data, total_count=rs.total_count, limit=limit, offset=offset)


def _issue_list_all_profiles(ctx, assigned_to_me, filter_kwargs, limit, offset):
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

    emit(all_issues, total_count=len(all_issues), limit=limit, offset=offset)


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
    """Create a new issue."""
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

    result = rm.issue.create(**fields)
    emit(result.raw())


@issue_group.command("update")
@click.argument("issue_id", type=int)
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
    issue_id,
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
    """Update an existing issue."""
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

    rm.issue.update(issue_id, **fields)
    emit({"updated": True, "issue_id": issue_id})


@issue_group.command("delete")
@click.argument("issue_id", type=int)
@click.pass_context
@handle_errors
def issue_delete(ctx, issue_id):
    """Delete an issue."""
    rm = get_redmine(ctx)
    rm.issue.delete(issue_id)
    emit({"deleted": True, "issue_id": issue_id})


@issue_group.command("add-watcher")
@click.argument("issue_id", type=int)
@click.option("--user-id", required=True, type=int, help="User ID to add as watcher")
@click.pass_context
@handle_errors
def issue_add_watcher(ctx, issue_id, user_id):
    """Add a watcher to an issue."""
    rm = get_redmine(ctx)
    issue = rm.issue.get(issue_id)
    issue.watcher.add(user_id)
    emit({"ok": True, "issue_id": issue_id, "watcher_added": user_id})


@issue_group.command("remove-watcher")
@click.argument("issue_id", type=int)
@click.option("--user-id", required=True, type=int, help="User ID to remove")
@click.pass_context
@handle_errors
def issue_remove_watcher(ctx, issue_id, user_id):
    """Remove a watcher from an issue."""
    rm = get_redmine(ctx)
    issue = rm.issue.get(issue_id)
    issue.watcher.remove(user_id)
    emit({"ok": True, "issue_id": issue_id, "watcher_removed": user_id})


@issue_group.command("copy")
@click.argument("issue_id", type=int)
@click.option("--project-id", type=int, help="Target project ID")
@click.option(
    "--link-original/--no-link-original", default=True, help="Link to original"
)
@click.option("--include", "includes", help="Comma-separated: subtasks,attachments")
@click.pass_context
@handle_errors
def issue_copy(ctx, issue_id, project_id, link_original, includes):
    """Copy an issue to another project."""
    rm = get_redmine(ctx)
    kwargs = {}
    if project_id:
        kwargs["project_id"] = project_id
    inc = tuple(includes.split(",")) if includes else ()
    result = rm.issue.get(issue_id).copy(
        link_original=link_original, include=inc, **kwargs
    )
    emit(result.raw())
