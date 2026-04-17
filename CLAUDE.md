# grafana-dashboards

Curated Grafana dashboards and Telegraf configs for a segmented home network on
the TIG stack (Telegraf + InfluxDB + Grafana). Maintained by Bastiaan
([@bastiaan365](https://github.com/bastiaan365)).

This file scopes Claude's behaviour for this repo. The global `~/.claude/CLAUDE.md`
covers personal conventions; everything below is repo-specific.

## Audience and assumptions

- Consumers are homelab operators on TIG stacks (Grafana 10.x+, InfluxDB 2.x, Telegraf 1.28+).
- Dashboards must import cleanly into a fresh Grafana instance with **only datasource UID substitution required**. No hardcoded IPs, hostnames, ASN numbers, MAC addresses, or org-specific labels.
- Telegraf configs must be read as templates, not as my running configs.

## Repo conventions

### Structure

```
dashboards/    <- one .json file per dashboard, kebab-case filename
telegraf/      <- input plugin configs and the main telegraf.conf template
screenshots/   <- one .png per dashboard, same basename as the .json
```

### Dashboard JSON

- **Filename**: `kebab-case.json`, matching the dashboard's `title` (sentence case in title, kebab in filename).
- **Datasource references**: every panel uses a UID like `${DS_PLACEHOLDER}` or named placeholder, never a real UID from my Grafana. Same convention for variables.
- **Panel IDs**: sequential, starting at 1. Don't leave Grafana's auto-generated UUIDs.
- **Time range**: default to `now-6h` unless the dashboard has a real reason to need longer.
- **No embedded credentials**: queries reference variables, not literal tokens or basic-auth strings.
- **No identifying data anywhere**: no `192.168.x.x`, no `niborserver`, no `Nibordooh`, no real MACs, no real WG peer names. Use placeholders like `vlan-iot`, `host-1`, `peer-laptop`.
- **Schema version**: pin to a current Grafana 10.x value; bump deliberately when upgrading.

### Telegraf configs

- Top-of-file comment block: which Grafana dashboard(s) consume this input, and what InfluxDB measurement it produces.
- Connection strings (`url`, `host`, `username`) **always commented as `# REPLACE: ...`** with a placeholder value, never my real ones.
- One file per logical input plugin (`snmp-input.conf`, `suricata-input.conf`, etc.); the main `telegraf.conf` references them via `[[inputs]]` includes if practical.

### Screenshots

- One PNG per dashboard, basename matches the JSON.
- Anonymise everything before commit: mask IP/hostname columns, blur top-talker labels, redact any specific signature names that hint at internal layout.
- 1200×800 or similar 3:2 ratio per `screenshots/README.md`.

### "Tests" (validation, not Pester)

There is no executable test suite in this repo. The validation gates are:

- Every JSON file passes `python3 -m json.tool dashboards/<file>.json > /dev/null` (or `jq .`)
- No hits for known-leak patterns: `grep -REn '192\.168\.|10\.[0-9]+\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|niborserver|Nibordooh|bastiaan@' dashboards/ telegraf/ | grep -vE '"version"\s*:\s*"|^[^:]+:[0-9]+:\s*##'` — the second filter strips Grafana `"version": "10.x.x"` schema lines and `##`-prefixed Telegraf example comments.
- Every `dashboards/*.json` has a matching row in the README dashboards table and (eventually) a screenshot.

Run all three before any commit that touches `dashboards/` or `telegraf/`.

## Workflow expectations for Claude

When I ask you to **add a dashboard**:

1. Read `dashboards/network-overview.json` (or another existing one) as a template.
2. Generate the JSON with placeholder datasource UIDs, sequential panel IDs, and a clear title.
3. Run the validation gates above. Report any anonymisation hits explicitly — don't auto-fix without showing me what you found.
4. Add the row to the README dashboards table.
5. Add a `screenshots/<name>.png` placeholder (note in the diff that the real screenshot is mine to add).

When I ask you to **modify an existing dashboard**:

1. Show the panel-level diff, not the entire JSON file.
2. Bump the dashboard's `version` field in the JSON.
3. Re-run validation gates.

When I ask you to **add or change a Telegraf config**:

1. Confirm which dashboard(s) consume the resulting measurement.
2. Show the input plugin block plus the comment header.
3. Flag any new external dependency (SNMP MIB, syslog tag, API endpoint) explicitly.

When **reviewing existing JSON**:

1. Flag any leaked identifier first, query/panel correctness second, style last.
2. If you find a leaked IP or hostname, do not paste the actual value back — say "found N hits at lines X-Y, type Z" and ask before you do anything.

## Things to avoid

- Pasting real datasource UIDs from my Grafana into the repo, ever.
- Grafana-only panel types from beta plugins — stick to the built-in panel library.
- Single-stat panels with no thresholds (defeats the purpose of an alert-grade view).
- Burying queries inside panels when a `query` variable would be reusable across panels.
- Modifying `screenshots/*.png` files programmatically (those are mine).
- Silently running `gh release` or pushing tags — releases happen by my hand only.

## Related repos

- [`homelab-infrastructure`](https://github.com/bastiaan365/homelab-infrastructure) — the network these dashboards monitor
- [`dns-security-setup`](https://github.com/bastiaan365/dns-security-setup) — DNS layer that feeds the DNS dashboard
- [`iot-threat-detector`](https://github.com/bastiaan365/iot-threat-detector) — anomaly engine that can surface alerts in Grafana

## Drift from target structure

_Claude maintains this section. List anything in the repo that doesn't match the conventions above, with why it's still there and what would need to happen to fix it._

- **All 6 dashboards lack screenshots** — `screenshots/README.md` lists 6 expected PNGs, none committed. Top-level README points readers to `bastiaan365.com` for visuals as a workaround. To fix: export from Grafana, anonymise per `screenshots/README.md`, commit each PNG matching its `.json` basename.
