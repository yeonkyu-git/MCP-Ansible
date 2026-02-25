from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from ...application.logging_config import configure_audit_logger, configure_logging
from ...application.registry_loader import RegistryLoader
from ...application.runner_wrapper import execute_playbook

logger = configure_logging()
audit_logger = configure_audit_logger()

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def resolve_registry_path(env_key: str, default_relative_path: str) -> Path:
    raw = os.getenv(env_key, "").strip()
    if raw:
        path = Path(raw)
        if not path.is_absolute():
            path = (BASE_DIR / path).resolve()
        return path
    return (BASE_DIR / default_relative_path).resolve()


PLAYBOOK_REGISTRY_PATH = resolve_registry_path(
    "ANSIBLE_MCP_PLAYBOOK_REGISTRY_PATH", "policy/registry_playbooks.yaml"
)
INVENTORY_REGISTRY_PATH = resolve_registry_path(
    "ANSIBLE_MCP_INVENTORY_REGISTRY_PATH", "policy/registry_inventories.yaml"
)

registry = RegistryLoader(
    playbook_registry_path=PLAYBOOK_REGISTRY_PATH,
    inventory_registry_path=INVENTORY_REGISTRY_PATH,
)

SENSITIVE_KEYWORDS = (
    "password",
    "passwd",
    "secret",
    "token",
    "key",
    "private",
    "credential",
    "vault",
)


def mask_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if any(word in key.lower() for word in SENSITIVE_KEYWORDS):
                out[key] = "***MASKED***"
            else:
                out[key] = mask_sensitive(item)
        return out
    if isinstance(value, list):
        return [mask_sensitive(item) for item in value]
    return value


def audit_log(event: str, payload: dict[str, Any]) -> None:
    record = {"event": event, "ts": int(time.time()), **payload}
    audit_logger.info(json.dumps(record, ensure_ascii=False))


def run_playbook(
    *,
    playbook_id: str,
    inventory_id: str,
    check_mode: bool,
    extra_vars: dict[str, Any] | None,
    limit: str | None,
    tags: str | None,
    skip_tags: str | None,
) -> dict[str, Any]:
    if extra_vars is not None and not isinstance(extra_vars, dict):
        raise ValueError("extra_vars must be an object")

    playbook_path = registry.resolve_playbook(playbook_id)
    inventory_path = registry.resolve_inventory(inventory_id)

    result = execute_playbook(
        playbook_path=playbook_path,
        inventory_path=inventory_path,
        check_mode=check_mode,
        extra_vars=extra_vars,
        limit=limit,
        tags=tags,
        skip_tags=skip_tags,
    )
    return result.to_dict()
