#!/usr/bin/env bash
# Smoke test the packaged jar in a container: build, run, curl, stop.
#
# Testcontainers is the right tool when a test needs a *database* container. This app is SQLite, so a
# container buys exactly one thing: proof that the image starts and answers. That is a shell script.
set -euo pipefail
cd "$(dirname "$0")/.."

NAME=legacy-smoke-$$
PORT=${PORT:-18080}

docker build -q -t legacy-revive-lab:smoke legacy-app >/dev/null
docker run -d --rm --name "$NAME" -p "$PORT:8080" legacy-revive-lab:smoke >/dev/null
trap 'docker stop "$NAME" >/dev/null 2>&1 || true' EXIT

for i in $(seq 1 45); do
  if curl -fsS "http://localhost:$PORT/api/legacy/ping" >/dev/null 2>&1; then
    echo "OK  GET /api/legacy/ping -> $(curl -fsS "http://localhost:$PORT/api/legacy/ping")"
    echo "OK  GET /api/customers/1 -> $(curl -fsS "http://localhost:$PORT/api/customers/1" | head -c 90)..."
    exit 0
  fi
  sleep 1
done

echo "FAIL the container never answered on port $PORT"
docker logs "$NAME" 2>&1 | tail -20
exit 1
