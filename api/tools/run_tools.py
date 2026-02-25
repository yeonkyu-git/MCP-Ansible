from __future__ import annotations

import time
from typing import Any

from mcp.server.fastmcp import FastMCP

from ...application.registry_loader import RegistryError
from .context import audit_log, logger, mask_sensitive, run_playbook


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
