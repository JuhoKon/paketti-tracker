"""Posti scraper — uses anonymous GraphQL API at graphql.posti.fi."""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any

import aiohttp

from ..const import (
    STATUS_DELIVERED,
    STATUS_EXCEPTION,
    STATUS_IN_TRANSIT,
    STATUS_OUT_FOR_DELIVERY,
    STATUS_PENDING,
    STATUS_UNKNOWN,
    VENDOR_POSTI,
)
from ..models import TrackingEvent, TrackingResult
from .base import BaseScraper, ScraperError

_LOGGER = logging.getLogger(__name__)

_AUTH_URL = "https://auth-service.posti.fi/api/v1/anonymous_token"
_GRAPHQL_URL = "https://graphql.posti.fi/graphql"

# Token refresh buffer: refresh 5 minutes before actual expiry.
_TOKEN_EXPIRY_BUFFER_S = 300

_SEARCH_SHIPMENTS_QUERY = """\
query SearchShipments(
  $page: Int!
  $pageSize: Int!
  $type: ConsumerSearchTypeFilter!
  $searchTerms: [String!]!
  $role: ConsumerUserRoleFilter
  $locale: String
) {
  consumerSearchShipments(
    page: $page
    pageSize: $pageSize
    type: $type
    searchTerms: $searchTerms
    role: $role
    locale: $locale
  ) {
    page
    totalHits
    hits {
      shipmentId
      displayId
      displayName
      status {
        main
        subStatus
        exception
      }
      delivery {
        method
        time {
          type
          timestamp
          timestampLatest
        }
        destination {
          name
          street
          postcode
          city
        }
      }
      pickupPoint {
        lastCollectionDate
        address {
          streetAddress
          postcode
          city
          publicName
        }
      }
      events {
        city
        eventDescription
        reasonDescription
        timestamp
      }
    }
  }
}"""

# Posti status string → normalized status mapping.
_STATUS_MAP: dict[str, str] = {
    "WAITING": STATUS_PENDING,
    "ORDER_RECEIVED": STATUS_PENDING,
    "RECEIVED": STATUS_IN_TRANSIT,
    "IN_TRANSPORT": STATUS_IN_TRANSIT,
    "READY_FOR_PICKUP": STATUS_DELIVERED,
    "IN_DELIVERY": STATUS_OUT_FOR_DELIVERY,
    "DELIVERED": STATUS_DELIVERED,
    "RETURN_WAITING": STATUS_EXCEPTION,
    "RETURN_IN_TRANSPORT": STATUS_EXCEPTION,
}


class PostiScraper(BaseScraper):
    """Scraper for Posti (posti.fi) using anonymous GraphQL endpoint."""

    def __init__(self) -> None:
        self._id_token: str | None = None
        self._role_token: str | None = None
        self._token_expires_at: float = 0.0

    async def fetch(
        self,
        tracking_id: str,
        session: aiohttp.ClientSession,
    ) -> TrackingResult:
        """Fetch tracking data for a Posti shipment."""
        await self._ensure_token(session)

        headers: dict[str, str] = {
            "authorization": self._role_token or "",
            "x-posti-token": f"Bearer {self._id_token}",
            "Content-Type": "application/json",
            "Origin": "https://www.posti.fi",
            "Referer": "https://www.posti.fi/",
        }

        payload = {
            "operationName": "SearchShipments",
            "query": _SEARCH_SHIPMENTS_QUERY,
            "variables": {
                "page": 1,
                "pageSize": 1,
                "searchTerms": [tracking_id],
                "type": "PUBLIC_SHIPMENTS",
                "role": None,
                "locale": "fi",
            },
        }

        try:
            async with session.post(_GRAPHQL_URL, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    raise ScraperError(
                        f"Posti GraphQL returned HTTP {resp.status} for tracking ID {tracking_id}"
                    )
                data = await resp.json()
        except aiohttp.ClientError as exc:
            raise ScraperError(
                f"Network error fetching Posti tracking for {tracking_id}: {exc}"
            ) from exc

        # Check for GraphQL-level errors.
        if "errors" in data:
            errors = data["errors"]
            msg = errors[0].get("message", "Unknown GraphQL error") if errors else ""
            # If unauthorized, invalidate token so next call re-authenticates.
            if "Unauthorized" in msg or "Not Authorized" in msg:
                self._invalidate_token()
            raise ScraperError(f"Posti GraphQL error for {tracking_id}: {msg}")

        return self._parse_response(tracking_id, data)

    # ------------------------------------------------------------------
    # Auth helpers
    # ------------------------------------------------------------------

    async def _ensure_token(self, session: aiohttp.ClientSession) -> None:
        """Obtain or refresh the anonymous token pair."""
        if self._role_token and time.time() < self._token_expires_at:
            return

        try:
            async with session.post(_AUTH_URL, json={}) as resp:
                if resp.status != 200:
                    raise ScraperError(f"Posti auth endpoint returned HTTP {resp.status}")
                body = await resp.json()
        except aiohttp.ClientError as exc:
            raise ScraperError(f"Network error during Posti auth: {exc}") from exc

        try:
            self._id_token = body["id_token"]
            role_tokens = body["role_tokens"]
            self._role_token = role_tokens[0]["token"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ScraperError(f"Unexpected Posti auth response format: {exc}") from exc

        # Parse expiry from the role_token JWT (middle segment).
        # We don't verify signature — just read `exp` claim.
        try:
            import base64
            import json as json_mod

            parts = self._role_token.split(".")
            # Add padding for base64url decoding.
            payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
            payload_bytes = base64.urlsafe_b64decode(payload_b64)
            claims = json_mod.loads(payload_bytes)
            exp = float(claims["exp"])
            self._token_expires_at = exp - _TOKEN_EXPIRY_BUFFER_S
        except Exception:  # noqa: BLE001
            # Fallback: assume token is valid for 50 minutes.
            self._token_expires_at = time.time() + 3000

        _LOGGER.debug("Posti anonymous token acquired, expires at %s", self._token_expires_at)

    def _invalidate_token(self) -> None:
        """Force re-authentication on next fetch."""
        self._id_token = None
        self._role_token = None
        self._token_expires_at = 0.0

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_response(self, tracking_id: str, data: dict[str, Any]) -> TrackingResult:
        """Parse GraphQL response into a TrackingResult."""
        search_result = data.get("data", {}).get("consumerSearchShipments")
        if not search_result:
            raise ScraperError(f"No consumerSearchShipments in response for {tracking_id}")

        hits = search_result.get("hits") or []
        if not hits:
            raise ScraperError(f"Tracking ID {tracking_id} not found on Posti")

        shipment = hits[0]
        return self._build_result(tracking_id, shipment)

    def _build_result(self, tracking_id: str, shipment: dict[str, Any]) -> TrackingResult:
        """Build TrackingResult from a single shipment hit."""
        # Status
        status_obj = shipment.get("status") or {}
        main_status = status_obj.get("main") or ""
        normalized = _STATUS_MAP.get(main_status, STATUS_UNKNOWN)

        # If there's an exception flag, override to exception.
        if status_obj.get("exception"):
            normalized = STATUS_EXCEPTION

        delivered = normalized == STATUS_DELIVERED

        # Events
        raw_events = shipment.get("events") or []
        events: list[TrackingEvent] = []
        for ev in raw_events:
            ts_str = ev.get("timestamp")
            if not ts_str:
                continue
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                continue

            description = (ev.get("eventDescription") or "").strip()
            reason = (ev.get("reasonDescription") or "").strip()
            if reason:
                description = f"{description} — {reason}"

            events.append(
                TrackingEvent(
                    timestamp=ts,
                    description=description,
                    location=ev.get("city"),
                )
            )

        # Last event info
        last_location: str | None = None
        last_event_time: datetime | None = None
        if events:
            last_location = events[0].location
            last_event_time = events[0].timestamp

        # Estimated delivery
        estimated_delivery = None
        delivery = shipment.get("delivery") or {}
        delivery_time = delivery.get("time") or {}
        ts_str = delivery_time.get("timestamp")
        if ts_str:
            try:
                dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                estimated_delivery = dt.date()
            except (ValueError, TypeError):
                pass

        return TrackingResult(
            tracking_id=tracking_id,
            vendor=VENDOR_POSTI,
            status=normalized,
            delivered=delivered,
            events=events,
            estimated_delivery=estimated_delivery,
            last_location=last_location,
            last_event_time=last_event_time,
        )
