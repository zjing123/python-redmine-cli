"""Serialization and data conversion utilities for redmine-cli."""

import json
import sys
from datetime import date, datetime

import click


def serialize(obj):
    """JSON serializer for objects not serializable by default json.dumps."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if hasattr(obj, "raw"):
        return obj.raw()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def to_json(obj, **kwargs):
    """Convert object to JSON string."""
    return json.dumps(obj, default=serialize, ensure_ascii=False, **kwargs)


def resource_to_dict(resource):
    """Convert a redminelib Resource to a plain dict via raw()."""
    return resource.raw()


def resourceset_to_list(resourceset):
    """Convert a ResourceSet to a list of dicts."""
    return [r.raw() for r in resourceset]


def parse_json_input(json_str, param_name="--json"):
    """Parse a JSON string, useful for --json CLI arguments.

    Args:
        json_str: The JSON string to parse.
        param_name: Parameter name used in error messages for context.
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise click.UsageError(f"Invalid JSON in {param_name}: {e}") from e


def resolve_json_data(json_data, stdin_mode, required=False):
    """Resolve JSON input from --json string or --stdin pipe.

    Returns parsed dict, or None if neither source was provided.
    Raises click.UsageError on mutual exclusion, empty stdin, or missing input.
    """
    if json_data and stdin_mode:
        raise click.UsageError("--json and --stdin are mutually exclusive.")
    if stdin_mode:
        raw = sys.stdin.read().strip()
        if not raw:
            raise click.UsageError("No data received on stdin.")
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise click.UsageError(f"Invalid JSON from --stdin: {e}") from e
    if json_data:
        try:
            return json.loads(json_data)
        except json.JSONDecodeError as e:
            raise click.UsageError(f"Invalid JSON in --json: {e}") from e
    if required:
        raise click.UsageError("Either --json or --stdin is required.")
    return None


def build_fields(json_data=None, **cli_kwargs):
    """Build a fields dict from either a JSON string or individual CLI kwargs.

    JSON string takes precedence if provided.
    """
    if json_data:
        return parse_json_input(json_data)
    fields = {}
    for key, value in cli_kwargs.items():
        if value is not None:
            fields[key] = value
    return fields
