"""Email parser for extracting tracking IDs from email content."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from email.message import Message

from app.scrapers.base import VENDOR_MATKAHUOLTO, VENDOR_POSTI, VENDOR_POSTNORD

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredPackage:
    """A package discovered from an email."""

    tracking_id: str
    vendor: str
    source_subject: str
    source_sender: str


# Regex patterns for Finnish carrier tracking IDs.
_POSTI_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(JJFI\d{9,20})\b", re.IGNORECASE),
    # Generic Posti tracking code (2 letters + 9 digits + FI)
    re.compile(r"\b([A-Z]{2}\d{9}FI)\b", re.IGNORECASE),
]

_POSTNORD_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(\d{14,20})\b"),
]

_MATKAHUOLTO_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\b(MH\d{8,12})\b", re.IGNORECASE),
]

# Sender patterns for vendor detection.
_VENDOR_SENDER_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    VENDOR_POSTI: [
        re.compile(r"posti\.fi", re.IGNORECASE),
        re.compile(r"@posti\.", re.IGNORECASE),
    ],
    VENDOR_POSTNORD: [
        re.compile(r"postnord", re.IGNORECASE),
    ],
    VENDOR_MATKAHUOLTO: [
        re.compile(r"matkahuolto", re.IGNORECASE),
    ],
}


def _get_email_text(msg: Message) -> str:
    """Extract plain text content from an email message."""
    text_parts: list[str] = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if isinstance(payload, bytes):
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        text_parts.append(payload.decode(charset, errors="replace"))
                    except (LookupError, UnicodeDecodeError):
                        text_parts.append(payload.decode("utf-8", errors="replace"))
            elif content_type == "text/html" and not text_parts:
                payload = part.get_payload(decode=True)
                if isinstance(payload, bytes):
                    charset = part.get_content_charset() or "utf-8"
                    try:
                        text_parts.append(payload.decode(charset, errors="replace"))
                    except (LookupError, UnicodeDecodeError):
                        text_parts.append(payload.decode("utf-8", errors="replace"))
    else:
        payload = msg.get_payload(decode=True)
        if isinstance(payload, bytes):
            charset = msg.get_content_charset() or "utf-8"
            try:
                text_parts.append(payload.decode(charset, errors="replace"))
            except (LookupError, UnicodeDecodeError):
                text_parts.append(payload.decode("utf-8", errors="replace"))

    return "\n".join(text_parts)


def _detect_vendor_from_sender(sender: str) -> str | None:
    """Detect vendor from email sender address."""
    for vendor, patterns in _VENDOR_SENDER_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(sender):
                return vendor
    return None


def _extract_tracking_ids(text: str, vendor: str | None) -> list[tuple[str, str]]:
    """Extract tracking IDs from text with associated vendor.

    Returns list of (tracking_id, vendor) tuples.
    """
    results: list[tuple[str, str]] = []
    seen: set[str] = set()

    if vendor == VENDOR_POSTI:
        for pattern in _POSTI_PATTERNS:
            for match in pattern.finditer(text):
                tid = match.group(1).upper()
                if tid not in seen:
                    seen.add(tid)
                    results.append((tid, VENDOR_POSTI))
    elif vendor == VENDOR_POSTNORD:
        for pattern in _POSTNORD_PATTERNS:
            for match in pattern.finditer(text):
                tid = match.group(1)
                if tid not in seen:
                    seen.add(tid)
                    results.append((tid, VENDOR_POSTNORD))
    elif vendor == VENDOR_MATKAHUOLTO:
        for pattern in _MATKAHUOLTO_PATTERNS:
            for match in pattern.finditer(text):
                tid = match.group(1).upper()
                if tid not in seen:
                    seen.add(tid)
                    results.append((tid, VENDOR_MATKAHUOLTO))
    else:
        # Unknown vendor — try all patterns.
        for pattern in _POSTI_PATTERNS:
            for match in pattern.finditer(text):
                tid = match.group(1).upper()
                if tid not in seen:
                    seen.add(tid)
                    results.append((tid, VENDOR_POSTI))
        for pattern in _MATKAHUOLTO_PATTERNS:
            for match in pattern.finditer(text):
                tid = match.group(1).upper()
                if tid not in seen:
                    seen.add(tid)
                    results.append((tid, VENDOR_MATKAHUOLTO))

    return results


def parse_email(msg: Message) -> list[DiscoveredPackage]:
    """Parse an email message and extract discovered packages."""
    subject = msg.get("Subject", "") or ""
    sender = msg.get("From", "") or ""

    vendor = _detect_vendor_from_sender(sender)

    body = _get_email_text(msg)
    full_text = f"{subject}\n{body}"

    tracking_ids = _extract_tracking_ids(full_text, vendor)

    return [
        DiscoveredPackage(
            tracking_id=tid,
            vendor=v,
            source_subject=subject,
            source_sender=sender,
        )
        for tid, v in tracking_ids
    ]
