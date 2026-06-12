"""Shared helpers for resource command modules.

These helpers collapse the repetition that was copy-pasted across every
resource command file (issue, project, generic, time_entry, user, wiki_page):

- slicing + emitting a ResourceSet with pagination metadata
- the dry-run guard around create/update/delete/...
- resolving mutation fields from --json/--stdin vs. individual CLI flags
- parsing the comma-separated --fields option

They depend only on utils / context / output, so there is no import cycle.
"""

from ..context import DRY_RUN_METHODS, build_dry_run_url
from ..output import emit, emit_dry_run
from ..utils import build_fields, resolve_json_data, resourceset_to_list


def slice_resourceset(rs, limit, fetch_all, offset):
    """Slice a ResourceSet by limit/offset, preserving the original total.

    Returns a tuple (sliced_rs, original_total_count). The total_count is
    captured before slicing so callers can emit accurate pagination metadata
    even after the set has been truncated.

    :param rs: A python-redmine ResourceSet (supports total_count + slicing).
    :param limit: Max number of items (ignored when fetch_all is True).
    :param fetch_all: When True, return the full set without applying limit.
    :param offset: Number of leading items to skip.
    """
    total_count = rs.total_count
    effective_limit = None if fetch_all else limit
    if effective_limit is not None:
        rs = rs[offset : offset + effective_limit] if offset else rs[:effective_limit]
    elif offset:
        rs = rs[offset:]
    return rs, total_count


def emit_resourceset(rs, *, limit, fetch_all, offset, fields=None, extra=None):
    """Slice, serialize, and emit a ResourceSet with pagination metadata.

    Convenience wrapper around slice_resourceset + resourceset_to_list + emit,
    producing the common list/filter shape:
    {"ok": true, "total_count", "limit", "offset", "data"}.
    """
    rs, total_count = slice_resourceset(rs, limit, fetch_all, offset)
    effective_limit = None if fetch_all else limit
    emit(
        resourceset_to_list(rs),
        total_count=total_count,
        limit=effective_limit,
        offset=offset,
        fields=fields,
        extra=extra,
    )


def emit_dry_run_mutation(ctx, base_url, resource_type, operation, payload=None, **url_kwargs):
    """Emit a dry-run mutation and return True when dry-run is active.

    Returns False otherwise, so callers can short-circuit with:
        if emit_dry_run_mutation(ctx, rm.url, "issue", "delete", id=issue_id):
            return

    :param ctx: Click context (ctx.obj must hold the '_dry_run' flag).
    :param base_url: Redmine server base URL.
    :param resource_type: e.g. 'issue', 'project'.
    :param operation: e.g. 'create', 'update', 'delete', 'add_watcher'.
    :param payload: Optional request body dict (sensitive keys auto-masked).
    :param url_kwargs: URL template vars (id, user_id, project_id, ...).
    """
    if not ctx.obj.get("_dry_run"):
        return False
    url = build_dry_run_url(base_url, resource_type, operation, **url_kwargs)
    emit_dry_run(operation, resource_type, DRY_RUN_METHODS[operation], url, payload=payload)
    return True


def resolve_fields(json_data, stdin_mode, **cli_kwargs):
    """Resolve mutation fields from --json/--stdin, else from CLI kwargs.

    --json / --stdin takes precedence when provided; otherwise build a dict
    from the non-None CLI kwargs. Resource-specific extras (custom_fields,
    watcher_user_ids, ...) are still appended by the caller afterwards.
    """
    json_fields = resolve_json_data(json_data, stdin_mode)
    if json_fields is not None:
        return json_fields
    return build_fields(**cli_kwargs)


def parse_fields(fields):
    """Parse a comma-separated --fields option into a list, or None.

    Returns None when nothing was given so emit() leaves output unfiltered.
    """
    return fields.split(",") if fields else None
