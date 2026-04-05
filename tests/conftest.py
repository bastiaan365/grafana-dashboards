"""Shared fixtures for grafana-dashboards test suite."""

import json
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DASHBOARDS_DIR = REPO_ROOT / "dashboards"
TELEGRAF_DIR = REPO_ROOT / "telegraf"

DASHBOARD_FILES = sorted(DASHBOARDS_DIR.glob("*.json"))
TELEGRAF_CONF_FILES = sorted(TELEGRAF_DIR.glob("*.conf"))

# ---------------------------------------------------------------------------
# Dashboard fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def dashboard_files():
    """Return sorted list of all dashboard JSON file paths."""
    return DASHBOARD_FILES


@pytest.fixture(scope="session")
def all_dashboards():
    """Return a dict mapping filename -> parsed dashboard dict for all dashboards."""
    result = {}
    for path in DASHBOARD_FILES:
        with path.open() as f:
            result[path.name] = json.load(f)
    return result


# ---------------------------------------------------------------------------
# Telegraf config fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def telegraf_conf_files():
    """Return sorted list of all telegraf .conf file paths."""
    return TELEGRAF_CONF_FILES


@pytest.fixture(scope="session")
def telegraf_configs():
    """Return a dict mapping filename -> parsed TOML dict for all telegraf configs."""
    result = {}
    for path in TELEGRAF_CONF_FILES:
        with path.open("rb") as f:
            result[path.name] = tomllib.load(f)
    return result
