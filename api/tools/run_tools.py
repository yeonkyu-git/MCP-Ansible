from __future__ import annotations

import time
from typing import Any

from mcp.server.fastmcp import FastMCP

from ...application.registry_loader import RegistryError
from .context import audit_log, logger, mask_sensitive, registry, run_playbook


def _is_type_match(value: Any, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return (isinstance(value, int) and not isinstance(value, bool)) or isinstance(value, float)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "object":
        return isinstance(value, dict)
    return False


def _matches_type_spec(value: Any, type_spec: str) -> bool:
    expected_types = [item.strip() for item in type_spec.split("|") if item.strip()]
    return any(_is_type_match(value, expected_type) for expected_type in expected_types)


def _validate_extra_vars(playbook_id: str, extra_vars: dict[str, Any] | None) -> None:
    if extra_vars is None:
        extra_vars = {}

    metadata = registry.get_playbook(playbook_id)
    inputs = metadata.get("inputs", [])
    schema_by_name = {str(item.get("name")): item for item in inputs if isinstance(item, dict)}

    unknown_keys = sorted(set(extra_vars.keys()) - set(schema_by_name.keys()))
    if unknown_keys:
        raise ValueError(
            f"unsupported extra_vars for playbook '{playbook_id}': {', '.join(unknown_keys)}"
        )

    missing_required: list[str] = []
    for name, schema in schema_by_name.items():
        if bool(schema.get("required")) and name not in extra_vars:
            missing_required.append(name)
    if missing_required:
        raise ValueError(
            f"missing required extra_vars for playbook '{playbook_id}': {', '.join(sorted(missing_required))}"
        )

    for name, value in extra_vars.items():
        schema = schema_by_name.get(name, {})
        type_spec = str(schema.get("type", "")).strip()
        if type_spec and not _matches_type_spec(value, type_spec):
            raise ValueError(
                f"invalid type for extra_var '{name}' in playbook '{playbook_id}': expected {type_spec}"
            )

        enum_values = schema.get("enum")
        if isinstance(enum_values, list) and value not in enum_values:
            allowed = ", ".join(str(item) for item in enum_values)
            raise ValueError(
                f"invalid value for extra_var '{name}' in playbook '{playbook_id}': allowed [{allowed}]"
            )


def register_run_tools(mcp: FastMCP) -> None:
    # check mode 실행 tool (실제 변경 없이 영향도 점검)
    @mcp.tool()
    def run_playbook_check(
        playbook_id: str,
        inventory_id: str,
        extra_vars: dict[str, Any] | None = None,
        limit: str | None = None,
        tags: str | None = None,
        skip_tags: str | None = None,
    ) -> dict[str, Any]:
        """Allow-list 기반 playbook을 check mode로 실행한다.

        Args:
            playbook_id: 실행할 playbook ID
            inventory_id: 실행할 inventory ID
            extra_vars: 플레이북 변수
            limit: 대상 호스트 제한
            tags: 실행할 태그
            skip_tags: 제외할 태그
        """
        started_at = time.perf_counter()
        audit_log(
            "tool.request.run_playbook_check",
            {
                "playbook_id": playbook_id,
                "inventory_id": inventory_id,
                "limit": limit,
                "tags": tags,
                "skip_tags": skip_tags,
                "extra_vars": mask_sensitive(extra_vars or {}),
            },
        )
        try:
            _validate_extra_vars(playbook_id=playbook_id, extra_vars=extra_vars)
            result = run_playbook(
                playbook_id=playbook_id,
                inventory_id=inventory_id,
                check_mode=True,
                extra_vars=extra_vars,
                limit=limit,
                tags=tags,
                skip_tags=skip_tags,
            )
            audit_log(
                "tool.result.run_playbook_check",
                {
                    "playbook_id": playbook_id,
                    "inventory_id": inventory_id,
                    "run_id": result.get("run_id"),
                    "status": result.get("status"),
                    "rc": result.get("rc"),
                    "duration_ms": int((time.perf_counter() - started_at) * 1000),
                },
            )
            return result
        except RegistryError as exc:
            logger.error("registry validation failed: %s", exc)
            audit_log(
                "tool.error.run_playbook_check",
                {"playbook_id": playbook_id, "inventory_id": inventory_id, "error": str(exc)},
            )
            raise ValueError(str(exc)) from exc
        except Exception as exc:
            audit_log(
                "tool.error.run_playbook_check",
                {"playbook_id": playbook_id, "inventory_id": inventory_id, "error": str(exc)},
            )
            raise

    # apply mode 실행 tool (실제 시스템 변경)
    @mcp.tool()
    def run_playbook_apply(
        playbook_id: str,
        inventory_id: str,
        extra_vars: dict[str, Any] | None = None,
        limit: str | None = None,
        tags: str | None = None,
        skip_tags: str | None = None,
    ) -> dict[str, Any]:
        """Allow-list 기반 playbook을 apply mode로 실행한다.

        Args:
            playbook_id: 실행할 playbook ID
            inventory_id: 실행할 inventory ID
            extra_vars: 플레이북 변수
            limit: 대상 호스트 제한
            tags: 실행할 태그
            skip_tags: 제외할 태그
        """
        started_at = time.perf_counter()
        audit_log(
            "tool.request.run_playbook_apply",
            {
                "playbook_id": playbook_id,
                "inventory_id": inventory_id,
                "limit": limit,
                "tags": tags,
                "skip_tags": skip_tags,
                "extra_vars": mask_sensitive(extra_vars or {}),
            },
        )
        try:
            _validate_extra_vars(playbook_id=playbook_id, extra_vars=extra_vars)
            result = run_playbook(
                playbook_id=playbook_id,
                inventory_id=inventory_id,
                check_mode=False,
                extra_vars=extra_vars,
                limit=limit,
                tags=tags,
                skip_tags=skip_tags,
            )
            audit_log(
                "tool.result.run_playbook_apply",
                {
                    "playbook_id": playbook_id,
                    "inventory_id": inventory_id,
                    "run_id": result.get("run_id"),
                    "status": result.get("status"),
                    "rc": result.get("rc"),
                    "duration_ms": int((time.perf_counter() - started_at) * 1000),
                },
            )
            return result
        except RegistryError as exc:
            logger.error("registry validation failed: %s", exc)
            audit_log(
                "tool.error.run_playbook_apply",
                {"playbook_id": playbook_id, "inventory_id": inventory_id, "error": str(exc)},
            )
            raise ValueError(str(exc)) from exc
        except Exception as exc:
            audit_log(
                "tool.error.run_playbook_apply",
                {"playbook_id": playbook_id, "inventory_id": inventory_id, "error": str(exc)},
            )
            raise
