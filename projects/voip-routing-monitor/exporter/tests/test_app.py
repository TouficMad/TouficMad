import pytest

from routing_monitor.app import create_app
from routing_monitor.kpi import KPIWindow
from routing_monitor.simulator import Simulator


@pytest.fixture
def client(config):
    sim = Simulator(config, seed=7)
    app = create_app(config, window=KPIWindow(10**9), simulator=sim)
    for _ in range(3000):
        app.ingest(sim.generate())
    return app.test_client()


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_kpis_endpoint(client):
    kpis = client.get("/api/kpis").get_json()
    assert {k["carrier"] for k in kpis} == {"carrier-alpha", "carrier-bravo", "carrier-charlie"}
    assert all(0 <= k["asr"] <= 1 for k in kpis)


def test_routing_plan_orders_by_cost(client):
    plan = client.get("/api/routing-plan").get_json()
    fr = [r["carrier"] for r in plan["FR-Fixed"]["routes"]]
    assert fr == ["carrier-alpha", "carrier-bravo"]  # alpha is cheaper


def test_metrics_endpoint(client):
    body = client.get("/metrics").get_data(as_text=True)
    for name in ("voip_calls_total", "voip_pdd_seconds_bucket", "voip_asr_ratio",
                 "voip_route_priority"):
        assert name in body


def test_post_cdrs(client):
    rows = [{"timestamp": 1, "carrier": "carrier-alpha", "destination": "UK-Mobile",
             "sip_code": 200, "pdd": 2.1, "duration": 60}]
    assert client.post("/api/cdrs", json=rows).status_code == 202
    assert client.post("/api/cdrs", json={"bad": 1}).status_code == 400
    assert client.post("/api/cdrs", json=[{"carrier": "x"}]).status_code == 400


def test_incident_lifecycle(client):
    assert client.post("/api/incidents/carrier-alpha", json={}).status_code == 201
    assert "carrier-alpha" in client.get("/api/incidents").get_json()
    assert client.delete("/api/incidents/carrier-alpha").status_code == 204
    assert client.post("/api/incidents/unknown").status_code == 404
