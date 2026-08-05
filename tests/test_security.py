from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.security.api_key import ApiKeyMiddleware
from backend.security.headers import SecurityHeadersMiddleware
from backend.security.rate_limit import RateLimitMiddleware


def _minimal_app() -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    def health():
        return {"status": "healthy"}

    @app.get("/tasks")
    def tasks():
        return {"tasks": []}

    return app


def test_security_headers_present_on_every_response():
    app = _minimal_app()
    app.add_middleware(SecurityHeadersMiddleware)
    client = TestClient(app)

    response = client.get("/health")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_api_key_middleware_blocks_without_key():
    app = _minimal_app()
    app.add_middleware(ApiKeyMiddleware, api_key="secret")
    client = TestClient(app)

    assert client.get("/tasks").status_code == 401
    assert client.get("/tasks", headers={"x-api-key": "wrong"}).status_code == 401
    assert client.get("/tasks", headers={"x-api-key": "secret"}).status_code == 200


def test_api_key_middleware_exempts_health():
    app = _minimal_app()
    app.add_middleware(ApiKeyMiddleware, api_key="secret")
    client = TestClient(app)

    assert client.get("/health").status_code == 200


def test_api_key_middleware_open_when_unconfigured():
    app = _minimal_app()
    app.add_middleware(ApiKeyMiddleware, api_key="")
    client = TestClient(app)

    assert client.get("/tasks").status_code == 200


def test_rate_limit_blocks_after_threshold():
    app = _minimal_app()
    app.add_middleware(RateLimitMiddleware, max_requests=3, window_seconds=60)
    client = TestClient(app)

    statuses = [client.get("/health").status_code for _ in range(5)]

    assert statuses == [200, 200, 200, 429, 429]
