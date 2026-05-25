#!/usr/bin/with-contenv bashio
# shellcheck shell=bash

# Helper: read bashio config value only if bashio is available and key exists.
# Falls back to the current env var value or empty string.
read_config() {
  local key="$1"
  local val=""
  if bashio::config.exists "${key}" 2>/dev/null; then
    val=$(bashio::config "${key}" 2>/dev/null) || true
    # Filter "null" string returned when option has no value
    [[ "${val}" == "null" ]] && val=""
  fi
  echo "${val}"
}

# Read options from add-on config (only when running under HA Supervisor).
# Pre-existing env vars (e.g. from docker run -e) are preserved as fallback.
_POLL_INTERVAL=$(read_config 'poll_interval_minutes')
_EMAIL_POLL_INTERVAL=$(read_config 'email_poll_interval_minutes')
_LOG_LEVEL=$(read_config 'log_level')
_EMAIL_ENABLED=$(read_config 'email_enabled')
_EMAIL_HOST=$(read_config 'email_host')
_EMAIL_PORT=$(read_config 'email_port')
_EMAIL_USERNAME=$(read_config 'email_username')
_EMAIL_PASSWORD=$(read_config 'email_password')
_EMAIL_FOLDER=$(read_config 'email_folder')
_EMAIL_AUTO_ADD=$(read_config 'email_auto_add')

# Export with priority: bashio value > existing env var > default
export PAKETTI_POLL_INTERVAL="${_POLL_INTERVAL:-${PAKETTI_POLL_INTERVAL:-60}}"
export PAKETTI_EMAIL_POLL_INTERVAL="${_EMAIL_POLL_INTERVAL:-${PAKETTI_EMAIL_POLL_INTERVAL:-30}}"
export PAKETTI_EMAIL_ENABLED="${_EMAIL_ENABLED:-${PAKETTI_EMAIL_ENABLED:-false}}"
export PAKETTI_EMAIL_HOST="${_EMAIL_HOST:-${PAKETTI_EMAIL_HOST:-}}"
export PAKETTI_EMAIL_PORT="${_EMAIL_PORT:-${PAKETTI_EMAIL_PORT:-993}}"
export PAKETTI_EMAIL_USERNAME="${_EMAIL_USERNAME:-${PAKETTI_EMAIL_USERNAME:-}}"
export PAKETTI_EMAIL_PASSWORD="${_EMAIL_PASSWORD:-${PAKETTI_EMAIL_PASSWORD:-}}"
export PAKETTI_EMAIL_FOLDER="${_EMAIL_FOLDER:-${PAKETTI_EMAIL_FOLDER:-INBOX}}"
export PAKETTI_EMAIL_AUTO_ADD="${_EMAIL_AUTO_ADD:-${PAKETTI_EMAIL_AUTO_ADD:-false}}"

# Validate log level, default to info
_LOG_LEVEL="${_LOG_LEVEL:-${PAKETTI_LOG_LEVEL:-info}}"
case "${_LOG_LEVEL}" in
  debug|info|warning|error|critical) ;;
  *) _LOG_LEVEL="info" ;;
esac
export PAKETTI_LOG_LEVEL="${_LOG_LEVEL}"

# SUPERVISOR_TOKEN is set automatically by HA Supervisor
# MQTT credentials are fetched at runtime via Supervisor API

cd /app || exit 1
exec uvicorn app.main:app --host 0.0.0.0 --port 8099 --log-level "${PAKETTI_LOG_LEVEL}"
