# VoIP Routing Monitor

Monitoring and **least-cost routing (LCR)** for voice carriers, built the way a DevOps/SRE team would run it. A Python exporter turns call detail records (CDRs) into the KPIs routing teams use every day: **ASR, NER, ACD and PDD**. It publishes them to **Prometheus**, fires alerts through **Alertmanager** when a carrier degrades, and shows everything in **Grafana**, including a live routing plan that drops bad carriers automatically.

This project combines my background running voice routing for a telecom operator with the DevOps tooling I'm learning.

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?logo=prometheus&logoColor=white)
![Grafana](https://img.shields.io/badge/Grafana-F46800?logo=grafana&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?logo=githubactions&logoColor=white)

## Why

On a voice network, a carrier can quietly start failing calls: congestion (SIP 503), long post-dial delay, or "false answer" routes. Without monitoring, customers notice before the NOC does. This stack:

1. Measures each **carrier × destination** route continuously
2. **Alerts** when ASR, NER or PDD crosses a threshold
3. Recomputes the **routing plan**: the cheapest carriers that still meet the quality floor go first, and failing ones are blocked with the reason

## Architecture

```
 CDRs (switch / SBC / CSV / simulator)
          │
          ▼
 ┌─────────────────────┐   /metrics   ┌────────────┐  alerts  ┌──────────────┐
 │  routing-monitor    │◄─────────────│ Prometheus │─────────►│ Alertmanager │──► Slack / email
 │  (Python exporter)  │              │  recording │          └──────────────┘
 │  • KPI window       │              │  + alert   │
 │  • LCR routing plan │              │    rules   │◄──── Grafana dashboards
 │  • REST API         │              └────────────┘
 └─────────────────────┘
```

## KPIs

| KPI | Meaning | Formula |
|---|---|---|
| **ASR** | Answer Seizure Ratio | answered calls / call attempts |
| **NER** | Network Effectiveness Ratio | (answered + busy/no-answer/rejected by user) / attempts. Leaves out user behaviour, so it isolates **network** failures |
| **ACD** | Average Call Duration | total billable seconds / answered calls |
| **PDD** | Post-Dial Delay | time from INVITE to ringing (p95 reported) |

SIP classification: `200` answered; `480, 486, 487, 603` user-caused; everything else (`503`, `404`, …) counts as a network failure.

## Quick start

```bash
git clone https://github.com/TouficMad/voip-routing-monitor.git
cd voip-routing-monitor
docker compose up --build
```

| Service | URL |
|---|---|
| Grafana (admin / admin): **Voice Routing Quality** dashboard | http://localhost:3000 |
| Prometheus | http://localhost:9090 |
| Alertmanager | http://localhost:9093 |
| Exporter API | http://localhost:9200 |

A built-in simulator generates about 20 calls/s across three carriers and three destinations, using realistic SIP response mixes.

### Simulate a carrier outage

```bash
# carrier-bravo starts failing: ASR drops 40 points, PDD +6s, mostly SIP 503
curl -X POST localhost:9200/api/incidents/carrier-bravo \
  -H 'Content-Type: application/json' -d '{"asr_drop": 0.4, "extra_pdd": 6}'
```

Within a few minutes:
- ASR/NER/PDD panels for `carrier-bravo` turn red
- `VoipLowASR`, `VoipLowNER` and `VoipHighPDD` fire in Alertmanager
- The routing plan blocks `carrier-bravo` and moves traffic to the next cheapest healthy carrier

```bash
curl -s localhost:9200/api/routing-plan | jq '.["UK-Mobile"]'
curl -X DELETE localhost:9200/api/incidents/carrier-bravo   # recover
```

## API

| Method | Path | Description |
|---|---|---|
| GET | `/metrics` | Prometheus metrics |
| GET | `/api/kpis` | ASR, NER, ACD, PDD per route over the sliding window (5 min) |
| GET | `/api/routing-plan` | LCR plan per destination: eligible routes by priority, blocked routes with reasons |
| POST | `/api/cdrs` | Ingest CDRs as JSON: `[{"timestamp", "carrier", "destination", "sip_code", "pdd", "duration"}]` |
| GET / POST / DELETE | `/api/incidents[/<carrier>]` | Inject or clear a simulated carrier degradation |

Example routing plan:

```json
"LB-Mobile": {
  "routes": [
    {"priority": 1, "carrier": "carrier-alpha", "cost_per_min": 0.11,  "asr": 0.46, "pdd": 3.9},
    {"priority": 2, "carrier": "carrier-bravo", "cost_per_min": 0.125, "asr": 0.48, "pdd": 3.5}
  ],
  "blocked": [
    {"carrier": "carrier-charlie", "cost_per_min": 0.095, "asr": 0.39, "reasons": ["ASR 39% < 40%"]}
  ]
}
```

### Using real CDRs

- **Live:** have your SBC or billing system `POST` CDRs to `/api/cdrs`, or set `SIMULATE=false` to turn off the simulator.
- **Replay a CSV:** set `CDR_FILE=/data/your_cdrs.csv` in `docker-compose.yml` (see [`samples/sample_cdrs.csv`](samples/sample_cdrs.csv) for the format). Replayed CDRs feed the Prometheus counters. The 5-minute KPI window and routing plan only count CDRs whose timestamps fall inside the window.

Carrier rates, destinations and thresholds live in [`exporter/config.yaml`](exporter/config.yaml).

## Prometheus rules

- **Recording rules** ([recording.yml](monitoring/prometheus/rules/recording.yml)) compute ASR, NER, ACD, p95 PDD and minutes per route from raw counters and histograms, so they work over any time range.
- **Alert rules** ([alerts.yml](monitoring/prometheus/rules/alerts.yml)): `VoipLowASR`, `VoipLowNER`, `VoipHighPDD`, `VoipRouteBlocked`, `VoipNoTraffic`, `RoutingMonitorDown`.
- **Alert unit tests** ([alerts_test.yml](monitoring/prometheus/tests/alerts_test.yml)) are run with `promtool test rules` in CI.

## CI/CD

GitHub Actions runs on every push:

1. `flake8` + `pytest` (KPI maths, LCR ranking, simulator, API)
2. `promtool check rules`, `promtool test rules`, `amtool check-config`
3. Docker build and smoke test, then push to **GitHub Container Registry** from `main`

## Project layout

```
exporter/
  routing_monitor/  cdr.py · kpi.py (window + LCR) · simulator.py · metrics.py · app.py
  tests/
  config.yaml       carriers, rates, thresholds
monitoring/
  prometheus/       scrape config, recording + alert rules, rule unit tests
  alertmanager/     routing, Slack example, inhibition
  grafana/          provisioned datasource and dashboard
samples/            example CDR file
docker-compose.yml
```

## Roadmap

- [ ] Parse CDRs directly from Kamailio / FreeSWITCH logs
- [ ] Push the routing plan to the softswitch (e.g. Kamailio `drouting` table)
- [ ] Deploy on Kubernetes with Helm and a ServiceMonitor
- [ ] Anomaly detection on ASR per destination (seasonality aware)
