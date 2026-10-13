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


def test_root_expose_version_header(client):
    resp = client.get("/")
    assert resp.headers["X-Visites-Version"] == "0.1.0"


def test_reset_remet_compteur_a_zero(client):
    client.get("/")
    client.get("/")
    assert client.post("/reset").json() == {"visites": 0}
    assert client.get("/").json() == {"visites": 1}
