"""Configuration management for redmine-cli.

Supports: CLI args > env vars > config file > defaults.
Config file: ~/.config/redmine-cli/config.yaml
"""

import json
import os
from pathlib import Path
from urllib.parse import urlparse

import yaml
from redminelib import Redmine
from redminelib.engines import SyncEngine

DEFAULT_TIMEOUT = 30


class TimeoutEngine(SyncEngine):
    """SyncEngine with a default request timeout."""

    timeout = DEFAULT_TIMEOUT

    def request(self, method, url, headers=None, params=None, data=None):
        kwargs = self.construct_request_kwargs(method, headers, params, data)
        return self.process_response(
            self.session.request(method, url, timeout=self.timeout, **kwargs)
        )

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "redmine-cli"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.yaml"


def _extract_profile_name(url):
    """Extract profile name from URL hostname prefix.

    Examples:
        http://redminetest.kettle.net.cn:7777/redmine2/ -> redminetest
        https://staging.example.com/ -> staging
    """
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    return hostname.split(".")[0]


def _resolve_config_path():
    return Path(os.environ.get("REDMINE_CONFIG", str(DEFAULT_CONFIG_PATH)))


def load_config_file():
    """Load raw config file data, returns dict or empty dict."""
    config_path = _resolve_config_path()
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    return {}


def save_config_file(data):
    """Save config data to file, creating directories as needed."""
    config_path = _resolve_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def load_config(profile=None):
    """Load configuration from file and environment variables.

    All accounts live under ``profiles`` in the config file.
    A *profile* name is required — either passed explicitly or resolved
    from a URL via :func:`resolve_profile_by_url`.

    If *profile* is ``None`` the function returns an empty dict so that
    env-var-only usage (``REDMINE_URL`` + ``REDMINE_API_KEY``) still works.
    """
    config_path = _resolve_config_path()
    config = {}

    if profile and config_path.exists():
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
        if profile in data.get("profiles", {}):
            config = dict(data["profiles"][profile])

    # Normalise api_key -> key for python-redmine
    if "api_key" in config and "key" not in config:
        config["key"] = config.pop("api_key")
    elif "api_key" in config:
        config.pop("api_key")

    env_map = {
        "url": "REDMINE_URL",
        "key": "REDMINE_API_KEY",
        "username": "REDMINE_USERNAME",
        "password": "REDMINE_PASSWORD",
        "version": "REDMINE_VERSION",
    }
    for key, env_var in env_map.items():
        val = os.environ.get(env_var)
        if val is not None:
            config[key] = val

    return config


def list_profiles():
    """List all profile names from config file."""
    data = load_config_file()
    profiles = list(data.get("profiles", {}).keys())
    return profiles


def resolve_profile_by_url(url):
    """Match a full Redmine URL against configured profiles.

    Uses longest prefix match so subpath-hosted Redmine instances
    (e.g. https://host/redmine2/) are handled correctly.

    :param url: Full Redmine URL, e.g. https://redminex.example.com/issues/123
    :returns: Profile name string, or None if no match.
    """
    data = load_config_file()
    url_clean = url.rstrip("/")

    best_match = None
    best_len = 0

    for name, conf in data.get("profiles", {}).items():
        profile_url = conf.get("url", "").rstrip("/")
        if url_clean.startswith(profile_url) and len(profile_url) > best_len:
            best_match = name
            best_len = len(profile_url)

    return best_match


def create_redmine(profile=None, **overrides):
    """Create a Redmine instance from configuration.

    :param profile: Config file profile name.
    :param overrides: Additional kwargs to pass to Redmine().
    :returns: redminelib.Redmine instance.
    :raises SystemExit: If url is missing.
    """
    config = load_config(profile)
    config.update(overrides)

    url = config.pop("url", None)
    if not url:
        raise SystemExit(
            json.dumps(
                {"ok": False, "error": "REDMINE_URL is required"},
                ensure_ascii=False,
            )
        )

    kwargs = {"url": url}

    if config.get("key"):
        kwargs["key"] = config["key"]
    elif config.get("username"):
        kwargs["username"] = config["username"]
        kwargs["password"] = config.get("password", "")

    if config.get("version"):
        kwargs["version"] = config["version"]

    kwargs["engine"] = TimeoutEngine
    return Redmine(**kwargs)
