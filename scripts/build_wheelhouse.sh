#!/usr/bin/env bash
set -euo pipefail

PYTHON_EXE="${PYTHON_EXE:-python3.11}"
REQUIREMENTS="${REQUIREMENTS:-requirements-offline.txt}"
OUTPUT_DIR="${OUTPUT_DIR:-wheelhouse}"

if [[ ! -f "${REQUIREMENTS}" ]]; then
  echo "Requirements file not found: ${REQUIREMENTS}" >&2
  exit 1
fi

mkdir -p "${OUTPUT_DIR}"

"${PYTHON_EXE}" -m pip download \
  --dest "${OUTPUT_DIR}" \
  -r "${REQUIREMENTS}"

echo "Wheelhouse ready at: ${OUTPUT_DIR}"
