"""Field metadata extraction from redminelib resource registry.

Provides a shared utility for discovering available fields on any Redmine
resource type without requiring a live connection. Used by the ``fields``
subcommands on each resource group.
"""

from redminelib.resources import registry as resource_registry


def _snake_to_pascal(name):
    """Convert snake_case resource name to PascalCase for registry lookup.

    Examples:
        issue -> Issue
        time_entry -> TimeEntry
        wiki_page -> WikiPage
    """
    return "".join(word.capitalize() for word in name.split("_"))


def get_resource_fields(resource_name):
    """Extract field metadata for a resource type from the redminelib registry.

    Args:
        resource_name: snake_case resource name (e.g. 'issue', 'wiki_page').

    Returns:
        dict with keys:
            - resource: the resource name
            - object_fields: single related objects (from _resource_map)
            - collection_fields: lists of related objects (from _resource_set_map)
            - includable_fields: data fetchable via ?include= (from _includes)
            - id_fields: foreign-key style fields (from _single/multiple_attr_id_map)
            - relations: related resource managers (from _relations)

    Raises:
        ValueError: if resource_name is not found in the registry.
    """
    pascal_name = _snake_to_pascal(resource_name)
    if pascal_name not in resource_registry:
        raise ValueError(
            f"Unknown resource '{resource_name}'. "
            f"Use 'redmine-cli resource types' to see available resources."
        )
    cls = resource_registry[pascal_name]["class"]

    return {
        "resource": resource_name,
        "object_fields": dict(getattr(cls, "_resource_map", {})),
        "collection_fields": dict(getattr(cls, "_resource_set_map", {})),
        "includable_fields": list(getattr(cls, "_includes", [])),
        "id_fields": {
            **getattr(cls, "_single_attr_id_map", {}),
            **getattr(cls, "_multiple_attr_id_map", {}),
        },
        "relations": list(getattr(cls, "_relations", [])),
    }
