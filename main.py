from __future__ import annotations

"""HTTP (streamable) MCP server entrypoint."""

import os

from .application.env_loader import load_env_file


def main() -> None:
    """Start the MCP server with streamable HTTP transport.

    Env:
    - `ANSIBLE_MCP_HOST` (default: 0.0.0.0)
    - `ANSIBLE_MCP_PORT` (default: 5000)
    - `ANSIBLE_MCP_HTTP_PATH` (default: /mcp)
    """
    # 서버 기동 전에 .env를 로드해 경로/로그/포트 설정을 반영한다.
    load_env_file(env_path=os.getenv("ANSIBLE_MCP_ENV_FILE"), override=False)

    from .api.mcp_router import create_mcp_server

    host = os.getenv("ANSIBLE_MCP_HOST", "0.0.0.0")
    port = int(os.getenv("ANSIBLE_MCP_PORT", "5000"))
    path = os.getenv("ANSIBLE_MCP_HTTP_PATH", "/mcp")

    server = create_mcp_server(host=host, port=port, streamable_http_path=path)
    server.run(transport="streamable-http")


if __name__ == "__main__":
    main()
