-- Migration 001: Initial schema
-- Creates packages, tracking_events, settings, and discovered_packages tables.

CREATE TABLE IF NOT EXISTS packages (
    tracking_id TEXT PRIMARY KEY,
    vendor TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'unknown',
    delivered INTEGER NOT NULL DEFAULT 0,
    last_updated DATETIME,
    tracking_url TEXT NOT NULL DEFAULT '',
    estimated_delivery DATE,
    last_location TEXT NOT NULL DEFAULT '',
    last_event_time DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tracking_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tracking_id TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    location TEXT NOT NULL DEFAULT '',
    FOREIGN KEY (tracking_id) REFERENCES packages(tracking_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_events_tracking_id ON tracking_events(tracking_id);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON tracking_events(tracking_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS discovered_packages (
    tracking_id TEXT PRIMARY KEY,
    vendor TEXT NOT NULL,
    source_subject TEXT NOT NULL DEFAULT '',
    source_sender TEXT NOT NULL DEFAULT '',
    discovered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
