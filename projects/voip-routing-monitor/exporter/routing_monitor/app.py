"""HTTP service: Prometheus metrics, KPI API, routing plan and incident injection."""
import csv
import logging
import os
import threading

import yaml
from flask import Flask, Response, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from . import metrics
from .cdr import CDR
from .kpi import KPIWindow, rank_routes
from .simulator import Simulator

log = logging.getLogger("routing_monitor")


def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)


def carrier_costs(config):
    return {
        carrier: {dest: d["cost_per_min"] for dest, d in profile["destinations"].items()}
        for carrier, profile in config["carriers"].items()
    }


def create_app(config, window=None, simulator=None):
    app = Flask(__name__)
    window = window or KPIWindow(config["kpi"]["window_seconds"])
    costs = carrier_costs(config)
    thresholds = config["thresholds"]
    min_attempts = config["kpi"]["min_attempts"]

    def ingest(cdr: CDR):
        window.add(cdr)
        metrics.record_cdr(cdr)

    def current_plan():
        kpis = window.kpis()
        plan = rank_routes(kpis, costs, thresholds, min_attempts)
        metrics.publish_window(kpis, plan)
        return kpis, plan

    app.ingest = ingest

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.get("/metrics")
    def prometheus_metrics():
        current_plan()  # refresh window gauges on every scrape
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    @app.get("/api/kpis")
    def kpis():
        return jsonify([k.to_dict() for k in current_plan()[0]])

    @app.get("/api/routing-plan")
    def routing_plan():
        return jsonify(current_plan()[1])

    @app.post("/api/cdrs")
    def post_cdrs():
        rows = request.get_json(silent=True)
        if not isinstance(rows, list):
            return jsonify(error="expected a JSON list of CDRs"), 400
        try:
            cdrs = [CDR.from_row(r) for r in rows]
        except (KeyError, TypeError, ValueError) as exc:
            return jsonify(error=f"invalid CDR: {exc}"), 400
        for cdr in cdrs:
            ingest(cdr)
        return jsonify(accepted=len(cdrs)), 202

    @app.get("/api/incidents")
    def list_incidents():
        return jsonify(simulator.incidents() if simulator else {})

    @app.post("/api/incidents/<carrier>")
    def start_incident(carrier):
        if simulator is None:
            return jsonify(error="simulator disabled"), 409
        body = request.get_json(silent=True) or {}
        try:
            simulator.set_incident(
                carrier,
                asr_drop=float(body.get("asr_drop", 0.4)),
                extra_pdd=float(body.get("extra_pdd", 6.0)),
            )
        except KeyError:
            return jsonify(error=f"unknown carrier {carrier}"), 404
        log.warning("incident started on %s", carrier)
        return jsonify(simulator.incidents()), 201

    @app.delete("/api/incidents/<carrier>")
    def stop_incident(carrier):
        if simulator is None:
            return jsonify(error="simulator disabled"), 409
        simulator.clear_incident(carrier)
        log.warning("incident cleared on %s", carrier)
        return "", 204

    return app


def replay_csv(path, ingest):
    with open(path, newline="") as f:
        count = 0
        for row in csv.DictReader(f):
            ingest(CDR.from_row(row))
            count += 1
    log.info("replayed %d CDRs from %s", count, path)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config = load_config(os.getenv("CONFIG_PATH", "config.yaml"))

    simulator = None
    if os.getenv("SIMULATE", "true").lower() == "true":
        simulator = Simulator(config)

    app = create_app(config, simulator=simulator)

    if os.getenv("CDR_FILE"):
        replay_csv(os.environ["CDR_FILE"], app.ingest)

    if simulator:
        rate = float(os.getenv("CALLS_PER_SECOND", config["simulator"]["calls_per_second"]))
        stop = threading.Event()
        threading.Thread(target=simulator.run, args=(app.ingest, rate, stop), daemon=True).start()
        log.info("simulator generating %.1f calls/s", rate)

    from waitress import serve

    serve(app, host="0.0.0.0", port=int(os.getenv("PORT", "9200")))


if __name__ == "__main__":
    main()
