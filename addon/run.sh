#!/usr/bin/with-contenv bashio
# shellcheck shell=bash

# Read options from add-on config with defaults
PAKETTI_POLL_INTERVAL=$(bashio::config 'poll_interval_minutes' 2>/dev/null) || true
PAKETTI_EMAIL_POLL_INTERVAL=$(bashio::config 'email_poll_interval_minutes' 2>/dev/null) || true
PAKETTI_LOG_LEVEL=$(bashio::config 'log_level' 2>/dev/null) || true

# Filter out "null" values from bashio (returned when option not set)
[[ "${PAKETTI_POLL_INTERVAL}" == "null" ]] && PAKETTI_POLL_INTERVAL=""
[[ "${PAKETTI_EMAIL_POLL_INTERVAL}" == "null" ]] && PAKETTI_EMAIL_POLL_INTERVAL=""
[[ "${PAKETTI_LOG_LEVEL}" == "null" ]] && PAKETTI_LOG_LEVEL=""

# Apply defaults
export PAKETTI_POLL_INTERVAL="${PAKETTI_POLL_INTERVAL:-60}"
export PAKETTI_EMAIL_POLL_INTERVAL="${PAKETTI_EMAIL_POLL_INTERVAL:-30}"

# Validate log level, default to info
case "${PAKETTI_LOG_LEVEL}" in
  debug|info|warning|error|critical) ;;
  *) PAKETTI_LOG_LEVEL="info" ;;
esac
export PAKETTI_LOG_LEVEL

# SUPERVISOR_TOKEN is set automatically by HA Supervisor
# MQTT credentials are fetched at runtime via Supervisor API

cd /app || exit 1
exec uvicorn app.main:app --host 0.0.0.0 --port 8099 --log-level "${PAKETTI_LOG_LEVEL}"
