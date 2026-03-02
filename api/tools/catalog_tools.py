from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from ...application.registry_loader import RegistryError
from .context import audit_log, logger, registry


def _parse_ini_inventory_hosts(inventory_path: Path) -> dict[str, Any]:
    """INI inventory 파일에서 제어 가능한 호스트 목록을 추출한다."""
    if not inventory_path.exists():
        raise ValueError(f"inventory file not found: {inventory_path}")

    groups: dict[str, list[str]] = {}
    all_hosts: set[str] = set()
    current_group = "ungrouped"

    for raw_line in inventory_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue

        if line.startswith("[") and line.endswith("]"):
            group_name = line[1:-1].strip()
            # [group:vars], [group:children] 같은 메타 섹션은 호스트 목록에서 제외한다.
            if ":" in group_name:
                current_group = ""
            else:
                current_group = group_name
                groups.setdefault(current_group, [])
            continue

        if not current_group:
            continue

        host = line.split()[0]
        if host and host not in groups[current_group]:
            groups[current_group].append(host)
            all_hosts.add(host)

    return {
        "inventory_path": str(inventory_path),
        "host_count": len(all_hosts),
        "hosts": sorted(all_hosts),
        "groups": groups,
    }


def register_catalog_tools(mcp: FastMCP) -> None:
    # 등록된 playbook 요약 목록(ID + 설명)만 조회하는 tool
    @mcp.tool()
    def list_registered_playbooks() -> dict[str, dict[str, str]]:
        """등록된 playbook 요약 목록을 반환한다."""
        response = registry.list_playbook_summaries()
        audit_log("tool.result.list_registered_playbooks", {"count": len(response)})
        return response

    # 특정 playbook의 상세 스키마(path/inputs 포함)를 조회하는 tool
    @mcp.tool()
    def get_playbook_schema(playbook_id: str) -> dict[str, Any]:
        """특정 playbook의 상세 메타데이터를 반환한다."""
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

    # 특정 inventory 파일을 파싱해 실제 제어 대상 호스트 목록을 반환하는 tool
    @mcp.tool()
    def list_inventory_hosts(inventory_id: str) -> dict[str, Any]:
        """inventory_id 기준으로 실제 호스트 목록과 그룹 구성을 반환한다."""
        try:
            inventory_path = Path(registry.resolve_inventory(inventory_id))
            response = _parse_ini_inventory_hosts(inventory_path)
            audit_log(
                "tool.result.list_inventory_hosts",
                {
                    "inventory_id": inventory_id,
                    "host_count": response.get("host_count", 0),
                },
            )
            return response
        except RegistryError as exc:
            logger.error("registry lookup failed: %s", exc)
            audit_log("tool.error.list_inventory_hosts", {"inventory_id": inventory_id, "error": str(exc)})
            raise ValueError(str(exc)) from exc
        except Exception as exc:
            audit_log("tool.error.list_inventory_hosts", {"inventory_id": inventory_id, "error": str(exc)})
            raise
