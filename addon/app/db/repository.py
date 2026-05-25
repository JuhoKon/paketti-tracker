"""Data access layer for packages and tracking events."""

from __future__ import annotations

from datetime import datetime

from app.database import Database
from app.db.models import PackageRow, TrackingEventRow


class PackageRepository:
    """Repository for package and tracking event CRUD operations."""

    def __init__(self, db: Database) -> None:
        self._db = db

    async def get_all(self) -> list[PackageRow]:
        """Get all packages."""
        rows = await self._db.fetchall(
            "SELECT * FROM packages ORDER BY created_at DESC"
        )
        return [self._row_to_package(row) for row in rows]

    async def get_by_id(self, tracking_id: str) -> PackageRow | None:
        """Get a package by tracking_id."""
        row = await self._db.fetchone(
            "SELECT * FROM packages WHERE tracking_id = ?", (tracking_id,)
        )
        return self._row_to_package(row) if row else None

    async def get_active(self) -> list[PackageRow]:
        """Get all non-delivered packages."""
        rows = await self._db.fetchall(
            "SELECT * FROM packages WHERE delivered = 0 ORDER BY created_at DESC"
        )
        return [self._row_to_package(row) for row in rows]

    async def create(self, package: PackageRow) -> PackageRow:
        """Insert a new package."""
        await self._db.execute(
            """
            INSERT INTO packages (tracking_id, vendor, name, status, delivered,
                                  last_updated, tracking_url, estimated_delivery,
                                  last_location, last_event_time, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                package.tracking_id,
                package.vendor,
                package.name,
                package.status,
                int(package.delivered),
                package.last_updated,
                package.tracking_url,
                package.estimated_delivery,
                package.last_location,
                package.last_event_time,
                package.created_at,
            ),
        )
        await self._db.commit()
        return package

    async def update(self, tracking_id: str, **fields: object) -> PackageRow | None:
        """Update specific fields of a package."""
        if not fields:
            return await self.get_by_id(tracking_id)

        # Build SET clause dynamically
        set_parts = []
        values: list[object] = []
        for key, value in fields.items():
            set_parts.append(f"{key} = ?")
            if key == "delivered":
                values.append(int(bool(value)))
            else:
                values.append(value)

        values.append(tracking_id)
        sql = f"UPDATE packages SET {', '.join(set_parts)} WHERE tracking_id = ?"
        await self._db.execute(sql, tuple(values))
        await self._db.commit()
        return await self.get_by_id(tracking_id)

    async def delete(self, tracking_id: str) -> bool:
        """Delete a package (cascade deletes events)."""
        cursor = await self._db.execute(
            "DELETE FROM packages WHERE tracking_id = ?", (tracking_id,)
        )
        await self._db.commit()
        return cursor.rowcount > 0

    # --- Tracking Events ---

    async def get_events(self, tracking_id: str) -> list[TrackingEventRow]:
        """Get all events for a package, newest first."""
        rows = await self._db.fetchall(
            "SELECT * FROM tracking_events WHERE tracking_id = ? ORDER BY timestamp DESC",
            (tracking_id,),
        )
        return [self._row_to_event(row) for row in rows]

    async def add_events(self, events: list[TrackingEventRow]) -> None:
        """Insert multiple tracking events (ignoring duplicates)."""
        if not events:
            return
        await self._db.executemany(
            """
            INSERT OR IGNORE INTO tracking_events (tracking_id, timestamp, description, location)
            VALUES (?, ?, ?, ?)
            """,
            [
                (e.tracking_id, e.timestamp, e.description, e.location)
                for e in events
            ],
        )
        await self._db.commit()

    async def replace_events(self, tracking_id: str, events: list[TrackingEventRow]) -> None:
        """Replace all events for a package with new ones."""
        await self._db.execute(
            "DELETE FROM tracking_events WHERE tracking_id = ?", (tracking_id,)
        )
        await self._db.executemany(
            """
            INSERT INTO tracking_events (tracking_id, timestamp, description, location)
            VALUES (?, ?, ?, ?)
            """,
            [
                (e.tracking_id, e.timestamp, e.description, e.location)
                for e in events
            ],
        )
        await self._db.commit()

    # --- Discovered Packages ---

    async def get_discovered(self) -> list[dict]:
        """Get all discovered packages."""
        rows = await self._db.fetchall(
            "SELECT * FROM discovered_packages ORDER BY discovered_at DESC"
        )
        return [dict(row) for row in rows]

    async def add_discovered(
        self,
        tracking_id: str,
        vendor: str,
        source_subject: str = "",
        source_sender: str = "",
    ) -> None:
        """Add a discovered package (ignore if exists)."""
        await self._db.execute(
            """
            INSERT OR IGNORE INTO discovered_packages
                (tracking_id, vendor, source_subject, source_sender)
            VALUES (?, ?, ?, ?)
            """,
            (tracking_id, vendor, source_subject, source_sender),
        )
        await self._db.commit()

    async def remove_discovered(self, tracking_id: str) -> bool:
        """Remove a discovered package."""
        cursor = await self._db.execute(
            "DELETE FROM discovered_packages WHERE tracking_id = ?", (tracking_id,)
        )
        await self._db.commit()
        return cursor.rowcount > 0

    # --- Helpers ---

    @staticmethod
    def _row_to_package(row) -> PackageRow:
        """Convert a database row to PackageRow."""
        return PackageRow(
            tracking_id=row["tracking_id"],
            vendor=row["vendor"],
            name=row["name"],
            status=row["status"],
            delivered=bool(row["delivered"]),
            last_updated=row["last_updated"],
            tracking_url=row["tracking_url"],
            estimated_delivery=row["estimated_delivery"],
            last_location=row["last_location"],
            last_event_time=row["last_event_time"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _row_to_event(row) -> TrackingEventRow:
        """Convert a database row to TrackingEventRow."""
        return TrackingEventRow(
            id=row["id"],
            tracking_id=row["tracking_id"],
            timestamp=row["timestamp"],
            description=row["description"],
            location=row["location"],
        )
