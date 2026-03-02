#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
PID_FILE="${PID_FILE:-$APP_DIR/ansible-mcp.pid}"
LOG_DIR="${LOG_DIR:-/var/log/ansible-mcp}"
OUT_LOG="${OUT_LOG:-$LOG_DIR/server.out.log}"
ERR_LOG="${ERR_LOG:-$LOG_DIR/server.err.log}"

if [[ ! -f "$PID_FILE" ]]; then
  echo "status: stopped"
  echo "pid file: $PID_FILE (not found)"
  exit 1
fi

PID="$(cat "$PID_FILE" || true)"
if [[ -z "${PID}" ]]; then
  echo "status: unknown"
  echo "pid file: $PID_FILE (empty)"
  exit 1
fi

if kill -0 "$PID" 2>/dev/null; then
  echo "status: running"
  echo "pid: $PID"
  echo "pid file: $PID_FILE"
  echo "out log: $OUT_LOG"
  echo "err log: $ERR_LOG"
  exit 0
fi

echo "status: stopped (stale pid file)"
echo "pid file: $PID_FILE"
exit 1
