#!/usr/bin/env bash
set -euo pipefail

# Local smoke test for mcp_ansible HTTP server.
# Runs initialize -> notifications/initialized -> tools/list -> tools/call(run_playbook_check)
# against 127.0.0.1 only.

BASE_URL="${BASE_URL:-http://127.0.0.1:5000/mcp}"
PROTOCOL_VERSION="${PROTOCOL_VERSION:-2025-11-25}"
PLAYBOOK_ID="${PLAYBOOK_ID:-ping_all}"
INVENTORY_ID="${INVENTORY_ID:-prod_linux}"
LIMIT_VALUE="${LIMIT_VALUE:-}"
CURL_BIN="${CURL_BIN:-curl}"
JQ_BIN="${JQ_BIN:-jq}"

if ! command -v "${CURL_BIN}" >/dev/null 2>&1; then
  echo "curl not found: ${CURL_BIN}" >&2
  exit 1
fi

if ! command -v "${JQ_BIN}" >/dev/null 2>&1; then
  echo "jq not found: ${JQ_BIN}" >&2
  exit 1
fi

parse_mcp_json() {
  # Accept either plain JSON or SSE payload and print normalized JSON.
  local raw="${1}"

  if echo "${raw}" | "${JQ_BIN}" -e . >/dev/null 2>&1; then
    echo "${raw}" | "${JQ_BIN}" .
    return 0
  fi

  local sse_data
  sse_data="$(echo "${raw}" | awk '/^data: /{sub(/^data: /, ""); print}' | tail -n 1)"
  if [[ -n "${sse_data}" ]] && echo "${sse_data}" | "${JQ_BIN}" -e . >/dev/null 2>&1; then
    echo "${sse_data}" | "${JQ_BIN}" .
    return 0
  fi

  echo "Failed to parse MCP response as JSON or SSE data." >&2
  echo "Raw response:" >&2
  echo "${raw}" >&2
  return 1
}

tmp_hdr="$(mktemp)"
tmp_body="$(mktemp)"
cleanup() {
  rm -f "${tmp_hdr}" "${tmp_body}"
}
trap cleanup EXIT

echo "[1/5] initialize -> ${BASE_URL}"
init_payload="$("${JQ_BIN}" -n \
  --arg pv "${PROTOCOL_VERSION}" \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":$pv,"capabilities":{},"clientInfo":{"name":"local-smoke","version":"1.0"}}}')"

"${CURL_BIN}" -sS -D "${tmp_hdr}" -o "${tmp_body}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -X POST "${BASE_URL}" \
  --data "${init_payload}"

sid="$(awk 'tolower($1)=="mcp-session-id:"{print $2}' "${tmp_hdr}" | tr -d '\r')"
if [[ -z "${sid}" ]]; then
  echo "Mcp-Session-Id not found in initialize response headers." >&2
  echo "Response body:" >&2
  cat "${tmp_body}" >&2
  exit 1
fi

echo "[2/5] notifications/initialized (session: ${sid})"
"${CURL_BIN}" -sS \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: ${sid}" \
  -X POST "${BASE_URL}" \
  --data '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}' >/dev/null

echo "[3/5] tools/list"
tools_resp="$("${CURL_BIN}" -sS \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: ${sid}" \
  -X POST "${BASE_URL}" \
  --data '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}')"
parse_mcp_json "${tools_resp}"

echo "[4/5] tools/call run_playbook_check"
call_payload="$("${JQ_BIN}" -n \
  --arg pb "${PLAYBOOK_ID}" \
  --arg inv "${INVENTORY_ID}" \
  --arg lim "${LIMIT_VALUE}" \
  '{
     "jsonrpc":"2.0",
     "id":3,
     "method":"tools/call",
     "params":{
       "name":"run_playbook_check",
       "arguments":(
         if $lim == "" then
           {"playbook_id":$pb,"inventory_id":$inv}
         else
           {"playbook_id":$pb,"inventory_id":$inv,"limit":$lim}
         end
       )
     }
   }')"

call_resp="$("${CURL_BIN}" -sS \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "Mcp-Session-Id: ${sid}" \
  -X POST "${BASE_URL}" \
  --data "${call_payload}")"
parse_mcp_json "${call_resp}"

echo "[5/5] done"
