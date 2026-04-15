"""Tests for output formatting module."""

import json
import sys
import pytest
from io import StringIO

from redmine_cli.output import emit, emit_error, handle_errors
from redminelib.exceptions import ResourceNotFoundError, ValidationError


def test_emit_single_data(capsys):
    emit({"id": 1, "subject": "Test"})
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["ok"] is True
    assert data["data"]["id"] == 1


def test_emit_list_with_pagination(capsys):
    emit([{"id": 1}, {"id": 2}], total_count=100, limit=2, offset=0)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["ok"] is True
    assert data["total_count"] == 100
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["data"]) == 2


def test_emit_error_exits_with_code(capsys):
    with pytest.raises(SystemExit) as exc_info:
        emit_error(ResourceNotFoundError())
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["ok"] is False
    assert data["error_type"] == "ResourceNotFoundError"


def test_emit_error_validation(capsys):
    with pytest.raises(SystemExit) as exc_info:
        emit_error(ValidationError("field is required"))
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["ok"] is False
    assert "field is required" in data["error"]


def test_handle_errors_decorator_catches_redmine_error(capsys):
    @handle_errors
    def failing_func():
        raise ResourceNotFoundError()

    with pytest.raises(SystemExit):
        failing_func()


def test_handle_errors_decorator_passes_through():
    @handle_errors
    def ok_func():
        return 42

    result = ok_func()
    assert result == 42


def test_handle_errors_catches_unknown(capsys):
    @handle_errors
    def boom():
        raise RuntimeError("boom")

    with pytest.raises(SystemExit):
        boom()
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["ok"] is False
    assert data["error"] == "boom"
