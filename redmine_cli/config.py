"""Configuration management for redmine-cli.

Supports: CLI args > env vars > config file > defaults.
Config file: ~/.config/redmine-cli/config.yaml
"""

import os
from pathlib import Path
from urllib.parse import urlparse

import yaml
from redminelib import Redmine

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
    """Load configuration from file, environment variables, and defaults.

    If no profile specified, merges default + env overrides.
    If profile specified, uses that profile's config + env overrides.
    """
    config_path = _resolve_config_path()
    config = {}

    if config_path.exists():
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
        if profile and profile in data.get("profiles", {}):
            config = data["profiles"][profile]
        else:
            config = data.get("default", {})

    if "api_key" in config:
        config["key"] = config.pop("api_key")

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
        raise SystemExit('{"ok": false, "error": "REDMINE_URL is required"}')

    kwargs = {"url": url}

    if config.get("key"):
        kwargs["key"] = config["key"]
    elif config.get("username"):
        kwargs["username"] = config["username"]
        kwargs["password"] = config.get("password", "")

    if config.get("version"):
        kwargs["version"] = config["version"]

    return Redmine(**kwargs)
