from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ...application.registry_loader import RegistryError
from .context import audit_log, logger, registry


def register_catalog_tools(mcp: FastMCP) -> None:
    # 등록된 playbook 요약 목록(ID + 설명)을 조회하는 tool
    @mcp.tool()
    def list_registered_playbooks() -> dict[str, dict[str, str]]:
        """등록된 playbook 요약 목록을 반환한다.

        Returns:
            dict[str, dict[str, str]]: `{playbook_id: {"description": "..."}}`
        """
        response = registry.list_playbook_summaries()
        audit_log("tool.result.list_registered_playbooks", {"count": len(response)})
        return response

    # 특정 playbook의 상세 스키마(path/inputs 포함)를 조회하는 tool
    @mcp.tool()
    def get_playbook_schema(playbook_id: str) -> dict[str, Any]:
        """특정 playbook의 상세 메타데이터를 반환한다.

        Args:
            playbook_id: 조회할 playbook ID
        """
        try:
            response = registry.get_playbook(playbook_id)
            audit_log(
                "tool.result.get_playbook_schema",
                {"playbook_id": playbook_id, "input_count": len(response.get("inputs", []))},
            )
            return response
        except RegistryError as exc:
            logger.error("registry lookup failed: %s", exc)
            audit_log("tool.error.get_playbook_schema", {"playbook_id": playbook_id, "error": str(exc)})
            raise ValueError(str(exc)) from exc

    # 등록된 inventory 목록(ID -> path)을 조회하는 tool
    @mcp.tool()
    def list_registered_inventories() -> dict[str, str]:
        """등록된 inventory 목록을 반환한다."""
        response = registry.list_inventories()
        audit_log("tool.result.list_registered_inventories", {"count": len(response)})
        return response
