from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .catalog_tools import register_catalog_tools
from .run_tools import register_run_tools


def register_tools(mcp: FastMCP) -> None:
    """모든 MCP tool 등록 진입점.

    역할:
    - tool 모듈별 등록 순서를 단일 지점에서 관리
    - `mcp_router`가 내부 구현 상세를 몰라도 되도록 캡슐화
    - 기능이 늘어나도 여기서 등록만 추가하면 확장 가능
    """
    # 조회성 tool 등록
    register_catalog_tools(mcp)
    # 실행성 tool 등록
    register_run_tools(mcp)
