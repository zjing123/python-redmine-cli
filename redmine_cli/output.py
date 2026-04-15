"""Unified JSON output and error handling for redmine-cli.

All output follows the convention:
  Success: {"ok": true, "data": ...}
  List:    {"ok": true, "total_count": N, "limit": N, "offset": N, "data": [...]}
  Error:   {"ok": false, "error": "...", "error_type": "..."}
"""

import sys
import json
import functools

import click
from redminelib import exceptions

EXIT_CODE_MAP = {
    exceptions.AuthError: 1,
    exceptions.ResourceNotFoundError: 1,
    exceptions.ValidationError: 1,
    exceptions.ForbiddenError: 1,
    exceptions.ConflictError: 1,
    exceptions.ServerError: 1,
    exceptions.ImpersonateError: 1,
    exceptions.ResourceBadMethodError: 2,
    exceptions.ResourceNoFiltersProvidedError: 2,
    exceptions.ResourceNoFieldsProvidedError: 2,
    exceptions.ResourceFilterError: 2,
    exceptions.ResourceVersionMismatchError: 1,
    exceptions.VersionMismatchError: 1,
    exceptions.CustomFieldValueError: 2,
}


def emit(data, total_count=None, limit=None, offset=None):
    """Emit a successful JSON response to stdout."""
    result = {"ok": True}
    if total_count is not None:
        result["total_count"] = total_count
        result["limit"] = limit
        result["offset"] = offset
    result["data"] = data
    click.echo(json.dumps(result, default=str, ensure_ascii=False))


def emit_error(exc):
    """Emit an error JSON response to stdout and exit with non-zero code."""
    result = {
        "ok": False,
        "error": str(exc),
        "error_type": type(exc).__name__,
    }
    if hasattr(exc, "status_code"):
        result["status_code"] = exc.status_code
    code = EXIT_CODE_MAP.get(type(exc), 1)
    click.echo(json.dumps(result, default=str, ensure_ascii=False))
    sys.exit(code)


def handle_errors(func):
    """Decorator that catches redminelib exceptions and emits JSON errors."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except exceptions.BaseRedmineError as e:
            emit_error(e)
        except SystemExit:
            raise
        except Exception as e:
            click.echo(
                json.dumps(
                    {
                        "ok": False,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                    default=str,
                    ensure_ascii=False,
                )
            )
            sys.exit(1)

    return wrapper
