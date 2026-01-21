#!/usr/bin/env bash

set -euo pipefail

PORT="${JUPYTER_PORT:-8888}"
TOKEN="${JUPYTER_TOKEN:-}"
PASSWORD_HASH="${JUPYTER_PASSWORD_HASH:-}"
DISABLE_TOKEN_ON_PASSWORD="${JUPYTER_DISABLE_TOKEN_ON_PASSWORD:-true}"

args=(
    "--ServerApp.ip=0.0.0.0"
    "--ServerApp.port=${PORT}"
    "--ServerApp.open_browser=False"
    "--ServerApp.allow_origin=*"
    "--ServerApp.root_dir=/app"
    "--ServerApp.preferred_dir=/app"
    "--ServerApp.allow_root=True"
)

if [[ -n "${PASSWORD_HASH}" ]]; then
    args+=("--ServerApp.password=${PASSWORD_HASH}")
    args+=("--PasswordIdentityProvider.hashed_password=${PASSWORD_HASH}")
    disable_token="$(echo "${DISABLE_TOKEN_ON_PASSWORD}" | tr '[:upper:]' '[:lower:]')"
    if [[ "${disable_token}" == "true" || "${disable_token}" == "1" || "${disable_token}" == "yes" ]]; then
        TOKEN=""
    fi
fi

if [[ -n "${TOKEN}" ]]; then
    args+=("--ServerApp.token=${TOKEN}")
    args+=("--IdentityProvider.token=${TOKEN}")
else
    args+=("--ServerApp.token=")
    args+=("--IdentityProvider.token=")
fi

exec poetry run jupyter lab "${args[@]}"
