"""FastAPI application setup with comprehensive security."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from caresense import __version__
from caresense.api.routes import router
from caresense.config import get_settings
from caresense.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from caresense.utils.logging import get_logger, setup_logging

log = get_logger(__name__)


def create_app() -> FastAPI:
    """
    Create FastAPI application with security hardening.

    Security features:
    - Rate limiting
    - Security headers
    - CORS restrictions
    - Trusted host validation
    - Request logging
    """
    settings = get_settings()
    setup_logging()

    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        description="Privacy-preserving medical triage API with explainability and clinician review",
    )

    # Security: Rate limiting (must be first)
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=60,
        burst_size=10,
    )

    # Security: Add security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Security: CORS with explicit origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allow_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )

    # Include API routes
    app.include_router(router, prefix="/v1")

    @app.get("/version", tags=["Observability"])
    def version() -> dict[str, str]:
        """Get API version."""
        return {"version": __version__, "api_version": settings.api_version}

    @app.on_event("startup")
    async def startup_event():
        """Log application startup."""
        log.info(
            "application_startup",
            version=__version__,
            environment=settings.environment,
        )

    @app.on_event("shutdown")
    async def shutdown_event():
        """Log application shutdown."""
        log.info("application_shutdown")

    return app


app = create_app()
