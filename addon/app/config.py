"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    """Application settings sourced from environment and add-on options."""

    # Data directory (mapped by Supervisor)
    data_dir: str = field(default_factory=lambda: os.environ.get("PAKETTI_DATA_DIR", "/data"))

    # Database
    @property
    def database_path(self) -> str:
        return f"{self.data_dir}/paketti_tracker.db"

    # Polling intervals (minutes)
    poll_interval: int = field(
        default_factory=lambda: int(os.environ.get("PAKETTI_POLL_INTERVAL", "60"))
    )
    email_poll_interval: int = field(
        default_factory=lambda: int(os.environ.get("PAKETTI_EMAIL_POLL_INTERVAL", "30"))
    )

    # Log level
    log_level: str = field(
        default_factory=lambda: os.environ.get("PAKETTI_LOG_LEVEL", "info")
    )

    # Supervisor token (set by HA Supervisor)
    supervisor_token: str = field(
        default_factory=lambda: os.environ.get("SUPERVISOR_TOKEN", "")
    )

    # HA API base URL (within add-on network)
    ha_api_url: str = field(
        default_factory=lambda: os.environ.get("HA_API_URL", "http://supervisor/core/api")
    )

    # Email IMAP settings (from add-on options)
    email_enabled: bool = field(
        default_factory=lambda: os.environ.get("PAKETTI_EMAIL_ENABLED", "false").lower() == "true"
    )
    email_host: str = field(
        default_factory=lambda: os.environ.get("PAKETTI_EMAIL_HOST", "")
    )
    email_port: int = field(
        default_factory=lambda: int(os.environ.get("PAKETTI_EMAIL_PORT", "993"))
    )
    email_username: str = field(
        default_factory=lambda: os.environ.get("PAKETTI_EMAIL_USERNAME", "")
    )
    email_password: str = field(
        default_factory=lambda: os.environ.get("PAKETTI_EMAIL_PASSWORD", "")
    )
    email_folder: str = field(
        default_factory=lambda: os.environ.get("PAKETTI_EMAIL_FOLDER", "INBOX")
    )
    email_auto_add: bool = field(
        default_factory=lambda: os.environ.get("PAKETTI_EMAIL_AUTO_ADD", "false").lower() == "true"
    )


def load_settings() -> Settings:
    """Create settings from current environment."""
    return Settings()
