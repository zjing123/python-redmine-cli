"""Resource schema discovery for redmine-cli.

Provides static and live schema information for Redmine resources.
Static schema is derived from python-redmine library introspection.
Live schema (--live) queries the Redmine API for enum values.
"""

from redminelib.resources import registry as resource_registry

from .fields import _snake_to_pascal


# Hardcoded required/optional field definitions based on Redmine API docs.
# These cannot be derived from the python-redmine library alone.
# Keys are snake_case resource names matching the registry.
_RESOURCE_SCHEMAS = {
    "issue": {
        "required_fields": ["project_id", "subject"],
        "optional_fields": [
            "tracker_id",
            "status_id",
            "priority_id",
            "assigned_to_id",
            "parent_issue_id",
            "fixed_version_id",
            "category_id",
            "description",
            "notes",
            "is_private",
            "estimated_hours",
            "start_date",
            "due_date",
            "done_ratio",
            "watcher_user_ids",
            "custom_fields",
        ],
    },
    "project": {
        "required_fields": ["name", "identifier"],
        "optional_fields": [
            "description",
            "homepage",
            "is_public",
            "parent_id",
            "inherit_members",
            "enabled_module_names",
            "tracker_ids",
            "custom_fields",
        ],
    },
    "user": {
        "required_fields": ["login", "firstname", "lastname", "mail"],
        "optional_fields": [
            "password",
            "auth_source_id",
            "must_change_passwd",
            "generate_password",
            "custom_fields",
        ],
    },
    "time_entry": {
        "required_fields": ["issue_id", "hours"],
        "optional_fields": [
            "project_id",
            "spent_on",
            "activity_id",
            "comments",
            "custom_fields",
        ],
    },
    "wiki_page": {
        "required_fields": ["title", "text"],
        "optional_fields": [
            "comments",
            "parent_title",
            "custom_fields",
        ],
    },
    "version": {
        "required_fields": ["name"],
        "optional_fields": [
            "description",
            "status",
            "sharing",
            "due_date",
            "wiki_page_title",
            "custom_fields",
        ],
    },
    "issue_category": {
        "required_fields": ["name"],
        "optional_fields": [
            "assigned_to_id",
        ],
    },
    "issue_relation": {
        "required_fields": ["issue_id", "relation_type"],
        "optional_fields": [
            "issue_to_id",
            "delay",
        ],
    },
    "news": {
        "required_fields": ["title", "summary", "description"],
        "optional_fields": [],
    },
    "group": {
        "required_fields": ["name"],
        "optional_fields": [
            "user_ids",
            "custom_fields",
        ],
    },
    "project_membership": {
        "required_fields": ["user_id", "role_ids"],
        "optional_fields": [],
    },
    "file": {
        "required_fields": ["token", "filename"],
        "optional_fields": [
            "description",
            "version_id",
        ],
    },
}


def get_resource_schema(resource_name):
    """Extract static schema for a resource type.

    Combines python-redmine library introspection with hardcoded
    required/optional field definitions. No live connection needed.

    Args:
        resource_name: snake_case resource name (e.g. 'issue', 'wiki_page').

    Returns:
        dict with keys:
            - resource: the resource name
            - creatable: whether the resource can be created via API
            - updatable: whether the resource can be updated via API
            - deletable: whether the resource can be deleted via API
            - required_url_params: params required in the URL template
            - required_fields: fields required for creation
            - optional_fields: fields optional for creation
            - create_readonly: fields that are read-only during creation
            - update_readonly: fields that are read-only during update
            - id_fields: foreign-key style fields
            - related_objects: single related objects
            - related_collections: lists of related objects

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

    # Determine creatability from query_create
    query_create = getattr(cls, "query_create", None)
    query_update = getattr(cls, "query_one", None)
    container_create = getattr(cls, "container_create", None)
    creatable = query_create is not None and container_create is not None

    # Updatable if query_one exists (has get endpoint for re-fetch)
    # and there's no restriction. python-redmine allows update if query_one exists.
    updatable = query_update is not None

    # Extract required URL params from query_create template
    required_url_params = []
    if creatable and hasattr(query_create, "formatter"):
        formatter = query_create.formatter
        # formatter.used_kwargs is populated after format() call,
        # but we can extract from the template string
        import re
        template_str = str(query_create)
        required_url_params = re.findall(r"\{(\w+)\}", template_str)

    # Get hardcoded schema if available
    hardcoded = _RESOURCE_SCHEMAS.get(resource_name, {})

    # Read-only fields
    create_readonly = list(getattr(cls, "_create_readonly", []))
    update_readonly = list(getattr(cls, "_update_readonly", []))

    # ID fields
    id_fields = {
        **getattr(cls, "_single_attr_id_map", {}),
        **getattr(cls, "_multiple_attr_id_map", {}),
    }

    # Related resources
    related_objects = dict(getattr(cls, "_resource_map", {}))
    related_collections = dict(getattr(cls, "_resource_set_map", {}))

    return {
        "resource": resource_name,
        "creatable": creatable,
        "updatable": updatable,
        "required_url_params": required_url_params,
        "required_fields": hardcoded.get("required_fields", []),
        "optional_fields": hardcoded.get("optional_fields", []),
        "create_readonly": create_readonly,
        "update_readonly": update_readonly,
        "id_fields": id_fields,
        "related_objects": related_objects,
        "related_collections": related_collections,
    }


def get_live_enums(rm, resource_name):
    """Fetch live enum values from a Redmine instance.

    Queries trackers, statuses, priorities, etc. based on the resource type.
    Requires a live Redmine connection.

    Args:
        rm: A connected Redmine instance.
        resource_name: snake_case resource name.

    Returns:
        dict with enum field names as keys and lists of {id, name} dicts as values.
        Empty dict if resource has no known enums.
    """
    from .utils import resourceset_to_list

    enums = {}
    enum_fetchers = {
        "issue": {
            "trackers": lambda: rm.tracker.all(),
            "statuses": lambda: rm.issue_status.all(),
            "priorities": lambda: rm.enumeration.filter(resource="issue_priorities"),
        },
        "project": {
            "trackers": lambda: rm.tracker.all(),
        },
        "time_entry": {
            "activities": lambda: rm.enumeration.filter(resource="time_entry_activities"),
        },
    }

    fetchers = enum_fetchers.get(resource_name, {})
    for name, fetcher in fetchers.items():
        try:
            rs = fetcher()
            enums[name] = resourceset_to_list(rs)
        except Exception:
            # If fetching fails (e.g. permissions), skip silently
            enums[name] = []

    return enums
