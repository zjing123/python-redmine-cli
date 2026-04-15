"""User subcommands for redmine-cli."""

import click

from ..output import emit, handle_errors
from ..utils import parse_json_input, resourceset_to_list, build_fields
from ..context import get_redmine


@click.group("user")
@click.pass_context
def user_group(ctx):
    """User operations."""
    pass


@user_group.command("get")
@click.argument("user_id")
@click.option("--include", "-i", "includes", help="Comma-separated: memberships,groups")
@click.pass_context
@handle_errors
def user_get(ctx, user_id, includes):
    """Get a single user by ID. Use 'current' for the authenticated user."""
    rm = get_redmine(ctx)
    kwargs = {}
    if includes:
        kwargs["include"] = includes.split(",")
    if user_id == "current":
        result = rm.user.get("current", **kwargs)
    else:
        result = rm.user.get(int(user_id), **kwargs)
    emit(result.raw())


@user_group.command("list")
@click.option(
    "--status", type=int, help="Filter by status (1=active, 2=registered, 3=locked)"
)
@click.option("--name", help="Filter by name")
@click.option("--group-id", type=int, help="Filter by group ID")
@click.option("--limit", "-l", type=int, default=0, help="Max results (0=all)")
@click.option("--offset", type=int, default=0, help="Result offset")
@click.pass_context
@handle_errors
def user_list(ctx, status, name, group_id, limit, offset):
    """List users."""
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
    emit(data, total_count=rs.total_count, limit=limit, offset=offset)


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
    """Create a new user."""
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

    result = rm.user.create(**fields)
    emit(result.raw())


@user_group.command("update")
@click.argument("user_id", type=int)
@click.option("--json", "json_data", help="JSON string with fields to update")
@click.option("--firstname", help="New first name")
@click.option("--lastname", help="New last name")
@click.option("--mail", help="New email")
@click.option("--password", help="New password")
@click.option("--must-change-password", is_flag=True)
@click.pass_context
@handle_errors
def user_update(
    ctx, user_id, json_data, firstname, lastname, mail, password, must_change_password
):
    """Update an existing user."""
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

    rm.user.update(user_id, **fields)
    emit({"updated": True, "user_id": user_id})


@user_group.command("delete")
@click.argument("user_id", type=int)
@click.pass_context
@handle_errors
def user_delete(ctx, user_id):
    """Delete a user."""
    rm = get_redmine(ctx)
    rm.user.delete(user_id)
    emit({"deleted": True, "user_id": user_id})
