from routing_monitor.kpi import compute_kpi
from routing_monitor.simulator import Simulator


def test_generated_asr_matches_profile(config):
    sim = Simulator(config, seed=42)
    cdrs = [sim.generate(now=0) for _ in range(20000)]
    subset = [c for c in cdrs if c.carrier == "carrier-alpha" and c.destination == "FR-Fixed"]
    k = compute_kpi("carrier-alpha", "FR-Fixed", subset)
    assert abs(k.asr - 0.60) < 0.05


def test_incident_degrades_carrier(config):
    sim = Simulator(config, seed=1)
    sim.set_incident("carrier-bravo", asr_drop=0.4, extra_pdd=6)
    cdrs = [sim.generate(now=0) for _ in range(20000)]
    subset = [c for c in cdrs if c.carrier == "carrier-bravo" and c.destination == "UK-Mobile"]
    k = compute_kpi("carrier-bravo", "UK-Mobile", subset)
    assert k.asr < 0.2
    assert k.pdd > 7
    sim.clear_incident("carrier-bravo")
    assert sim.incidents() == {}
