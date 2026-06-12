"""Search subcommand for redmine-cli."""

import click

from ..context import get_redmine
from ..output import emit, handle_errors
from ..utils import resourceset_to_list


@click.command("search")
@click.argument("query")
@click.option(
    "--resources",
    "-r",
    help="Comma-separated resource types to search (e.g. issues,wiki_pages,news)",
)
@click.pass_context
@handle_errors
def search(ctx, query, resources):
    """Full-text search across Redmine resources.

    \b
    Searches issues, wiki pages, news, documents, changesets, etc.
    Use -r to limit results to specific resource types.
    Returns matching resources with their basic fields.

    \b
    Examples:
      redmine-cli -p redminex search "login error"
      redmine-cli -p redminex search "部署" -r issues
      redmine-cli -p redminex search "API" -r issues,documents
    """
    rm = get_redmine(ctx)
    opts = {}
    if resources:
        opts["resources"] = [r.strip() for r in resources.split(",")]
    results = rm.search(query, **opts)
    if not results:
        emit({})
        return
    serialized = {}
    for key, value in results.items():
        if (
            hasattr(value, "__iter__")
            and hasattr(value, "__len__")
            and hasattr(value, "__getitem__")
        ):
            serialized[key] = resourceset_to_list(value)
        elif isinstance(value, dict):
            serialized[key] = value
        else:
            serialized[key] = value
    emit(serialized)
