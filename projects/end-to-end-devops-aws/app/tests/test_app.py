import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_index_reports_service(client):
    assert client.get("/").get_json()["service"] == "taskapp"


def test_create_and_list_tasks(client):
    resp = client.post("/api/tasks", json={"title": "Write Terraform"})
    assert resp.status_code == 201
    task = resp.get_json()
    assert task == {"id": 1, "title": "Write Terraform", "done": False}
    assert client.get("/api/tasks").get_json() == [task]


def test_create_requires_title(client):
    assert client.post("/api/tasks", json={}).status_code == 400
    assert client.post("/api/tasks", json={"title": "   "}).status_code == 400


def test_update_task(client):
    client.post("/api/tasks", json={"title": "Deploy"})
    resp = client.patch("/api/tasks/1", json={"done": True})
    assert resp.status_code == 200
    assert resp.get_json()["done"] is True


def test_missing_task_returns_404(client):
    assert client.get("/api/tasks/99").status_code == 404
    assert client.patch("/api/tasks/99", json={"done": True}).status_code == 404
    assert client.delete("/api/tasks/99").status_code == 404


def test_delete_task(client):
    client.post("/api/tasks", json={"title": "Temp"})
    assert client.delete("/api/tasks/1").status_code == 204
    assert client.get("/api/tasks").get_json() == []


def test_metrics_exposed(client):
    client.get("/health")
    body = client.get("/metrics").get_data(as_text=True)
    assert "http_requests_total" in body
    assert "http_request_duration_seconds" in body
