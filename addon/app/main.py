"""FastAPI application entry point with lifespan management."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.config import Settings, load_settings
from app.database import Database

logger = logging.getLogger(__name__)

# Global state
_settings: Settings | None = None
_database: Database | None = None
_scraper_service = None
_email_service = None
_mqtt_service = None
_notify_service = None
_ready: bool = False


def get_settings() -> Settings:
    """Get application settings."""
    assert _settings is not None, "Settings not initialized"
    return _settings


def get_database() -> Database:
    """Get database instance."""
    assert _database is not None, "Database not initialized"
    return _database


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle: startup and shutdown."""
    global _settings, _database, _ready
    global _scraper_service, _email_service, _mqtt_service, _notify_service

    # Startup
    _settings = load_settings()

    logging.basicConfig(
        level=getattr(logging, _settings.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    logger.info("Starting Paketti Tracker add-on")

    # Initialize database
    _database = Database(_settings.database_path)
    await _database.initialize()

    # Initialize services
    from app.services.notify_service import NotifyService
    from app.services.mqtt_service import MqttService
    from app.services.scraper_service import ScraperService
    from app.services.email_service import EmailService

    # Notify service
    _notify_service = NotifyService(
        database=_database,
        supervisor_token=_settings.supervisor_token,
        ha_api_url=_settings.ha_api_url,
    )
    await _notify_service.start()

    # MQTT service (optional — fails gracefully if broker unavailable)
    _mqtt_service = MqttService()
    await _mqtt_service.start()

    # Scraper service
    _scraper_service = ScraperService(
        database=_database,
        poll_interval_minutes=_settings.poll_interval,
        on_notifications=_notify_service.send_notifications,
        on_package_updated=_mqtt_service.publish_package,
    )
    await _scraper_service.start()

    # Email service
    _email_service = EmailService(
        database=_database,
        settings=_settings,
    )
    await _email_service.start()

    _ready = True
    logger.info("Paketti Tracker ready")

    yield

    # Shutdown
    _ready = False
    logger.info("Shutting down Paketti Tracker")

    if _email_service:
        await _email_service.stop()
    if _scraper_service:
        await _scraper_service.stop()
    if _mqtt_service:
        await _mqtt_service.stop()
    if _notify_service:
        await _notify_service.stop()
    if _database:
        await _database.close()


app = FastAPI(
    title="Paketti Tracker",
    version="0.9.0",
    lifespan=lifespan,
)

# Register routers
from app.routers.packages import router as packages_router
from app.routers.settings import router as settings_router
from app.routers.email import router as email_router

app.include_router(packages_router)
app.include_router(settings_router)
app.include_router(email_router)


@app.get("/api/health")
async def health() -> JSONResponse:
    """Health check endpoint."""
    if not _ready:
        return JSONResponse(
            status_code=503,
            content={"status": "starting"},
        )
    return JSONResponse(
        status_code=200,
        content={"status": "healthy"},
    )


# Ingress path middleware — injects X-Ingress-Path into HTML for frontend
@app.middleware("http")
async def ingress_middleware(request: Request, call_next):
    """Pass through X-Ingress-Path for the frontend to use."""
    response = await call_next(request)
    return response


# Mount static frontend (SPA with fallback)
_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_frontend_dir):
    # SPA fallback: serve index.html for non-API routes that don't match static files
    _index_html = os.path.join(_frontend_dir, "index.html")

    @app.get("/{path:path}", include_in_schema=False)
    async def spa_fallback(request: Request, path: str) -> HTMLResponse:
        """Serve index.html for SPA client-side routing."""
        # Only serve SPA for non-API, non-static paths
        if path.startswith("api/"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})

        # Try to serve static file first
        static_path = os.path.join(_frontend_dir, path)
        if os.path.isfile(static_path):
            from fastapi.responses import FileResponse
            import mimetypes
            mime_type, _ = mimetypes.guess_type(static_path)
            return FileResponse(static_path, media_type=mime_type)

        # Fallback to index.html
        if os.path.isfile(_index_html):
            with open(_index_html) as f:
                html = f.read()
            # Inject ingress path as meta tag
            ingress_path = request.headers.get("X-Ingress-Path", "")
            if ingress_path:
                html = html.replace(
                    "<head>",
                    f'<head><meta name="ingress-path" content="{ingress_path}">',
                )
            return HTMLResponse(html)
        return HTMLResponse("<h1>Frontend not built</h1>", status_code=500)
