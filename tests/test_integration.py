import pytest
import redis
from fastapi.testclient import TestClient

import app.main as main
from app.config import settings

pytestmark = pytest.mark.integration


@pytest.fixture
def real_client():
    conn = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    conn.delete("visites")
    with TestClient(main.app) as c:
        yield c
    conn.delete("visites")


def test_counter_persists_in_real_redis(real_client):
    real_client.get("/")
    real_client.get("/")
    conn = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    assert conn.get("visites") == "2"


def test_health_against_real_redis(real_client):
    assert real_client.get("/health").json() == {"status": "ok"}
