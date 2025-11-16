from fastapi.testclient import TestClient

from search_api.main import app


def test_health():
    client = TestClient(app)
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_search_basic():
    client = TestClient(app)
    res = client.get("/v1/search?q=hello+world")
    assert res.status_code == 200
    body = res.json()
    assert body["query"] == "hello world"
    assert "results" in body and isinstance(body["results"], list)
    assert body["page"] == 1
    assert body["size"] >= 1


def test_recrawl_lifecycle():
    client = TestClient(app)
    payload = {
        "urls": ["https://example.com/a", "https://example.com/b"],
        "priority": "normal",
        "reason": "test",
    }
    res = client.post("/v1/recrawl", json=payload)
    assert res.status_code == 202
    body = res.json()
    assert "jobs" in body and len(body["jobs"]) == 2
    job_id = body["jobs"][0]["job_id"]

    status_res = client.get(f"/v1/recrawl/{job_id}")
    assert status_res.status_code == 200
    status_body = status_res.json()
    assert status_body["job_id"] == job_id
    assert status_body["status"] in {"queued", "running", "succeeded", "failed", "expired"}


