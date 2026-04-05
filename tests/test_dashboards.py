"""Comprehensive tests for Grafana dashboard JSON files."""

import json
import re
from pathlib import Path

import pytest

from tests.conftest import DASHBOARDS_DIR, DASHBOARD_FILES

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXPECTED_SCHEMA_VERSION = 38
GRAFANA_GRID_WIDTH = 24
EXPECTED_BUCKET = "telegraf"
EXPECTED_DATASOURCE_INPUT_NAME = "DS_INFLUXDB"
EXPECTED_DATASOURCE_PLUGIN_ID = "influxdb"
VALID_PANEL_TYPES = {"timeseries", "gauge", "stat", "table", "piechart", "barchart", "graph", "text", "row"}
PANEL_REQUIRED_KEYS = ["id", "title", "type", "gridPos", "datasource", "targets"]
VALID_REFRESH_PATTERN = re.compile(r"^\d+[smhd]$")

# Expected dashboard metadata: filename -> (title, uid, min_panel_count, tags)
EXPECTED_DASHBOARDS = {
    "dns-analytics.json": ("DNS Analytics", "dns-analytics-001", 3, ["dns", "analytics"]),
    "network-overview.json": ("Network Overview", "net-overview-001", 3, ["network", "traffic", "vlan"]),
    "opnsense-firewall.json": ("OPNsense Firewall", "opnsense-fw-001", 3, ["opnsense", "firewall"]),
    "suricata-ids.json": ("Suricata IDS", "suricata-ids-001", 3, ["suricata", "ids", "security"]),
    "system-health.json": ("System Health", "sys-health-001", 4, ["system", "health", "hardware"]),
    "wireguard-vpn.json": ("WireGuard VPN", "wireguard-vpn-001", 3, ["wireguard", "vpn"]),
}

# Expected panels per dashboard: filename -> list of (panel title, panel type)
EXPECTED_PANELS = {
    "dns-analytics.json": [
        ("DNS Query Volume", "timeseries"),
        ("DNSSEC Validation", "stat"),
        ("Top Queried Domains", "table"),
        ("Blocked Domains", "stat"),
    ],
    "network-overview.json": [
        ("Traffic In/Out per Interface", "timeseries"),
        ("Bandwidth Usage by VLAN", "timeseries"),
        ("Current Throughput", "gauge"),
        ("Top Talkers", "table"),
    ],
    "opnsense-firewall.json": [
        ("Firewall Rule Hits Over Time", "timeseries"),
        ("State Table Size", "gauge"),
        ("Interface Packets & Errors", "timeseries"),
        ("Top Blocked IPs", "table"),
    ],
    "suricata-ids.json": [
        ("Alert Severity Distribution", "piechart"),
        ("Top Alert Signatures", "barchart"),
        ("Alerts Over Time", "timeseries"),
        ("Blocked Threats (24h)", "stat"),
    ],
    "system-health.json": [
        ("CPU Usage", "timeseries"),
        ("Memory Usage", "gauge"),
        ("Temperature", "stat"),
        ("Disk I/O", "timeseries"),
        ("Disk Usage", "gauge"),
    ],
    "wireguard-vpn.json": [
        ("Tunnel Status", "stat"),
        ("Last Handshake", "table"),
        ("Data Transferred per Peer", "timeseries"),
    ],
}

# Measurements referenced in each dashboard's Flux queries
EXPECTED_MEASUREMENTS = {
    "dns-analytics.json": ["dns_query"],
    "network-overview.json": ["net"],
    "opnsense-firewall.json": ["opnsense_firewall", "snmp_interface"],
    "suricata-ids.json": ["suricata"],
    "system-health.json": ["cpu", "mem", "temp", "disk"],
    "wireguard-vpn.json": ["wireguard"],
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def load_dashboard(filename: str) -> dict:
    path = DASHBOARDS_DIR / filename
    with path.open() as f:
        return json.load(f)


def all_queries(dashboard: dict) -> list[str]:
    queries = []
    for panel in dashboard.get("panels", []):
        for target in panel.get("targets", []):
            q = target.get("query", "")
            if q:
                queries.append(q)
    return queries


# ---------------------------------------------------------------------------
# 1. JSON validity
# ---------------------------------------------------------------------------

class TestJsonValidity:
    """Every dashboard file must be valid JSON."""

    @pytest.mark.parametrize("path", DASHBOARD_FILES, ids=[p.name for p in DASHBOARD_FILES])
    def test_file_is_valid_json(self, path: Path):
        with path.open() as f:
            data = json.load(f)
        assert isinstance(data, dict), f"{path.name} root element must be a JSON object"

    def test_all_expected_dashboards_present(self):
        actual = {p.name for p in DASHBOARD_FILES}
        for expected_name in EXPECTED_DASHBOARDS:
            assert expected_name in actual, f"Dashboard {expected_name!r} is missing from dashboards/"


# ---------------------------------------------------------------------------
# 2. Top-level required fields
# ---------------------------------------------------------------------------

class TestTopLevelFields:
    """Each dashboard must contain the required top-level Grafana fields."""

    REQUIRED_FIELDS = [
        "title", "uid", "schemaVersion", "panels", "tags",
        "time", "refresh", "timezone", "annotations", "templating",
        "__inputs", "__requires",
    ]

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    @pytest.mark.parametrize("field", REQUIRED_FIELDS)
    def test_required_field_present(self, filename: str, field: str):
        d = load_dashboard(filename)
        assert field in d, f"{filename}: missing required field {field!r}"

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_schema_version(self, filename: str):
        d = load_dashboard(filename)
        assert d["schemaVersion"] == EXPECTED_SCHEMA_VERSION, (
            f"{filename}: schemaVersion should be {EXPECTED_SCHEMA_VERSION}, got {d['schemaVersion']}"
        )

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_title_matches_expected(self, filename: str):
        expected_title, *_ = EXPECTED_DASHBOARDS[filename]
        d = load_dashboard(filename)
        assert d["title"] == expected_title, (
            f"{filename}: title should be {expected_title!r}, got {d['title']!r}"
        )

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_uid_matches_expected(self, filename: str):
        _, expected_uid, *_ = EXPECTED_DASHBOARDS[filename]
        d = load_dashboard(filename)
        assert d["uid"] == expected_uid, (
            f"{filename}: uid should be {expected_uid!r}, got {d['uid']!r}"
        )

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_tags_match_expected(self, filename: str):
        *_, expected_tags = EXPECTED_DASHBOARDS[filename]
        d = load_dashboard(filename)
        assert sorted(d["tags"]) == sorted(expected_tags), (
            f"{filename}: tags mismatch — expected {sorted(expected_tags)}, got {sorted(d['tags'])}"
        )

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_tags_not_empty(self, filename: str):
        d = load_dashboard(filename)
        assert d["tags"], f"{filename}: tags list must not be empty"

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_refresh_is_set(self, filename: str):
        d = load_dashboard(filename)
        assert d.get("refresh"), f"{filename}: refresh must be set to a non-empty value"

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_refresh_format(self, filename: str):
        d = load_dashboard(filename)
        refresh = d.get("refresh", "")
        assert VALID_REFRESH_PATTERN.match(refresh), (
            f"{filename}: refresh value {refresh!r} should match pattern like '30s', '1m', '6h'"
        )

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_time_has_from_and_to(self, filename: str):
        d = load_dashboard(filename)
        t = d.get("time", {})
        assert "from" in t, f"{filename}: time.from is missing"
        assert "to" in t, f"{filename}: time.to is missing"

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_time_to_is_now(self, filename: str):
        d = load_dashboard(filename)
        assert d["time"]["to"] == "now", f"{filename}: time.to should be 'now'"

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_id_is_null(self, filename: str):
        """Dashboards exported for import must have id: null."""
        d = load_dashboard(filename)
        assert d.get("id") is None, f"{filename}: id should be null for importable dashboards"


# ---------------------------------------------------------------------------
# 3. UID uniqueness across all dashboards
# ---------------------------------------------------------------------------

class TestUidUniqueness:
    def test_uids_are_unique_across_dashboards(self):
        uids = []
        for filename in EXPECTED_DASHBOARDS:
            d = load_dashboard(filename)
            uids.append(d["uid"])
        assert len(uids) == len(set(uids)), f"Duplicate UIDs found: {uids}"


# ---------------------------------------------------------------------------
# 4. Datasource / __inputs / __requires
# ---------------------------------------------------------------------------

class TestDatasourceConfig:
    """Dashboards must declare the InfluxDB datasource via __inputs/__requires."""

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_inputs_has_influxdb_datasource(self, filename: str):
        d = load_dashboard(filename)
        inputs = d.get("__inputs", [])
        names = [i.get("name") for i in inputs]
        assert EXPECTED_DATASOURCE_INPUT_NAME in names, (
            f"{filename}: __inputs must contain {EXPECTED_DATASOURCE_INPUT_NAME!r}"
        )

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_inputs_datasource_type(self, filename: str):
        d = load_dashboard(filename)
        for inp in d.get("__inputs", []):
            if inp.get("name") == EXPECTED_DATASOURCE_INPUT_NAME:
                assert inp.get("pluginId") == EXPECTED_DATASOURCE_PLUGIN_ID, (
                    f"{filename}: __inputs DS_INFLUXDB pluginId should be {EXPECTED_DATASOURCE_PLUGIN_ID!r}"
                )
                assert inp.get("type") == "datasource", (
                    f"{filename}: __inputs DS_INFLUXDB type should be 'datasource'"
                )

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_requires_grafana_entry(self, filename: str):
        d = load_dashboard(filename)
        requires = d.get("__requires", [])
        grafana_reqs = [r for r in requires if r.get("type") == "grafana"]
        assert grafana_reqs, f"{filename}: __requires must include a 'grafana' entry"

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_requires_grafana_version_10(self, filename: str):
        d = load_dashboard(filename)
        for req in d.get("__requires", []):
            if req.get("type") == "grafana":
                version = req.get("version", "")
                parts = version.split(".") if version else []
                major = int(parts[0]) if parts and parts[0].isdigit() else 0
                assert major >= 10, (
                    f"{filename}: Grafana version requirement should be >= 10.0.0, got {version!r}"
                )

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_requires_influxdb_datasource(self, filename: str):
        d = load_dashboard(filename)
        requires = d.get("__requires", [])
        influx_reqs = [r for r in requires if r.get("id") == "influxdb" and r.get("type") == "datasource"]
        assert influx_reqs, f"{filename}: __requires must include an influxdb datasource entry"


# ---------------------------------------------------------------------------
# 5. Panel structure
# ---------------------------------------------------------------------------

class TestPanelStructure:
    """Each panel must have required fields and valid values."""

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_panel_count_meets_minimum(self, filename: str):
        _, _, min_panels, _ = EXPECTED_DASHBOARDS[filename]
        d = load_dashboard(filename)
        count = len(d.get("panels", []))
        assert count >= min_panels, (
            f"{filename}: expected at least {min_panels} panels, found {count}"
        )

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_panel_ids_are_unique(self, filename: str):
        d = load_dashboard(filename)
        ids = [p["id"] for p in d.get("panels", []) if "id" in p]
        assert len(ids) == len(set(ids)), (
            f"{filename}: panel IDs must be unique, found duplicates in {ids}"
        )

    @pytest.mark.parametrize("filename,field", [
        (fname, field)
        for fname in EXPECTED_DASHBOARDS
        for field in PANEL_REQUIRED_KEYS
    ])
    def test_panels_have_required_keys(self, filename: str, field: str):
        d = load_dashboard(filename)
        for panel in d.get("panels", []):
            assert field in panel, (
                f"{filename}: panel {panel.get('title', '?')!r} is missing required field {field!r}"
            )

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_panel_types_are_valid(self, filename: str):
        d = load_dashboard(filename)
        for panel in d.get("panels", []):
            assert panel["type"] in VALID_PANEL_TYPES, (
                f"{filename}: panel {panel.get('title')!r} has unknown type {panel['type']!r}"
            )

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_panel_titles_are_non_empty(self, filename: str):
        d = load_dashboard(filename)
        for panel in d.get("panels", []):
            assert panel.get("title", "").strip(), (
                f"{filename}: panel id={panel.get('id')} has an empty title"
            )

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_panel_datasource_uses_influxdb_variable(self, filename: str):
        d = load_dashboard(filename)
        for panel in d.get("panels", []):
            ds = panel.get("datasource", {})
            assert ds.get("type") == "influxdb", (
                f"{filename}: panel {panel.get('title')!r} datasource type should be 'influxdb'"
            )
            assert ds.get("uid") == "${DS_INFLUXDB}", (
                f"{filename}: panel {panel.get('title')!r} datasource uid should be '${{DS_INFLUXDB}}'"
            )


# ---------------------------------------------------------------------------
# 6. Specific expected panels per dashboard
# ---------------------------------------------------------------------------

class TestExpectedPanelContent:
    """Each dashboard must contain the specific panels with correct types."""

    @pytest.mark.parametrize("filename", EXPECTED_PANELS)
    def test_expected_panels_exist(self, filename: str):
        d = load_dashboard(filename)
        actual = {(p["title"], p["type"]) for p in d.get("panels", [])}
        for title, ptype in EXPECTED_PANELS[filename]:
            assert (title, ptype) in actual, (
                f"{filename}: expected panel ({title!r}, type={ptype!r}) not found"
            )


# ---------------------------------------------------------------------------
# 7. Grid layout
# ---------------------------------------------------------------------------

class TestGridLayout:
    """Panel grid positions must respect Grafana's 24-column layout."""

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_gridpos_keys_present(self, filename: str):
        d = load_dashboard(filename)
        for panel in d.get("panels", []):
            gp = panel.get("gridPos", {})
            for key in ("h", "w", "x", "y"):
                assert key in gp, (
                    f"{filename}: panel {panel.get('title')!r} gridPos missing key {key!r}"
                )

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_gridpos_values_are_positive(self, filename: str):
        d = load_dashboard(filename)
        for panel in d.get("panels", []):
            gp = panel.get("gridPos", {})
            assert gp.get("h", 0) > 0, (
                f"{filename}: panel {panel.get('title')!r} gridPos.h must be positive"
            )
            assert gp.get("w", 0) > 0, (
                f"{filename}: panel {panel.get('title')!r} gridPos.w must be positive"
            )
            assert gp.get("x", -1) >= 0, (
                f"{filename}: panel {panel.get('title')!r} gridPos.x must be >= 0"
            )
            assert gp.get("y", -1) >= 0, (
                f"{filename}: panel {panel.get('title')!r} gridPos.y must be >= 0"
            )

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_gridpos_fits_within_24_columns(self, filename: str):
        d = load_dashboard(filename)
        for panel in d.get("panels", []):
            gp = panel.get("gridPos", {})
            right_edge = gp.get("x", 0) + gp.get("w", 0)
            assert right_edge <= GRAFANA_GRID_WIDTH, (
                f"{filename}: panel {panel.get('title')!r} exceeds 24-column grid "
                f"(x={gp.get('x')} + w={gp.get('w')} = {right_edge})"
            )


# ---------------------------------------------------------------------------
# 8. Flux query structure
# ---------------------------------------------------------------------------

class TestFluxQueries:
    """Every panel target must have a valid Flux query."""

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_all_targets_have_queries(self, filename: str):
        d = load_dashboard(filename)
        for panel in d.get("panels", []):
            for i, target in enumerate(panel.get("targets", [])):
                assert target.get("query", "").strip(), (
                    f"{filename}: panel {panel.get('title')!r} target[{i}] has an empty query"
                )

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_all_targets_have_ref_id(self, filename: str):
        d = load_dashboard(filename)
        for panel in d.get("panels", []):
            for i, target in enumerate(panel.get("targets", [])):
                assert target.get("refId", "").strip(), (
                    f"{filename}: panel {panel.get('title')!r} target[{i}] is missing refId"
                )

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_queries_start_with_from_bucket(self, filename: str):
        for query in all_queries(load_dashboard(filename)):
            # Allow variable assignments before from() (e.g. "secure = from(...")
            assert "from(bucket:" in query, (
                f"{filename}: query does not contain 'from(bucket:': {query[:120]!r}"
            )

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_queries_reference_telegraf_bucket(self, filename: str):
        for query in all_queries(load_dashboard(filename)):
            assert f'"{EXPECTED_BUCKET}"' in query, (
                f"{filename}: query does not reference bucket {EXPECTED_BUCKET!r}: {query[:120]!r}"
            )

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_queries_have_range_call(self, filename: str):
        for query in all_queries(load_dashboard(filename)):
            assert "|> range(" in query, (
                f"{filename}: query missing |> range() call: {query[:120]!r}"
            )

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_queries_have_filter_call(self, filename: str):
        for query in all_queries(load_dashboard(filename)):
            assert "|> filter(" in query, (
                f"{filename}: query missing |> filter() call: {query[:120]!r}"
            )

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_queries_have_measurement_filter(self, filename: str):
        for query in all_queries(load_dashboard(filename)):
            assert 'r._measurement ==' in query or 'r["_measurement"] ==' in query, (
                f"{filename}: query does not filter by _measurement: {query[:120]!r}"
            )

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_queries_contain_expected_measurements(self, filename: str):
        queries_text = "\n".join(all_queries(load_dashboard(filename)))
        for measurement in EXPECTED_MEASUREMENTS.get(filename, []):
            assert measurement in queries_text, (
                f"{filename}: no query references measurement {measurement!r}"
            )

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_queries_have_yield_or_aggregate(self, filename: str):
        """Queries should produce output via yield(), aggregateWindow(), or group()."""
        for query in all_queries(load_dashboard(filename)):
            has_output = (
                "|> yield(" in query
                or "|> aggregateWindow(" in query
                or "|> group(" in query
                or "|> sort(" in query
                or "|> limit(" in query
                or "|> last()" in query
                or "|> mean()" in query
                or "|> sum()" in query
                or "|> count()" in query
            )
            assert has_output, (
                f"{filename}: query appears to have no terminal aggregation or yield: {query[:120]!r}"
            )

    @pytest.mark.parametrize("filename", EXPECTED_DASHBOARDS)
    def test_queries_do_not_contain_hardcoded_tokens(self, filename: str):
        """Queries must not embed literal InfluxDB tokens or passwords."""
        token_pattern = re.compile(r'token\s*=\s*"[^$][^"]{10,}"', re.IGNORECASE)
        for query in all_queries(load_dashboard(filename)):
            assert not token_pattern.search(query), (
                f"{filename}: query appears to contain a hardcoded token"
            )


DASHBOARDS_WITH_VARIABLES = {
    "network-overview.json": ["interface"],
    "system-health.json": ["host"],
}


# ---------------------------------------------------------------------------
# 9. Template variables
# ---------------------------------------------------------------------------

class TestTemplateVariables:
    """Dashboards with template variables must declare them correctly."""

    @pytest.mark.parametrize("filename,expected_vars", DASHBOARDS_WITH_VARIABLES.items())
    def test_template_variable_names(self, filename: str, expected_vars: list):
        d = load_dashboard(filename)
        var_names = [v["name"] for v in d.get("templating", {}).get("list", [])]
        for var in expected_vars:
            assert var in var_names, (
                f"{filename}: expected template variable {var!r} not found (found: {var_names})"
            )

    @pytest.mark.parametrize("filename,expected_vars", DASHBOARDS_WITH_VARIABLES.items())
    def test_template_variables_have_required_fields(self, filename: str, expected_vars: list):
        d = load_dashboard(filename)
        for var in d.get("templating", {}).get("list", []):
            assert var.get("name"), f"{filename}: template variable missing 'name'"
            assert var.get("type"), f"{filename}: template variable {var.get('name')!r} missing 'type'"
            assert "query" in var, f"{filename}: template variable {var.get('name')!r} missing 'query'"

    @pytest.mark.parametrize("filename,expected_vars", DASHBOARDS_WITH_VARIABLES.items())
    def test_template_variable_datasource_uses_influxdb(self, filename: str, expected_vars: list):
        d = load_dashboard(filename)
        for var in d.get("templating", {}).get("list", []):
            ds = var.get("datasource", {})
            assert ds.get("uid") == "${DS_INFLUXDB}", (
                f"{filename}: template variable {var.get('name')!r} datasource uid "
                f"should be '${{DS_INFLUXDB}}', got {ds.get('uid')!r}"
            )

    @pytest.mark.parametrize("filename,expected_vars", DASHBOARDS_WITH_VARIABLES.items())
    def test_template_variables_have_non_empty_query(self, filename: str, expected_vars: list):
        d = load_dashboard(filename)
        for var in d.get("templating", {}).get("list", []):
            q = var.get("query", "") or var.get("definition", "")
            assert q.strip(), (
                f"{filename}: template variable {var.get('name')!r} has an empty query"
            )

    @pytest.mark.parametrize("filename", [
        fname for fname in EXPECTED_DASHBOARDS
        if fname not in DASHBOARDS_WITH_VARIABLES
    ])
    def test_dashboards_without_variables_have_empty_templating(self, filename: str):
        d = load_dashboard(filename)
        var_list = d.get("templating", {}).get("list", [])
        assert var_list == [], (
            f"{filename}: expected no template variables but found: "
            f"{[v.get('name') for v in var_list]}"
        )
