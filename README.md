# Grafana Dashboards

My Grafana dashboard collection for monitoring a segmented home network. Built on the TIG stack (Telegraf + InfluxDB + Grafana) running on a Raspberry Pi 5.

These are the dashboards I actually use day-to-day to keep an eye on traffic, firewall activity, DNS queries, and system health across my VLANs.

## Dashboards

| Dashboard | What it shows |
|---|---|
| Network Overview | Traffic per VLAN, bandwidth, top talkers |
| Suricata IDS | Alert severity, top signatures, blocked threats |
| DNS Analytics | Query volume, top domains, blocked domains, DNSSEC stats |
| OPNsense Firewall | Rule hits, state table, interface stats |
| System Health | CPU, memory, disk, temperature across all devices |
| WireGuard VPN | Tunnel status, handshake times, transfer volumes |

Screenshots coming once I have time to anonymize them properly. In the meantime, see [bastiaan365.com](https://bastiaan365.com) for visuals.

## Stack

```
[Network devices] → [Telegraf] → [InfluxDB] → [Grafana]
                       ↑
               SNMP / syslog / API
```

Everything runs on a Pi 5 (8GB). Telegraf collects via SNMP, syslog, and API polling. InfluxDB stores the time-series data. Grafana does the visualization and alerting.

## How to use

1. Import the JSON files from `dashboards/` into your Grafana instance
2. Point them at your InfluxDB datasource
3. Adjust the Telegraf configs in `telegraf/` for your setup
4. Update dashboard variables to match your network segments

The JSON files contain anonymized placeholder datasources — you'll need to swap in your own connection details.

## File structure

```
dashboards/
├── network-overview.json
├── suricata-ids.json
├── dns-analytics.json
├── opnsense-firewall.json
├── system-health.json
└── wireguard-vpn.json
telegraf/
├── telegraf.conf
├── suricata-input.conf
└── snmp-input.conf
```

## Requirements

- Grafana 10.x+
- InfluxDB 2.x
- Telegraf 1.28+

## Related

- [Homelab Infrastructure](https://github.com/bastiaan365/homelab-infrastructure) — the network these dashboards monitor
- [DNS Security Setup](https://github.com/bastiaan365/dns-security-setup) — DNS filtering config that feeds the DNS dashboard
- [IoT Threat Detector](https://github.com/bastiaan365/iot-threat-detector) — anomaly detection that can trigger Grafana alerts

## License

MIT
