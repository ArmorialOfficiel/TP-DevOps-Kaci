import time

import redis
from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from .config import settings

app = FastAPI(title="visites")
r = redis.Redis.from_url(settings.redis_url, decode_responses=True)

REQUESTS = Counter(
    "http_requests_total",
    "Requêtes HTTP",
    ["method", "path", "status"],
)
LATENCY = Histogram(
    "http_request_duration_seconds",
    "Latence",
    ["path"],
)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    path = request.url.path
    start = time.perf_counter()
    status = "500"
    try:
        response = await call_next(request)
        status = str(response.status_code)
        return response
    finally:
        if path != "/metrics":
            LATENCY.labels(path).observe(time.perf_counter() - start)
            REQUESTS.labels(request.method, path, status).inc()


@app.get("/")
def root(response: Response):
    n = r.incr("visites")
    response.headers["X-Visites-Version"] = "0.1.0"
    return {"visites": n}


@app.post("/reset")
def reset_visites():
    r.set("visites", 0)
    return {"visites": 0}


@app.get("/health")
def health():
    try:
        r.ping()
    except redis.exceptions.ConnectionError:
        return Response(status_code=503, content="redis down")
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
