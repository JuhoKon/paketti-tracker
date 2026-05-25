"""Tests for PostiScraper."""

from __future__ import annotations

from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.paketti_tracker.const import (
    STATUS_DELIVERED,
    STATUS_EXCEPTION,
    STATUS_IN_TRANSIT,
    STATUS_OUT_FOR_DELIVERY,
    STATUS_PENDING,
    VENDOR_POSTI,
)
from custom_components.paketti_tracker.scrapers.base import ScraperError
from custom_components.paketti_tracker.scrapers.posti import PostiScraper

# -- Fixtures: realistic API response shapes ---------------------------------

AUTH_RESPONSE = {
    "id_token": "fake-id-token",
    "role_tokens": [
        {
            "type": "anonymous",
            # Minimal valid JWT with exp claim (exp = 9999999999)
            "token": ("eyJhbGciOiJSUzI1NiJ9.eyJleHAiOjk5OTk5OTk5OTl9.fake-signature"),
        }
    ],
}

GRAPHQL_SUCCESS_RESPONSE = {
    "data": {
        "consumerSearchShipments": {
            "page": 1,
            "totalHits": 1,
            "hits": [
                {
                    "shipmentId": "31064249809",
                    "displayId": "JJFI60773420139193970",
                    "displayName": "JJFI60773420139193970",
                    "status": {
                        "main": "IN_TRANSPORT",
                        "subStatus": [],
                        "exception": None,
                    },
                    "delivery": {
                        "method": "PICKUP_POINT",
                        "time": {
                            "type": "ESTIMATED",
                            "timestamp": "2026-05-24T00:00:00.000Z",
                            "timestampLatest": "2026-05-26T00:00:00.000Z",
                        },
                        "destination": {
                            "name": "Automaatti",
                            "street": "Kauppakatu 1",
                            "postcode": "40100",
                            "city": "JYVÄSKYLÄ",
                        },
                    },
                    "pickupPoint": {
                        "lastCollectionDate": "2026-05-30",
                        "address": {
                            "streetAddress": "Kauppakatu 1",
                            "postcode": "40100",
                            "city": "JYVÄSKYLÄ",
                            "publicName": "Posti automaatti",
                        },
                    },
                    "events": [
                        {
                            "city": "JYVÄSKYLÄ",
                            "eventDescription": "Lähetys on kuljetuksessa.",
                            "reasonDescription": " ",
                            "timestamp": "2026-05-22T22:15:48.000Z",
                        },
                        {
                            "city": "SEINÄJOKI",
                            "eventDescription": "Lähetys on kuljetuksessa.",
                            "reasonDescription": None,
                            "timestamp": "2026-05-22T18:17:38.000Z",
                        },
                        {
                            "city": None,
                            "eventDescription": "Olemme saaneet tiedon tulevasta lähetyksestä",
                            "reasonDescription": "Lähetys ei ole vielä saapunut meille.",
                            "timestamp": "2026-05-22T11:56:25.000Z",
                        },
                    ],
                }
            ],
        }
    }
}

GRAPHQL_NOT_FOUND_RESPONSE = {
    "data": {
        "consumerSearchShipments": {
            "page": 1,
            "totalHits": 0,
            "hits": [],
        }
    }
}

GRAPHQL_DELIVERED_RESPONSE = {
    "data": {
        "consumerSearchShipments": {
            "page": 1,
            "totalHits": 1,
            "hits": [
                {
                    "shipmentId": "123",
                    "displayId": "TEST123",
                    "displayName": "TEST123",
                    "status": {
                        "main": "DELIVERED",
                        "subStatus": [],
                        "exception": None,
                    },
                    "delivery": {
                        "method": "HOME",
                        "time": None,
                        "destination": None,
                    },
                    "pickupPoint": None,
                    "events": [
                        {
                            "city": "HELSINKI",
                            "eventDescription": "Lähetys on toimitettu.",
                            "reasonDescription": None,
                            "timestamp": "2026-05-23T10:00:00.000Z",
                        },
                    ],
                }
            ],
        }
    }
}

GRAPHQL_EXCEPTION_RESPONSE = {
    "data": {
        "consumerSearchShipments": {
            "page": 1,
            "totalHits": 1,
            "hits": [
                {
                    "shipmentId": "456",
                    "displayId": "EXCEPT456",
                    "displayName": "EXCEPT456",
                    "status": {
                        "main": "IN_TRANSPORT",
                        "subStatus": [],
                        "exception": "DAMAGED",
                    },
                    "delivery": {"method": None, "time": None, "destination": None},
                    "pickupPoint": None,
                    "events": [],
                }
            ],
        }
    }
}

GRAPHQL_ERROR_RESPONSE = {
    "errors": [{"message": "Not Authorized to access consumerSearchShipments on type Query"}],
    "data": None,
}


# -- Helpers ------------------------------------------------------------------


def _make_mock_response(status: int, json_data: dict) -> AsyncMock:
    """Create a mock aiohttp response."""
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=json_data)
    return resp


def _make_mock_session(responses: list[tuple[int, dict]]) -> MagicMock:
    """Create a mock session that returns responses in order."""
    session = MagicMock()
    mock_posts = []
    for status, data in responses:
        ctx = AsyncMock()
        ctx.__aenter__ = AsyncMock(return_value=_make_mock_response(status, data))
        ctx.__aexit__ = AsyncMock(return_value=False)
        mock_posts.append(ctx)
    session.post = MagicMock(side_effect=mock_posts)
    return session


# -- Tests --------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_success_in_transit():
    """Test successful fetch returns correct TrackingResult."""
    session = _make_mock_session(
        [
            (200, AUTH_RESPONSE),  # auth call
            (200, GRAPHQL_SUCCESS_RESPONSE),  # graphql call
        ]
    )

    scraper = PostiScraper()
    result = await scraper.fetch("JJFI60773420139193970", session)

    assert result.tracking_id == "JJFI60773420139193970"
    assert result.vendor == VENDOR_POSTI
    assert result.status == STATUS_IN_TRANSIT
    assert result.delivered is False
    assert len(result.events) == 3
    assert result.last_location == "JYVÄSKYLÄ"
    assert result.last_event_time == datetime(2026, 5, 22, 22, 15, 48, tzinfo=UTC)
    assert result.estimated_delivery == date(2026, 5, 24)


@pytest.mark.asyncio
async def test_fetch_delivered():
    """Test delivered status is correctly detected."""
    session = _make_mock_session(
        [
            (200, AUTH_RESPONSE),
            (200, GRAPHQL_DELIVERED_RESPONSE),
        ]
    )

    scraper = PostiScraper()
    result = await scraper.fetch("TEST123", session)

    assert result.status == STATUS_DELIVERED
    assert result.delivered is True
    assert len(result.events) == 1
    assert result.last_location == "HELSINKI"


@pytest.mark.asyncio
async def test_fetch_exception_overrides_status():
    """Test that exception field overrides main status."""
    session = _make_mock_session(
        [
            (200, AUTH_RESPONSE),
            (200, GRAPHQL_EXCEPTION_RESPONSE),
        ]
    )

    scraper = PostiScraper()
    result = await scraper.fetch("EXCEPT456", session)

    assert result.status == STATUS_EXCEPTION
    assert result.delivered is False


@pytest.mark.asyncio
async def test_fetch_not_found_raises():
    """Test that unknown tracking ID raises ScraperError."""
    session = _make_mock_session(
        [
            (200, AUTH_RESPONSE),
            (200, GRAPHQL_NOT_FOUND_RESPONSE),
        ]
    )

    scraper = PostiScraper()
    with pytest.raises(ScraperError, match="not found on Posti"):
        await scraper.fetch("INVALID123", session)


@pytest.mark.asyncio
async def test_fetch_graphql_error_raises():
    """Test that GraphQL errors raise ScraperError."""
    session = _make_mock_session(
        [
            (200, AUTH_RESPONSE),
            (200, GRAPHQL_ERROR_RESPONSE),
        ]
    )

    scraper = PostiScraper()
    with pytest.raises(ScraperError, match="Not Authorized"):
        await scraper.fetch("TEST123", session)


@pytest.mark.asyncio
async def test_fetch_auth_failure_raises():
    """Test that auth endpoint failure raises ScraperError."""
    session = _make_mock_session(
        [
            (500, {}),  # auth fails
        ]
    )

    scraper = PostiScraper()
    with pytest.raises(ScraperError, match="auth endpoint returned HTTP 500"):
        await scraper.fetch("TEST123", session)


@pytest.mark.asyncio
async def test_fetch_graphql_http_error_raises():
    """Test that non-200 from GraphQL raises ScraperError."""
    session = _make_mock_session(
        [
            (200, AUTH_RESPONSE),
            (503, {}),  # graphql returns 503
        ]
    )

    scraper = PostiScraper()
    with pytest.raises(ScraperError, match="HTTP 503"):
        await scraper.fetch("TEST123", session)


@pytest.mark.asyncio
async def test_token_reuse():
    """Test that token is cached and reused across fetches."""
    # First call: auth + graphql. Second call: only graphql (token cached).
    session = _make_mock_session(
        [
            (200, AUTH_RESPONSE),
            (200, GRAPHQL_SUCCESS_RESPONSE),
            (200, GRAPHQL_SUCCESS_RESPONSE),  # second fetch, no auth call
        ]
    )

    scraper = PostiScraper()
    await scraper.fetch("JJFI60773420139193970", session)
    await scraper.fetch("JJFI60773420139193970", session)

    # Should have called post 3 times total (1 auth + 2 graphql)
    assert session.post.call_count == 3


@pytest.mark.asyncio
async def test_token_invalidation_on_unauthorized():
    """Test that auth error invalidates cached token."""
    session = _make_mock_session(
        [
            (200, AUTH_RESPONSE),
            (200, GRAPHQL_ERROR_RESPONSE),  # triggers invalidation
        ]
    )

    scraper = PostiScraper()
    with pytest.raises(ScraperError):
        await scraper.fetch("TEST123", session)

    # Token should be invalidated
    assert scraper._role_token is None
    assert scraper._id_token is None


@pytest.mark.asyncio
async def test_events_description_with_reason():
    """Test that reason is appended to event description."""
    session = _make_mock_session(
        [
            (200, AUTH_RESPONSE),
            (200, GRAPHQL_SUCCESS_RESPONSE),
        ]
    )

    scraper = PostiScraper()
    result = await scraper.fetch("JJFI60773420139193970", session)

    # Third event has a reason description
    third_event = result.events[2]
    assert "—" in third_event.description
    assert "Lähetys ei ole vielä saapunut meille." in third_event.description


@pytest.mark.asyncio
async def test_status_mapping_all_values():
    """Test all known Posti status values map correctly."""
    from custom_components.paketti_tracker.scrapers.posti import _STATUS_MAP

    assert _STATUS_MAP["WAITING"] == STATUS_PENDING
    assert _STATUS_MAP["ORDER_RECEIVED"] == STATUS_PENDING
    assert _STATUS_MAP["RECEIVED"] == STATUS_IN_TRANSIT
    assert _STATUS_MAP["IN_TRANSPORT"] == STATUS_IN_TRANSIT
    assert _STATUS_MAP["READY_FOR_PICKUP"] == STATUS_DELIVERED
    assert _STATUS_MAP["IN_DELIVERY"] == STATUS_OUT_FOR_DELIVERY
    assert _STATUS_MAP["DELIVERED"] == STATUS_DELIVERED
    assert _STATUS_MAP["RETURN_WAITING"] == STATUS_EXCEPTION
    assert _STATUS_MAP["RETURN_IN_TRANSPORT"] == STATUS_EXCEPTION
