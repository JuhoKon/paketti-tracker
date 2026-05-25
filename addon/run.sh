#!/usr/bin/with-contenv bashio
# shellcheck shell=bash

# Read options from add-on config
export PAKETTI_POLL_INTERVAL=$(bashio::config 'poll_interval_minutes')
export PAKETTI_EMAIL_POLL_INTERVAL=$(bashio::config 'email_poll_interval_minutes')
export PAKETTI_LOG_LEVEL=$(bashio::config 'log_level')

# SUPERVISOR_TOKEN is set automatically by HA Supervisor
# MQTT credentials are fetched at runtime via Supervisor API

exec uvicorn app.main:app --host 0.0.0.0 --port 8099 --log-level "${PAKETTI_LOG_LEVEL:-info}"
