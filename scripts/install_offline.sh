#!/usr/bin/env bash
set -euo pipefail

PYTHON_EXE="${PYTHON_EXE:-python3.11}"
REQUIREMENTS="${REQUIREMENTS:-requirements-offline.txt}"
WHEELHOUSE_DIR="${WHEELHOUSE_DIR:-wheelhouse}"
VENV_DIR="${VENV_DIR:-.venv}"

if [[ ! -f "${REQUIREMENTS}" ]]; then
  echo "Requirements file not found: ${REQUIREMENTS}" >&2
  exit 1
fi

if [[ ! -d "${WHEELHOUSE_DIR}" ]]; then
  echo "Wheelhouse directory not found: ${WHEELHOUSE_DIR}" >&2
  exit 1
fi

"${PYTHON_EXE}" -m venv "${VENV_DIR}"

VENV_PYTHON="${VENV_DIR}/bin/python"
if [[ ! -x "${VENV_PYTHON}" ]]; then
  echo "Venv python not found: ${VENV_PYTHON}" >&2
  exit 1
fi

"${VENV_PYTHON}" -m pip install \
  --no-index \
  --find-links "${WHEELHOUSE_DIR}" \
  -r "${REQUIREMENTS}"

echo "Offline install completed in venv: ${VENV_DIR}"
echo "Run from package parent directory:"
echo "  ${VENV_DIR}/bin/python -m mcp_ansible.main"
