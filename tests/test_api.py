def test_root_increments(client):
    assert client.get("/").json() == {"visites": 1}
    assert client.get("/").json() == {"visites": 2}


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_health_redis_down(client, fake_server):
    fake_server.connected = False
    resp = client.get("/health")
    assert resp.status_code == 503
    assert resp.text == "redis down"


def test_metrics_counts_requests(client):
    client.get("/")
    body = client.get("/metrics").text
    assert 'http_requests_total{method="GET",path="/",status="200"}' in body
    assert "http_request_duration_seconds" in body
