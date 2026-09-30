"""Task tracker API instrumented with Prometheus metrics."""
import os
import threading
import time
from itertools import count

from flask import Flask, Response, g, jsonify, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

REQUESTS = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)
LATENCY = Histogram(
    "http_request_duration_seconds", "HTTP request latency", ["method", "endpoint"]
)
TASKS = Gauge("tasks_total", "Number of tasks currently stored")


def create_app():
    app = Flask(__name__)
    tasks = {}
    ids = count(1)
    lock = threading.Lock()

    @app.before_request
    def start_timer():
        g.start = time.perf_counter()

    @app.after_request
    def record_metrics(response):
        endpoint = request.url_rule.rule if request.url_rule else "unmatched"
        if endpoint != "/metrics":
            LATENCY.labels(request.method, endpoint).observe(time.perf_counter() - g.start)
            REQUESTS.labels(request.method, endpoint, response.status_code).inc()
        return response

    @app.get("/")
    def index():
        return jsonify(
            service="taskapp",
            version=os.getenv("APP_VERSION", "dev"),
            environment=os.getenv("APP_ENV", "local"),
        )

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.get("/metrics")
    def metrics():
        return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    @app.get("/api/tasks")
    def list_tasks():
        with lock:
            return jsonify(list(tasks.values()))

    @app.post("/api/tasks")
    def create_task():
        data = request.get_json(silent=True) or {}
        title = str(data.get("title", "")).strip()
        if not title:
            return jsonify(error="title is required"), 400
        with lock:
            task = {"id": next(ids), "title": title, "done": False}
            tasks[task["id"]] = task
            TASKS.set(len(tasks))
        return jsonify(task), 201

    @app.get("/api/tasks/<int:task_id>")
    def get_task(task_id):
        with lock:
            task = tasks.get(task_id)
        if task is None:
            return jsonify(error="not found"), 404
        return jsonify(task)

    @app.patch("/api/tasks/<int:task_id>")
    def update_task(task_id):
        data = request.get_json(silent=True) or {}
        with lock:
            task = tasks.get(task_id)
            if task is None:
                return jsonify(error="not found"), 404
            if "title" in data:
                title = str(data["title"]).strip()
                if not title:
                    return jsonify(error="title cannot be empty"), 400
                task["title"] = title
            if "done" in data:
                task["done"] = bool(data["done"])
            return jsonify(task)

    @app.delete("/api/tasks/<int:task_id>")
    def delete_task(task_id):
        with lock:
            if tasks.pop(task_id, None) is None:
                return jsonify(error="not found"), 404
            TASKS.set(len(tasks))
        return "", 204

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
