"""Unified JSON output and error handling for redmine-cli.

All output follows the convention:
  Success: {"ok": true, "data": ...}
  List:    {"ok": true, "total_count": N, "limit": N, "offset": N, "data": [...]}
  Error:   {"ok": false, "error": "...", "error_type": "..."}

Exit codes:
  0  — success
  1  — business / runtime error
  2  — argument / usage error
"""

import sys
import json
import functools
import re

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


def _filter_fields(data, fields):
    """Filter data items to only include specified fields.

    Works on both lists (list commands) and dicts (single item).
    """
    if not fields:
        return data
    field_set = set(fields)
    if isinstance(data, list):
        return [{k: v for k, v in item.items() if k in field_set} for item in data]
    if isinstance(data, dict):
        return {k: v for k, v in data.items() if k in field_set}
    return data


def emit(data, total_count=None, limit=None, offset=None, fields=None, extra=None):
    """Emit a successful JSON response to stdout."""
    result = {"ok": True}
    if total_count is not None:
        result["total_count"] = total_count
        result["limit"] = limit
        result["offset"] = offset if offset else 0
    if fields:
        data = _filter_fields(data, fields)
    result["data"] = data
    if extra:
        result.update(extra)
    click.echo(json.dumps(result, default=str, ensure_ascii=False))


def _mask_sensitive_keys(obj, _seen=None):
    """Recursively mask sensitive values in a nested dict/list structure.

    Keys matching common sensitive patterns (password, token, api_key, secret,
    etc.) have their values replaced with '****'.  Non-dict/non-list values
    are returned unchanged.
    """
    if _seen is None:
        _seen = set()

    if isinstance(obj, dict):
        obj_id = id(obj)
        if obj_id in _seen:
            return obj
        _seen.add(obj_id)
        masked = {}
        for k, v in obj.items():
            if _is_sensitive_key(k):
                masked[k] = "****"
            else:
                masked[k] = _mask_sensitive_keys(v, _seen)
        return masked

    if isinstance(obj, list):
        return [_mask_sensitive_keys(item, _seen) for item in obj]

    return obj


_SENSITIVE_PATTERN = re.compile(
    r"(password|passwd|secret|token|api_key|apikey|api_secret|"
    r"private_key|access_key|auth_token|credentials?)",
    re.IGNORECASE,
)


def _is_sensitive_key(key):
    """Return True if *key* looks like it holds a secret."""
    return bool(_SENSITIVE_PATTERN.search(key))


def emit_dry_run(operation, resource_type, method, url, payload=None):
    """Emit a dry-run response showing what would be sent to the API.

    Outputs the same {"ok": true, "data": ...} envelope but with an extra
    top-level "dry_run": true key so consumers can detect it programmatically.
    Sensitive fields (password, token, api_key, etc.) in *payload* are
    automatically masked with '****'.

    :param operation: 'create', 'update', 'delete', 'close', 'reopen', etc.
    :param resource_type: 'issue', 'project', 'user', etc.
    :param method: HTTP method ('POST', 'PUT', 'DELETE').
    :param url: The full URL that would be called.
    :param payload: Optional dict of fields that would be sent as the request body.
    """
    data = {
        "dry_run": True,
        "operation": operation,
        "resource_type": resource_type,
        "method": method,
        "url": url,
    }
    if payload:
        data["payload"] = _mask_sensitive_keys(payload)
    result = {"ok": True, "dry_run": True, "data": data}
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
    """Decorator that catches exceptions and emits JSON errors.

    * ``click.UsageError`` / ``click.BadParameter`` → JSON + exit 2
    * ``redminelib`` exceptions → JSON + mapped exit code (default 1)
    * Unexpected exceptions → JSON + exit 1
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (click.UsageError, click.BadParameter) as e:
            click.echo(
                json.dumps(
                    {
                        "ok": False,
                        "error": e.format_message(),
                        "error_type": type(e).__name__,
                    },
                    default=str,
                    ensure_ascii=False,
                )
            )
            sys.exit(2)
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
