from routing_monitor.cdr import CDR
from routing_monitor.kpi import KPIWindow, RouteKPI, compute_kpi, rank_routes


def cdr(code, pdd=2.0, duration=0.0, ts=0.0, carrier="a", dest="UK"):
    return CDR(ts, carrier, dest, code, pdd, duration)


def test_compute_kpi():
    calls = [
        cdr(200, pdd=2, duration=100),
        cdr(200, pdd=4, duration=200),
        cdr(486, pdd=3),  # busy: user-caused, counts for NER
        cdr(503, pdd=7),  # network failure
    ]
    k = compute_kpi("a", "UK", calls)
    assert k.attempts == 4
    assert k.asr == 0.5
    assert k.ner == 0.75
    assert k.acd == 150
    assert k.pdd == 4


def test_compute_kpi_empty():
    k = compute_kpi("a", "UK", [])
    assert (k.attempts, k.asr, k.acd) == (0, 0.0, 0.0)


def test_window_expires_old_cdrs():
    now = [1000.0]
    window = KPIWindow(window_seconds=60, clock=lambda: now[0])
    window.add(cdr(200, ts=900, duration=10))  # already outside the window
    window.add(cdr(486, ts=990))
    [k] = window.kpis()
    assert k.attempts == 1
    assert k.asr == 0.0


def kpi(carrier, asr, pdd=2.0, attempts=100, dest="UK"):
    return RouteKPI(carrier, dest, attempts, asr=asr, ner=asr, acd=120, pdd=pdd)


THRESHOLDS = {"min_asr": 0.4, "max_pdd": 6.0}


def test_rank_routes_prefers_cheapest_healthy_carrier():
    costs = {"a": {"UK": 0.02}, "b": {"UK": 0.01}, "c": {"UK": 0.005}}
    plan = rank_routes(
        [kpi("a", 0.5), kpi("b", 0.45), kpi("c", 0.2)], costs, THRESHOLDS, min_attempts=20
    )
    routes = plan["UK"]["routes"]
    assert [r["carrier"] for r in routes] == ["b", "a"]
    assert [r["priority"] for r in routes] == [1, 2]
    [blocked] = plan["UK"]["blocked"]
    assert blocked["carrier"] == "c"
    assert "ASR" in blocked["reasons"][0]


def test_rank_routes_blocks_high_pdd_and_low_traffic():
    costs = {"a": {"UK": 0.01}, "b": {"UK": 0.02}}
    plan = rank_routes(
        [kpi("a", 0.6, pdd=9), kpi("b", 0.6, attempts=5)], costs, THRESHOLDS, min_attempts=20
    )
    assert plan["UK"]["routes"] == []
    reasons = {b["carrier"]: b["reasons"] for b in plan["UK"]["blocked"]}
    assert "PDD" in reasons["a"][0]
    assert "not enough traffic" in reasons["b"][0]
