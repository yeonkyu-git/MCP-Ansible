from __future__ import annotations

"""로깅 구성 모듈.

MCP 프로토콜은 stdout을 사용하므로, 애플리케이션 로그는 반드시 stderr로 분리해야 한다.
또한 운영/감사 추적을 위해 선택적으로 파일 로깅을 지원한다.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging() -> logging.Logger:
    """서버 공용 로거를 초기화해 반환한다.

    환경 변수:
    - `ANSIBLE_MCP_LOG_LEVEL`: DEBUG/INFO/WARNING/ERROR (기본 INFO)
    - `ANSIBLE_MCP_LOG_DIR`: app.log / audit.log 기본 디렉터리
    - `ANSIBLE_MCP_LOG_FILE`: 애플리케이션 로그 파일 경로 (우선순위 높음)
    - `ANSIBLE_MCP_LOG_MAX_BYTES`: 로테이션 크기 (기본 10MB)
    - `ANSIBLE_MCP_LOG_BACKUP_COUNT`: 보관 파일 개수 (기본 5)

    Returns:
        logging.Logger: stderr 출력이 설정된 로거.
    """
    logger = logging.getLogger("mcp-ansible")

    # 이미 초기화된 경우(재호출/재import) 기존 객체를 그대로 반환한다.
    if logger.handlers:
        return logger

    level_name = os.getenv("ANSIBLE_MCP_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")

    # stdout은 MCP JSON-RPC 프레임 전용이므로 stderr 핸들러를 사용한다.
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)

    logger.setLevel(level)
    logger.addHandler(stderr_handler)

    log_dir = os.getenv("ANSIBLE_MCP_LOG_DIR")
    log_file = os.getenv("ANSIBLE_MCP_LOG_FILE")
    max_bytes = int(os.getenv("ANSIBLE_MCP_LOG_MAX_BYTES", str(10 * 1024 * 1024)))
    backup_count = int(os.getenv("ANSIBLE_MCP_LOG_BACKUP_COUNT", "5"))

    # file 경로 우선순위: ANSIBLE_MCP_LOG_FILE > ANSIBLE_MCP_LOG_DIR/app.log
    resolved_log_file: Path | None = None
    if log_file:
        resolved_log_file = Path(log_file)
    elif log_dir:
        resolved_log_file = Path(log_dir) / "app.log"

    if resolved_log_file is not None:
        resolved_log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            filename=str(resolved_log_file),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger


def configure_audit_logger() -> logging.Logger:
    """감사 로그 전용 로거를 초기화해 반환한다.

    환경 변수:
    - `ANSIBLE_MCP_AUDIT_LOG_FILE`: 감사 로그 파일 절대/상대 경로
    - `ANSIBLE_MCP_LOG_DIR`: audit 파일 경로 미지정 시 기본 디렉터리
    - `ANSIBLE_MCP_LOG_MAX_BYTES`: 로테이션 크기 (기본 10MB)
    - `ANSIBLE_MCP_LOG_BACKUP_COUNT`: 보관 파일 개수 (기본 5)
    """
    logger = logging.getLogger("mcp-ansible-audit")

    if logger.handlers:
        return logger

    max_bytes = int(os.getenv("ANSIBLE_MCP_LOG_MAX_BYTES", str(10 * 1024 * 1024)))
    backup_count = int(os.getenv("ANSIBLE_MCP_LOG_BACKUP_COUNT", "5"))
    log_dir = os.getenv("ANSIBLE_MCP_LOG_DIR")
    audit_log_file = os.getenv("ANSIBLE_MCP_AUDIT_LOG_FILE")

    resolved_audit_file: Path | None = None
    if audit_log_file:
        resolved_audit_file = Path(audit_log_file)
    elif log_dir:
        resolved_audit_file = Path(log_dir) / "audit.log"

    logger.setLevel(logging.INFO)

    # 감사 로그 파일 경로가 없더라도 서버 동작은 유지하고 stderr로 대체한다.
    if resolved_audit_file is not None:
        resolved_audit_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            filename=str(resolved_audit_file),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(file_handler)
    else:
        fallback_handler = logging.StreamHandler(sys.stderr)
        fallback_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(fallback_handler)

    logger.propagate = False
    return logger
