# 📊 Grafana Dashboards

Custom Grafana dashboards for monitoring a segmented home network with OPNsense, Suricata and various services. Built on the TIG stack (Telegraf, InfluxDB, Grafana) running on Raspberry Pi.

## 📈 Dashboards

| Dashboard | Description |
|---|---|
| Network Overview | Traffic per VLAN, bandwidth usage, top talkers |
| Suricata IDS | Alert severity, top signatures, blocked threats |
| DNS Analytics | Query volume, top domains, blocked domains, DNSSEC stats |
| OPNsense Firewall | Rule hits, state table, interface stats |
| System Health | CPU, memory, disk, temperature for all devices |
| WireGuard VPN | Tunnel status, handshake times, data transferred |

## 📸 Screenshots

Screenshots will be added once available. All dashboards display anonymized sample data. See [bastiaan365.com](https://bastiaan365.com) for a full write-up and visuals.
## 🏗️ Stack

```text
[Network Devices] → [Telegraf] → [InfluxDB] → [Grafana]
     ↓                  ↓
  Syslog          SNMP / API
```

- **Telegraf** — Collects metrics via SNMP, syslog, and API polling
- **InfluxDB** — Time-series database for all metrics
- **Grafana** — Visualization and alerting
- **Platform** — Raspberry Pi 5 (8GB)

## 🚀 Usage

1. Import JSON files from `dashboards/` into your Grafana instance
2. Configure InfluxDB datasource
3. Adjust Telegraf configs from `telegraf/` for your environment
4. Update variables in each dashboard to match your network segments

## 📁 Structure

```
├── dashboards/
│   ├── network-overview.json
│   ├── suricata-ids.json
│   ├── dns-analytics.json
│   ├── opnsense-firewall.json
│   ├── system-health.json
│   └── wireguard-vpn.json
├── telegraf/
│   ├── telegraf.conf
│   ├── suricata-input.conf
│   └── snmp-input.conf
└── screenshots/
```

## 📋 Requirements

- Grafana 10.x+
- InfluxDB 2.x
- Telegraf 1.28+

## 🔗 Related

- [Homelab Infrastructure](https://github.com/bastiaan365/homelab-infrastructure) — Network architecture these dashboards monitor
- [bastiaan365.com](https://bastiaan365.com) — Full homelab write-up

---

*Dashboard JSON files contain anonymized data sources. Update connection strings for your environment.*
