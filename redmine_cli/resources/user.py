"""User subcommands for redmine-cli."""

import click

from ..output import emit, handle_errors, emit_dry_run
from ..utils import parse_json_input, resourceset_to_list, build_fields
from ..context import get_redmine, resolve_ref, build_dry_run_url, DRY_RUN_METHODS


@click.group("user")
@click.pass_context
def user_group(ctx):
    """User operations: CRUD with current-user support.

    \b
    Resource arguments (USER_REF) accept:
      - Integer ID or 'current' (requires -p):  redmine-cli -p prod user get 5
      - Full URL (auto-detects profile):        redmine-cli user get https://prod.example.com/users/5
    """
    pass


@user_group.command("get")
@click.argument("user_ref")
@click.option(
    "--include",
    "-i",
    "includes",
    help="Comma-separated related data: memberships,groups",
)
@click.option(
    "--fields",
    help="Comma-separated fields to include in output (e.g. id,login,firstname,lastname). Reduces output size for agents.",
)
@click.pass_context
@handle_errors
def user_get(ctx, user_ref, includes, fields):
    """Get a single user by ID, 'current', or URL.

    \b
    USER_REF accepts:
      - Integer ID or 'current' (requires -p):  redmine-cli -p prod user get 5
      - Full URL (auto-detect):                 redmine-cli user get https://prod.example.com/users/5

    \b
    Examples:
      redmine-cli -p redminex user get 5
      redmine-cli -p redminex user get current
      redmine-cli user get https://redminex.silksoftware.com/users/5
      redmine-cli -p redminex user get current -i memberships,groups
      redmine-cli -p redminex user get 5 --fields id,login,firstname,lastname
    """
    uid = resolve_ref(ctx, user_ref)
    rm = get_redmine(ctx)
    kwargs = {}
    if includes:
        kwargs["include"] = includes.split(",")
    if uid == "current":
        result = rm.user.get("current", **kwargs)
    else:
        result = rm.user.get(int(uid), **kwargs)
    emit(result.raw(), fields=fields.split(",") if fields else None)


@user_group.command("list")
@click.option(
    "--status", type=int, help="Filter by status: 1=active, 2=registered, 3=locked"
)
@click.option("--name", help="Filter by login, firstname, lastname, or email")
@click.option("--group-id", type=int, help="Filter by group ID")
@click.option("--limit", "-l", type=int, default=0, help="Max results (0=no limit)")
@click.option("--offset", type=int, default=0, help="Result offset for pagination")
@click.option(
    "--fields",
    help="Comma-separated fields to include in output (e.g. id,login,firstname,lastname). Reduces output size.",
)
@click.pass_context
@handle_errors
def user_list(ctx, status, name, group_id, limit, offset, fields):
    """List users with optional filters and pagination.

    \b
    Examples:
      redmine-cli -p redminex user list
      redmine-cli -p redminex user list --status 1 --limit 10
    """
    rm = get_redmine(ctx)
    kwargs = {}
    if status is not None:
        kwargs["status"] = status
    if name:
        kwargs["name"] = name
    if group_id:
        kwargs["group_id"] = group_id

    if kwargs:
        rs = rm.user.filter(**kwargs)
    else:
        rs = rm.user.all()

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


@user_group.command("create")
@click.option("--json", "json_data", help="JSON string with all fields")
@click.option("--login", help="Username")
@click.option("--firstname", help="First name")
@click.option("--lastname", help="Last name")
@click.option("--mail", help="Email address")
@click.option("--password", help="Password")
@click.option("--auth-source-id", type=int, help="Auth source ID")
@click.option("--must-change-password", is_flag=True, help="Force password change")
@click.option("--generate-password", is_flag=True, help="Generate random password")
@click.option("--send-information", is_flag=True, help="Send account info email")
@click.pass_context
@handle_errors
def user_create(
    ctx,
    json_data,
    login,
    firstname,
    lastname,
    mail,
    password,
    auth_source_id,
    must_change_password,
    generate_password,
    send_information,
):
    """Create a new user. Login, firstname, lastname, mail and password are typically required.

    \b
    Examples:
      redmine-cli -p redminex user create --login admin --firstname Admin --lastname User --mail admin@test.com
    """
    rm = get_redmine(ctx)
    if json_data:
        fields = parse_json_input(json_data)
    else:
        fields = build_fields(
            login=login,
            firstname=firstname,
            lastname=lastname,
            mail=mail,
            password=password,
            auth_source_id=auth_source_id,
        )
        if must_change_password:
            fields["must_change_passwd"] = True
        if generate_password:
            fields["generate_password"] = True
        if send_information:
            fields["send_information"] = True

    if ctx.obj.get("_dry_run"):
        url = build_dry_run_url(rm.url, "user", "create")
        emit_dry_run("create", "user", DRY_RUN_METHODS["create"], url, payload=fields)
        return

    result = rm.user.create(**fields)
    emit(result.raw())


@user_group.command("update")
@click.argument("user_ref")
@click.option("--json", "json_data", help="JSON string with fields to update")
@click.option("--firstname", help="New first name")
@click.option("--lastname", help="New last name")
@click.option("--mail", help="New email")
@click.option("--password", help="New password")
@click.option("--must-change-password", is_flag=True)
@click.pass_context
@handle_errors
def user_update(
    ctx, user_ref, json_data, firstname, lastname, mail, password, must_change_password
):
    """Update an existing user's fields.

    \b
    USER_REF accepts an integer ID (requires -p) or a full Redmine URL.

    \b
    Examples:
      redmine-cli -p redminex user update 5 --firstname "New Name"
      redmine-cli user update https://redminex.silksoftware.com/users/5 --firstname "New Name"
    """
    uid = resolve_ref(ctx, user_ref)
    rm = get_redmine(ctx)
    if json_data:
        fields = parse_json_input(json_data)
    else:
        fields = build_fields(
            firstname=firstname,
            lastname=lastname,
            mail=mail,
            password=password,
        )
        if must_change_password:
            fields["must_change_passwd"] = True

    if ctx.obj.get("_dry_run"):
        url = build_dry_run_url(rm.url, "user", "update", id=uid)
        emit_dry_run("update", "user", DRY_RUN_METHODS["update"], url, payload=fields)
        return

    rm.user.update(int(uid), **fields)
    emit({"updated": True, "resource": "user", "id": uid})


@user_group.command("delete")
@click.argument("user_ref")
@click.pass_context
@handle_errors
def user_delete(ctx, user_ref):
    """Delete a user permanently.

    \b
    USER_REF accepts an integer ID (requires -p) or a full Redmine URL.

    \b
    Examples:
      redmine-cli -p redminex user delete 5
      redmine-cli user delete https://redminex.silksoftware.com/users/5
    """
    uid = resolve_ref(ctx, user_ref)
    rm = get_redmine(ctx)
    if ctx.obj.get("_dry_run"):
        url = build_dry_run_url(rm.url, "user", "delete", id=uid)
        emit_dry_run("delete", "user", DRY_RUN_METHODS["delete"], url)
        return
    rm.user.delete(int(uid))
    emit({"deleted": True, "resource": "user", "id": uid})


@user_group.command("fields")
@click.pass_context
@handle_errors
def user_fields(ctx):
    """Show available fields for the user resource type.

    \b
    Example:
      redmine-cli user fields
    """
    from ..fields import get_resource_fields

    emit(get_resource_fields("user"))


@user_group.command("schema")
@click.pass_context
@handle_errors
def user_schema(ctx):
    """Show creation schema for users.

    Returns required fields, optional fields, read-only fields, and ID fields.

    \b
    Example:
      redmine-cli user schema
    """
    from ..schema import get_resource_schema

    emit(get_resource_schema("user"))
