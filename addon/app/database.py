"""Async SQLite database management with schema migrations."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).parent / "db" / "migrations"


class Database:
    """Async SQLite database wrapper with connection pooling and migrations."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._connection: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        """Open connection and run migrations."""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)

        self._connection = await aiosqlite.connect(self._db_path)
        self._connection.row_factory = aiosqlite.Row

        # Enable WAL mode and foreign keys
        await self._connection.execute("PRAGMA journal_mode=WAL")
        await self._connection.execute("PRAGMA foreign_keys=ON")

        await self._run_migrations()

    async def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None

    @property
    def connection(self) -> aiosqlite.Connection:
        """Get the active connection."""
        assert self._connection is not None, "Database not initialized"
        return self._connection

    async def execute(
        self, sql: str, parameters: tuple | dict | None = None
    ) -> aiosqlite.Cursor:
        """Execute a single SQL statement."""
        if parameters:
            return await self.connection.execute(sql, parameters)
        return await self.connection.execute(sql)

    async def executemany(
        self, sql: str, parameters: list[tuple | dict]
    ) -> aiosqlite.Cursor:
        """Execute SQL with multiple parameter sets."""
        return await self.connection.executemany(sql, parameters)

    async def fetchone(
        self, sql: str, parameters: tuple | dict | None = None
    ) -> aiosqlite.Row | None:
        """Execute SQL and fetch one row."""
        cursor = await self.execute(sql, parameters)
        return await cursor.fetchone()

    async def fetchall(
        self, sql: str, parameters: tuple | dict | None = None
    ) -> list[aiosqlite.Row]:
        """Execute SQL and fetch all rows."""
        cursor = await self.execute(sql, parameters)
        return await cursor.fetchall()

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.connection.commit()

    async def _run_migrations(self) -> None:
        """Run pending schema migrations."""
        # Create schema_version table if it doesn't exist
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await self.connection.commit()

        # Get current version
        row = await self.fetchone(
            "SELECT MAX(version) as version FROM schema_version"
        )
        current_version = row["version"] if row and row["version"] is not None else 0

        # Find and run pending migrations
        if not MIGRATIONS_DIR.exists():
            logger.debug("No migrations directory found")
            return

        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        for migration_file in migration_files:
            # Extract version number from filename (e.g., "001_initial.sql" -> 1)
            version = int(migration_file.stem.split("_")[0])
            if version <= current_version:
                continue

            logger.info(f"Running migration {migration_file.name}")
            sql = migration_file.read_text()

            # Execute migration statements
            await self.connection.executescript(sql)

            # Record version
            await self.connection.execute(
                "INSERT INTO schema_version (version) VALUES (?)", (version,)
            )
            await self.connection.commit()
            logger.info(f"Migration {migration_file.name} applied successfully")
