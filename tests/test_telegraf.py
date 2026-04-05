"""Comprehensive tests for Telegraf configuration files."""

import re
import tomllib
from pathlib import Path

import pytest

from tests.conftest import TELEGRAF_DIR, TELEGRAF_CONF_FILES

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXPECTED_BUCKET = "telegraf"
EXPECTED_ORGANIZATION = "homelab"
INFLUX_URL_PATTERN = re.compile(r"^https?://")
DURATION_PATTERN = re.compile(r'^\d+[smhd]$')

EXPECTED_CONF_FILES = {"telegraf.conf", "snmp-input.conf", "suricata-input.conf"}

EXPECTED_SYSTEM_INPUTS = {"cpu", "mem", "disk", "diskio", "net", "system", "processes", "temp"}
EXPECTED_SYSLOG_INPUTS = {"syslog"}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def load_toml(filename: str) -> dict:
    path = TELEGRAF_DIR / filename
    with path.open("rb") as f:
        return tomllib.load(f)


def first(toml_section) -> dict:
    """Return the first item when a TOML [[array of tables]] is parsed as a list."""
    if isinstance(toml_section, list):
        return toml_section[0] if toml_section else {}
    if isinstance(toml_section, dict):
        return toml_section
    return {}


# ---------------------------------------------------------------------------
# 1. File presence and TOML validity
# ---------------------------------------------------------------------------

class TestTelegrafFilePresence:
    def test_expected_conf_files_exist(self):
        actual = {p.name for p in TELEGRAF_CONF_FILES}
        for expected in EXPECTED_CONF_FILES:
            assert expected in actual, f"Expected telegraf config file {expected!r} is missing"

    @pytest.mark.parametrize("path", TELEGRAF_CONF_FILES, ids=[p.name for p in TELEGRAF_CONF_FILES])
    def test_conf_file_is_valid_toml(self, path: Path):
        with path.open("rb") as f:
            data = tomllib.load(f)
        assert isinstance(data, dict), f"{path.name} should parse as a TOML dict"

    @pytest.mark.parametrize("path", TELEGRAF_CONF_FILES, ids=[p.name for p in TELEGRAF_CONF_FILES])
    def test_conf_file_is_not_empty(self, path: Path):
        assert path.stat().st_size > 0, f"{path.name} must not be an empty file"


# ---------------------------------------------------------------------------
# 2. Main telegraf.conf — global tags and agent settings
# ---------------------------------------------------------------------------

class TestMainTelegrafConf:
    def test_global_tags_present(self):
        d = load_toml("telegraf.conf")
        assert "global_tags" in d, "telegraf.conf must have [global_tags]"

    def test_global_tags_environment_set(self):
        d = load_toml("telegraf.conf")
        env = d.get("global_tags", {}).get("environment", "")
        assert env, "global_tags.environment must be set"

    def test_agent_section_present(self):
        d = load_toml("telegraf.conf")
        assert "agent" in d, "telegraf.conf must have an [agent] section"

    def test_agent_interval_set(self):
        d = load_toml("telegraf.conf")
        interval = d.get("agent", {}).get("interval", "")
        assert interval, "agent.interval must be set"
        assert DURATION_PATTERN.match(interval), (
            f"agent.interval {interval!r} should be a duration like '10s'"
        )

    def test_agent_flush_interval_set(self):
        d = load_toml("telegraf.conf")
        fi = d.get("agent", {}).get("flush_interval", "")
        assert fi, "agent.flush_interval must be set"
        assert DURATION_PATTERN.match(fi), (
            f"agent.flush_interval {fi!r} should be a duration like '10s'"
        )

    def test_agent_round_interval(self):
        d = load_toml("telegraf.conf")
        assert d.get("agent", {}).get("round_interval") is True, (
            "agent.round_interval should be true"
        )

    def test_agent_metric_batch_size_positive(self):
        d = load_toml("telegraf.conf")
        batch = d.get("agent", {}).get("metric_batch_size", 0)
        assert batch > 0, "agent.metric_batch_size must be a positive integer"

    def test_agent_metric_buffer_limit_positive(self):
        d = load_toml("telegraf.conf")
        buf = d.get("agent", {}).get("metric_buffer_limit", 0)
        assert buf > 0, "agent.metric_buffer_limit must be a positive integer"

    def test_agent_buffer_limit_greater_than_batch_size(self):
        d = load_toml("telegraf.conf")
        agent = d.get("agent", {})
        batch = agent.get("metric_batch_size", 0)
        buf = agent.get("metric_buffer_limit", 0)
        assert buf > batch, (
            f"metric_buffer_limit ({buf}) must be greater than metric_batch_size ({batch})"
        )


# ---------------------------------------------------------------------------
# 3. InfluxDB v2 output plugin
# ---------------------------------------------------------------------------

class TestInfluxDBOutput:
    def test_outputs_influxdb_v2_present(self):
        d = load_toml("telegraf.conf")
        assert "outputs" in d and "influxdb_v2" in d["outputs"], (
            "telegraf.conf must have [[outputs.influxdb_v2]]"
        )

    def test_output_has_urls(self):
        d = load_toml("telegraf.conf")
        output = first(d["outputs"]["influxdb_v2"])
        urls = output.get("urls", [])
        assert urls, "outputs.influxdb_v2 must have at least one URL"

    def test_output_url_format(self):
        d = load_toml("telegraf.conf")
        output = first(d["outputs"]["influxdb_v2"])
        for url in output.get("urls", []):
            assert INFLUX_URL_PATTERN.match(url), (
                f"outputs.influxdb_v2 URL {url!r} must start with http:// or https://"
            )

    def test_output_bucket_matches_dashboards(self):
        d = load_toml("telegraf.conf")
        output = first(d["outputs"]["influxdb_v2"])
        bucket = output.get("bucket", "")
        assert bucket == EXPECTED_BUCKET, (
            f"outputs.influxdb_v2 bucket should be {EXPECTED_BUCKET!r}, got {bucket!r}"
        )

    def test_output_organization_set(self):
        d = load_toml("telegraf.conf")
        output = first(d["outputs"]["influxdb_v2"])
        org = output.get("organization", "")
        assert org == EXPECTED_ORGANIZATION, (
            f"outputs.influxdb_v2 organization should be {EXPECTED_ORGANIZATION!r}, got {org!r}"
        )

    def test_output_token_uses_env_variable(self):
        """Token must be set via environment variable, not hardcoded."""
        d = load_toml("telegraf.conf")
        output = first(d["outputs"]["influxdb_v2"])
        token = output.get("token", "")
        assert token.startswith("${") and token.endswith("}"), (
            f"outputs.influxdb_v2 token should be an env-var reference like ${{INFLUX_TOKEN}}, "
            f"got {token!r}"
        )

    def test_output_timeout_set(self):
        d = load_toml("telegraf.conf")
        output = first(d["outputs"]["influxdb_v2"])
        timeout = output.get("timeout", "")
        assert timeout, "outputs.influxdb_v2 timeout must be set"
        assert DURATION_PATTERN.match(timeout), (
            f"outputs.influxdb_v2 timeout {timeout!r} should be a duration like '5s'"
        )


# ---------------------------------------------------------------------------
# 4. System input plugins in telegraf.conf
# ---------------------------------------------------------------------------

class TestSystemInputPlugins:
    def test_inputs_section_present(self):
        d = load_toml("telegraf.conf")
        assert "inputs" in d, "telegraf.conf must have at least one [[inputs.*]] section"

    @pytest.mark.parametrize("plugin", sorted(EXPECTED_SYSTEM_INPUTS))
    def test_expected_input_plugin_present(self, plugin: str):
        d = load_toml("telegraf.conf")
        inputs = d.get("inputs", {})
        assert plugin in inputs, (
            f"telegraf.conf must have [[inputs.{plugin}]] defined"
        )

    @pytest.mark.parametrize("plugin", sorted(EXPECTED_SYSLOG_INPUTS))
    def test_syslog_input_present(self, plugin: str):
        d = load_toml("telegraf.conf")
        inputs = d.get("inputs", {})
        assert plugin in inputs, (
            f"telegraf.conf must have [[inputs.{plugin}]] defined"
        )

    def test_disk_input_ignores_virtual_filesystems(self):
        d = load_toml("telegraf.conf")
        disk = first(d.get("inputs", {}).get("disk", [{}]))
        ignore_fs = disk.get("ignore_fs", [])
        assert ignore_fs, "inputs.disk should have ignore_fs set to exclude virtual filesystems"
        assert "tmpfs" in ignore_fs, "inputs.disk.ignore_fs should include 'tmpfs'"

    def test_cpu_input_totalcpu_enabled(self):
        d = load_toml("telegraf.conf")
        cpu = first(d.get("inputs", {}).get("cpu", [{}]))
        assert cpu.get("totalcpu") is True, "inputs.cpu.totalcpu should be true"

    def test_net_input_ignores_protocol_stats(self):
        d = load_toml("telegraf.conf")
        net = first(d.get("inputs", {}).get("net", [{}]))
        assert net.get("ignore_protocol_stats") is True, (
            "inputs.net.ignore_protocol_stats should be true"
        )

    def test_syslog_server_address_set(self):
        d = load_toml("telegraf.conf")
        syslog = first(d.get("inputs", {}).get("syslog", [{}]))
        server = syslog.get("server", "")
        assert server, "inputs.syslog server must be configured"
        assert re.match(r"^(udp|tcp)://", server), (
            f"inputs.syslog server {server!r} should start with 'udp://' or 'tcp://'"
        )

    def test_syslog_best_effort_enabled(self):
        d = load_toml("telegraf.conf")
        syslog = first(d.get("inputs", {}).get("syslog", [{}]))
        assert syslog.get("best_effort") is True, (
            "inputs.syslog.best_effort should be true for tolerance of malformed messages"
        )


# ---------------------------------------------------------------------------
# 5. SNMP input config (snmp-input.conf)
# ---------------------------------------------------------------------------

class TestSnmpInputConf:
    def test_snmp_input_section_present(self):
        d = load_toml("snmp-input.conf")
        assert "inputs" in d and "snmp" in d["inputs"], (
            "snmp-input.conf must have [[inputs.snmp]]"
        )

    def test_snmp_name_override(self):
        d = load_toml("snmp-input.conf")
        snmp = first(d["inputs"]["snmp"])
        assert snmp.get("name") == "snmp_opnsense", (
            "inputs.snmp name should be 'snmp_opnsense'"
        )

    def test_snmp_agents_configured(self):
        d = load_toml("snmp-input.conf")
        snmp = first(d["inputs"]["snmp"])
        agents = snmp.get("agents", [])
        assert agents, "inputs.snmp must have at least one agent configured"

    def test_snmp_version_is_2_or_3(self):
        d = load_toml("snmp-input.conf")
        snmp = first(d["inputs"]["snmp"])
        version = snmp.get("version")
        assert version in (2, 3), (
            f"inputs.snmp version should be 2 or 3, got {version!r}"
        )

    def test_snmp_community_uses_env_variable(self):
        d = load_toml("snmp-input.conf")
        snmp = first(d["inputs"]["snmp"])
        community = snmp.get("community", "")
        assert community.startswith("${") and community.endswith("}"), (
            f"inputs.snmp community should be an env-var reference, got {community!r}"
        )

    def test_snmp_interval_set(self):
        d = load_toml("snmp-input.conf")
        snmp = first(d["inputs"]["snmp"])
        interval = snmp.get("interval", "")
        assert DURATION_PATTERN.match(interval), (
            f"inputs.snmp interval {interval!r} should be a duration string"
        )

    def test_snmp_timeout_set(self):
        d = load_toml("snmp-input.conf")
        snmp = first(d["inputs"]["snmp"])
        timeout = snmp.get("timeout", "")
        assert DURATION_PATTERN.match(timeout), (
            f"inputs.snmp timeout {timeout!r} should be a duration string"
        )

    def test_snmp_retries_positive(self):
        d = load_toml("snmp-input.conf")
        snmp = first(d["inputs"]["snmp"])
        retries = snmp.get("retries", 0)
        assert retries > 0, "inputs.snmp retries must be a positive integer"

    def test_snmp_fields_defined(self):
        d = load_toml("snmp-input.conf")
        snmp = first(d["inputs"]["snmp"])
        fields = snmp.get("field", [])
        assert fields, "inputs.snmp must define at least one [[inputs.snmp.field]]"

    def test_snmp_table_defined(self):
        d = load_toml("snmp-input.conf")
        snmp = first(d["inputs"]["snmp"])
        tables = snmp.get("table", [])
        assert tables, "inputs.snmp must define at least one [[inputs.snmp.table]]"

    def test_snmp_table_interface_defined(self):
        d = load_toml("snmp-input.conf")
        snmp = first(d["inputs"]["snmp"])
        table_names = [t.get("name") for t in snmp.get("table", [])]
        assert "snmp_interface" in table_names, (
            "inputs.snmp must include an 'snmp_interface' table for interface metrics"
        )

    def test_snmp_uptime_field_has_oid(self):
        d = load_toml("snmp-input.conf")
        snmp = first(d["inputs"]["snmp"])
        uptime_fields = [f for f in snmp.get("field", []) if f.get("name") == "uptime"]
        assert uptime_fields, "inputs.snmp must define a field named 'uptime'"
        assert uptime_fields[0].get("oid"), "inputs.snmp uptime field must have an OID"

    def test_snmp_interface_table_has_fields(self):
        d = load_toml("snmp-input.conf")
        snmp = first(d["inputs"]["snmp"])
        for table in snmp.get("table", []):
            if table.get("name") == "snmp_interface":
                assert table.get("field"), (
                    "snmp_interface table must define sub-fields"
                )
                break


# ---------------------------------------------------------------------------
# 6. Suricata input config (suricata-input.conf)
# ---------------------------------------------------------------------------

class TestSuricataInputConf:
    def test_tail_input_section_present(self):
        d = load_toml("suricata-input.conf")
        assert "inputs" in d and "tail" in d["inputs"], (
            "suricata-input.conf must have [[inputs.tail]]"
        )

    def test_name_override_is_suricata(self):
        d = load_toml("suricata-input.conf")
        tail = first(d["inputs"]["tail"])
        assert tail.get("name_override") == "suricata", (
            f"inputs.tail name_override should be 'suricata', got {tail.get('name_override')!r}"
        )

    def test_suricata_log_file_configured(self):
        d = load_toml("suricata-input.conf")
        tail = first(d["inputs"]["tail"])
        files = tail.get("files", [])
        assert files, "inputs.tail must specify at least one log file path"
        assert any("suricata" in f or "eve" in f for f in files), (
            "inputs.tail files should reference the Suricata EVE log"
        )

    def test_data_format_is_json(self):
        d = load_toml("suricata-input.conf")
        tail = first(d["inputs"]["tail"])
        fmt = tail.get("data_format", "")
        assert fmt == "json", (
            f"inputs.tail data_format should be 'json' for Suricata EVE, got {fmt!r}"
        )

    def test_json_time_key_set(self):
        d = load_toml("suricata-input.conf")
        tail = first(d["inputs"]["tail"])
        key = tail.get("json_time_key", "")
        assert key == "timestamp", (
            f"inputs.tail json_time_key should be 'timestamp', got {key!r}"
        )

    def test_json_time_format_set(self):
        d = load_toml("suricata-input.conf")
        tail = first(d["inputs"]["tail"])
        fmt = tail.get("json_time_format", "")
        assert fmt, "inputs.tail json_time_format must be set to parse Suricata timestamps"

    def test_tag_keys_include_alert_fields(self):
        d = load_toml("suricata-input.conf")
        tail = first(d["inputs"]["tail"])
        tag_keys = tail.get("tag_keys", [])
        assert tag_keys, "inputs.tail tag_keys must be set"
        expected_tags = {"event_type", "src_ip", "dest_ip", "proto"}
        for tag in expected_tags:
            assert tag in tag_keys, (
                f"inputs.tail tag_keys should include {tag!r}"
            )

    def test_fieldpass_includes_alert_severity(self):
        d = load_toml("suricata-input.conf")
        tail = first(d["inputs"]["tail"])
        fieldpass = tail.get("fieldpass", [])
        assert "alert_severity" in fieldpass, (
            "inputs.tail fieldpass should include 'alert_severity'"
        )

    def test_watch_method_set(self):
        d = load_toml("suricata-input.conf")
        tail = first(d["inputs"]["tail"])
        watch = tail.get("watch_method", "")
        assert watch, "inputs.tail watch_method must be configured"


