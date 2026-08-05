"""Entrypoint for running VictoriaOS directly: ``python -m backend.main``.

The FastAPI application itself lives in ``backend.app``; this module just
launches it with uvicorn so there is a single source of truth for routes,
middleware, and startup behavior.
"""

from __future__ import annotations

import uvicorn

from backend.config.settings import get_settings


def main() -> None:
    """Run the VictoriaOS API server."""
    settings = get_settings()
    uvicorn.run(
        "backend.app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
    )


if __name__ == "__main__":
    main()
