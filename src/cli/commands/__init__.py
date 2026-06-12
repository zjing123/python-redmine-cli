"""Command groups split out from the root CLI.

Aggregates the ``config`` group and ``search`` command so ``main`` can import
them in one line. Resource command groups (issue, project, ...) still live in
``redmine_cli.resources``.
"""

from .config import config_group
from .search import search

__all__ = ["config_group", "search"]
