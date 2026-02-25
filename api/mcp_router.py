from __future__ import annotations

"""MCP server routing/wiring."""

import os

from mcp.server.fastmcp import FastMCP

from ..application.env_loader import load_env_file
from .tools import register_tools


def create_mcp_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    streamable_http_path: str = "/mcp",
) -> FastMCP:
    """Create MCP server instance and register tools."""
    # Ensure .env is loaded even when imported directly.
    load_env_file(env_path=os.getenv("ANSIBLE_MCP_ENV_FILE"), override=False)

    mcp = FastMCP(
        "ansible-mcp-server",
        host=host,
        port=port,
        streamable_http_path=streamable_http_path,
    )
    register_tools(mcp)
    return mcp
