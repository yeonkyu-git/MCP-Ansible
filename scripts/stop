#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
PID_FILE="${PID_FILE:-$APP_DIR/ansible-mcp.pid}"
GRACE_SECONDS="${GRACE_SECONDS:-10}"

if [[ ! -f "$PID_FILE" ]]; then
  echo "ansible-mcp is not running (pid file not found)"
  exit 0
fi

PID="$(cat "$PID_FILE" || true)"
if [[ -z "${PID}" ]]; then
  rm -f "$PID_FILE"
  echo "invalid pid file removed: $PID_FILE"
  exit 0
fi

if ! kill -0 "$PID" 2>/dev/null; then
  rm -f "$PID_FILE"
  echo "process already stopped (stale pid file removed)"
  exit 0
fi

kill "$PID"
for _ in $(seq 1 "$GRACE_SECONDS"); do
  if ! kill -0 "$PID" 2>/dev/null; then
    rm -f "$PID_FILE"
    echo "ansible-mcp stopped (pid=$PID)"
    exit 0
  fi
  sleep 1
done

kill -9 "$PID" 2>/dev/null || true
rm -f "$PID_FILE"
echo "ansible-mcp force-stopped (pid=$PID)"
