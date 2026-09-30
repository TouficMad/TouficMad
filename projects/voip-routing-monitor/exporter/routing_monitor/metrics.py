"""Prometheus metrics. Raw counters/histograms are exported so KPIs can be
computed with PromQL over any time range; the window KPIs are exported too."""
from prometheus_client import Counter, Gauge, Histogram

LABELS = ["carrier", "destination"]

CALLS = Counter("voip_calls_total", "Call attempts by final SIP response", LABELS + ["sip_code"])
ANSWERED = Counter("voip_calls_answered_total", "Answered calls", LABELS)
EFFECTIVE = Counter(
    "voip_calls_network_effective_total", "Answered or user-caused failures (for NER)", LABELS
)
DURATION = Histogram(
    "voip_call_duration_seconds",
    "Billable duration of answered calls",
    LABELS,
    buckets=(10, 30, 60, 120, 180, 300, 600, 1200),
)
PDD = Histogram(
    "voip_pdd_seconds", "Post-dial delay", LABELS, buckets=(1, 2, 3, 4, 5, 7, 10, 15)
)

ASR = Gauge("voip_asr_ratio", "ASR over the sliding window", LABELS)
NER = Gauge("voip_ner_ratio", "NER over the sliding window", LABELS)
ACD = Gauge("voip_acd_seconds", "ACD over the sliding window", LABELS)
AVG_PDD = Gauge("voip_avg_pdd_seconds", "Average PDD over the sliding window", LABELS)
ROUTE_PRIORITY = Gauge(
    "voip_route_priority", "LCR priority (1 = preferred, 0 = blocked)", LABELS
)
COST = Gauge("voip_carrier_cost_per_minute", "Configured carrier rate", LABELS)


def record_cdr(cdr):
    labels = (cdr.carrier, cdr.destination)
    CALLS.labels(*labels, str(cdr.sip_code)).inc()
    PDD.labels(*labels).observe(cdr.pdd)
    if cdr.answered:
        ANSWERED.labels(*labels).inc()
        DURATION.labels(*labels).observe(cdr.duration)
    else:
        ANSWERED.labels(*labels)  # make sure the series exists at 0
    if cdr.network_effective:
        EFFECTIVE.labels(*labels).inc()
    else:
        EFFECTIVE.labels(*labels)


def publish_window(kpis, plan):
    for k in kpis:
        labels = (k.carrier, k.destination)
        ASR.labels(*labels).set(k.asr)
        NER.labels(*labels).set(k.ner)
        ACD.labels(*labels).set(k.acd)
        AVG_PDD.labels(*labels).set(k.pdd)
    for dest, entry in plan.items():
        for r in entry["routes"]:
            ROUTE_PRIORITY.labels(r["carrier"], dest).set(r["priority"])
            COST.labels(r["carrier"], dest).set(r["cost_per_min"])
        for r in entry["blocked"]:
            ROUTE_PRIORITY.labels(r["carrier"], dest).set(0)
            if r["cost_per_min"] is not None:
                COST.labels(r["carrier"], dest).set(r["cost_per_min"])
