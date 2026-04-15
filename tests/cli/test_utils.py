"""Tests for serialization utilities."""

import json
import pytest
from datetime import date, datetime
from unittest.mock import MagicMock

from redmine_cli.utils import (
    serialize,
    to_json,
    resource_to_dict,
    resourceset_to_list,
    parse_json_input,
    build_fields,
)


def test_serialize_datetime():
    dt = datetime(2025, 1, 15, 10, 30, 0)
    assert serialize(dt) == "2025-01-15T10:30:00"


def test_serialize_date():
    d = date(2025, 1, 15)
    assert serialize(d) == "2025-01-15"


def test_serialize_resource():
    resource = MagicMock()
    resource.raw.return_value = {"id": 1, "subject": "Test"}
    assert serialize(resource) == {"id": 1, "subject": "Test"}


def test_to_json():
    data = {"date": date(2025, 1, 15), "name": "test"}
    result = json.loads(to_json(data))
    assert result["date"] == "2025-01-15"
    assert result["name"] == "test"


def test_resource_to_dict():
    resource = MagicMock()
    resource.raw.return_value = {"id": 1, "name": "Project X"}
    assert resource_to_dict(resource) == {"id": 1, "name": "Project X"}


def test_resourceset_to_list():
    r1 = MagicMock()
    r1.raw.return_value = {"id": 1}
    r2 = MagicMock()
    r2.raw.return_value = {"id": 2}
    result = resourceset_to_list([r1, r2])
    assert result == [{"id": 1}, {"id": 2}]


def test_parse_json_input():
    result = parse_json_input('{"project_id": 1, "subject": "test"}')
    assert result == {"project_id": 1, "subject": "test"}


def test_build_fields_from_json():
    result = build_fields(json_data='{"a": 1, "b": 2}')
    assert result == {"a": 1, "b": 2}


def test_build_fields_from_kwargs():
    result = build_fields(a=1, b=None, c=3)
    assert result == {"a": 1, "c": 3}


def test_build_fields_json_takes_precedence():
    result = build_fields(json_data='{"a": 1}', a=999)
    assert result == {"a": 1}
