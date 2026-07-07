"""Search subcommand for redmine-cli."""

import urllib.parse

import click

from ..context import get_redmine
from ..output import emit, handle_errors
from ..utils import resourceset_to_list


def _scoped_search(rm, query, project, resources):
    """Run a search, optionally scoped to a single project.

    Redmine serves project-scoped searches from a separate
    ``/projects/{id_or_identifier}/search.json`` endpoint, while python-redmine's
    ``Redmine.search()`` hardcodes the global ``/search.json`` URL. To reuse
    ``rm.search()``'s resource-type mapping and pagination we temporarily
    rewrite ``rm.url`` to the project-scoped path and restore it afterwards.
    The CLI is single-threaded, so this is safe.
    """
    opts = {}
    if resources:
        opts["resources"] = [r.strip() for r in resources.split(",")]
    if project:
        original_url = rm.url
        try:
            rm.url = "{base}/projects/{scope}".format(
                base=original_url,
                scope=urllib.parse.quote(str(project), safe=""),
            )
            return rm.search(query, **opts)
        finally:
            rm.url = original_url
    return rm.search(query, **opts)


@click.command("search")
@click.argument("query")
@click.option(
    "--resources",
    "-r",
    help="Comma-separated resource types to search (e.g. issues,wiki_pages,news)",
)
@click.option(
    "--project",
    "-P",
    help="Limit the search to a project (identifier or numeric id, e.g. redminex)",
)
@click.pass_context
@handle_errors
def search(ctx, query, resources, project):
    """Full-text search across Redmine resources.

    \b
    Searches issues, wiki pages, news, documents, changesets, etc.
    Use -r to limit results to specific resource types.
    Use -P to limit the search to a single project.

    \b
    Examples:
      redmine-cli -p redminex search "login error"
      redmine-cli -p redminex search "部署" -r issues
      redmine-cli -p redminex search "API" -r issues,documents
      redmine-cli -p redminex search "login" -P myproject
      redmine-cli -p redminex search "API" -P 42 -r issues
    """
    rm = get_redmine(ctx)
    results = _scoped_search(rm, query, project, resources)
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
