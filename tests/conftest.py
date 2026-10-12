import fakeredis
import pytest
from fastapi.testclient import TestClient

import app.main as main


@pytest.fixture
def fake_server():
    return fakeredis.FakeServer()


@pytest.fixture
def client(monkeypatch, fake_server):
    """Client HTTP avec un Redis simulé (fakeredis), remis à zéro à chaque test."""
    fake = fakeredis.FakeRedis(server=fake_server, decode_responses=True)
    monkeypatch.setattr(main, "r", fake)
    with TestClient(main.app) as c:
        yield c
