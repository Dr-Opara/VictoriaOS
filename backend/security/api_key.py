from __future__ import annotations

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from backend.core.logger import logger

API_KEY_HEADER = "x-api-key"

_EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Require a shared secret on every request when ``api_key`` is configured.

    VictoriaOS is a single-user assistant, not a multi-tenant service, so a
    shared API key (rather than full OAuth/JWT user accounts) is the right
    amount of security for its threat model: it stops the API from being
    usable by anyone who can merely reach the port, once it's deployed
    somewhere beyond localhost. When no key is configured (local
    development), requests are allowed through with a one-time warning.
    """

    def __init__(self, app, api_key: str) -> None:
        super().__init__(app)
        self.api_key = api_key
        self._warned = False

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if not self.api_key:
            if not self._warned:
                logger.warning(
                    "No API_KEY configured - all VictoriaOS endpoints are unauthenticated. "
                    "Set API_KEY in the environment before exposing this beyond localhost."
                )
                self._warned = True
            return await call_next(request)

        if request.url.path in _EXEMPT_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        provided_key = request.headers.get(API_KEY_HEADER)
        if provided_key != self.api_key:
            logger.warning("Rejected request to %s: missing/invalid API key.", request.url.path)
            return Response(
                content='{"detail":"Invalid or missing API key."}',
                status_code=401,
                media_type="application/json",
            )

        return await call_next(request)
