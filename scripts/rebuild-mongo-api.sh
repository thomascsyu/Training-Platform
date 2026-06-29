#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_READY_URL="${API_READY_URL:-http://localhost:8001/ready}"
RESET_DB=false
PULL_MONGO=false
START_WEB=false
ASSUME_YES=false

usage() {
  cat <<'EOF'
Usage: scripts/rebuild-mongo-api.sh [options]

Rebuild the LearnHub API container and restart MongoDB + API with Docker Compose.

Options:
  --reset-db     Remove the Compose MongoDB volume before starting services.
                 This deletes local MongoDB data.
  --pull-mongo   Pull the configured MongoDB image before starting services.
  --web          Start/recreate the web service after MongoDB and API are ready.
  -y, --yes      Skip confirmation prompts. Required for non-interactive reset.
  -h, --help     Show this help.

Environment:
  API_READY_URL  Readiness URL to poll. Default: http://localhost:8001/ready
EOF
}

while (($#)); do
  case "$1" in
    --reset-db)
      RESET_DB=true
      ;;
    --pull-mongo)
      PULL_MONGO=true
      ;;
    --web)
      START_WEB=true
      ;;
    -y|--yes)
      ASSUME_YES=true
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required but was not found on PATH." >&2
  exit 127
fi

cd "$PROJECT_DIR"

if [[ ! -f .env ]]; then
  echo "No root .env file found. Creating one from .env.docker.example." >&2
  cp .env.docker.example .env
  echo "Review .env before using production secrets." >&2
fi

if [[ "$RESET_DB" == true && "$ASSUME_YES" != true ]]; then
  echo "This will delete the local Docker Compose MongoDB volume." >&2
  read -r -p "Continue? [y/N] " answer
  case "$answer" in
    y|Y|yes|YES)
      ;;
    *)
      echo "Aborted." >&2
      exit 1
      ;;
  esac
fi

if [[ "$RESET_DB" == true ]]; then
  echo "Stopping services and removing Compose volumes..."
  docker compose down --volumes --remove-orphans
fi

if [[ "$PULL_MONGO" == true ]]; then
  echo "Pulling MongoDB image..."
  docker compose pull mongo
fi

echo "Building and starting MongoDB + API..."
docker compose up -d --build --force-recreate mongo api

echo "Waiting for API readiness at ${API_READY_URL}..."
for attempt in $(seq 1 60); do
  if python3 - "$API_READY_URL" <<'PY' >/dev/null 2>&1
import sys
import urllib.request

url = sys.argv[1]
with urllib.request.urlopen(url, timeout=2) as response:
    if 200 <= response.status < 300:
        raise SystemExit(0)
raise SystemExit(1)
PY
  then
    echo "API is ready."
    if [[ "$START_WEB" == true ]]; then
      echo "Starting web service..."
      docker compose up -d --build --force-recreate web
    fi
    docker compose ps
    exit 0
  fi

  sleep 2
  if (( attempt % 10 == 0 )); then
    echo "Still waiting for API readiness (${attempt}/60)..."
  fi
done

echo "API did not become ready. Recent API logs:" >&2
docker compose logs --tail=100 api >&2
exit 1
