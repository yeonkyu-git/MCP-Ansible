#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
PYTHON_BIN="${PYTHON_BIN:-$APP_DIR/.venv/bin/python}"
PACKAGE_NAME="${PACKAGE_NAME:-$(basename "$APP_DIR")}"
RUN_CWD="${RUN_CWD:-$(dirname "$APP_DIR")}"
LOG_DIR="${LOG_DIR:-/var/log/ansible-mcp}"
PID_FILE="${PID_FILE:-$APP_DIR/ansible-mcp.pid}"
OUT_LOG="${OUT_LOG:-$LOG_DIR/server.out.log}"
ERR_LOG="${ERR_LOG:-$LOG_DIR/server.err.log}"

mkdir -p "$LOG_DIR"

if [[ -f "$PID_FILE" ]]; then
  OLD_PID="$(cat "$PID_FILE" || true)"
  if [[ -n "${OLD_PID}" ]] && kill -0 "$OLD_PID" 2>/dev/null; then
    echo "ansible-mcp already running (pid=$OLD_PID)"
    exit 0
  fi
  rm -f "$PID_FILE"
fi

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "python not found or not executable: $PYTHON_BIN" >&2
  exit 1
fi

cd "$RUN_CWD"
nohup "$PYTHON_BIN" -m "${PACKAGE_NAME}.main" >>"$OUT_LOG" 2>>"$ERR_LOG" &
NEW_PID=$!
echo "$NEW_PID" > "$PID_FILE"

echo "ansible-mcp started"
echo "pid: $NEW_PID"
echo "pid file: $PID_FILE"
echo "run cwd: $RUN_CWD"
echo "module: ${PACKAGE_NAME}.main"
echo "out log: $OUT_LOG"
echo "err log: $ERR_LOG"
