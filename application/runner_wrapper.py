from __future__ import annotations

"""ansible-runner 실행 래퍼.

이 모듈의 책임:
1. 실행 단위 run_id 생성
2. run_id 기반 artifact 디렉터리 생성
3. ansible-runner 호출(check/apply)
4. runner 통계를 표준 응답 스키마로 변환
5. 실패 이벤트를 `failures[]`로 정리
"""

import os
import shutil
import uuid
from pathlib import Path
from typing import Any

import ansible_runner

from ..domain.schemas import FailureItem, HostSummary, RunResult

# 기본 artifact 루트. Linux 서버 기준 경로이며 환경변수로 재정의 가능하다.
DEFAULT_RUNS_ROOT = "/var/lib/ansible-mcp/runs"
DEFAULT_RUNS_KEEP_COUNT = 5
DEFAULT_STDOUT_MAX_LINES = 300


def _get_runs_keep_count() -> int:
    """runs artifact 보관 개수를 반환한다.

    우선순위:
    1) ANSIBLE_MCP_RUNS_BACKUP_COUNT
    2) ANSIBLE_MCP_LOG_BACKUP_COUNT (요청에 따른 통합 기준)
    3) 기본값(DEFAULT_RUNS_KEEP_COUNT)
    """
    raw = os.getenv("ANSIBLE_MCP_RUNS_BACKUP_COUNT")
    if raw is None:
        raw = os.getenv("ANSIBLE_MCP_LOG_BACKUP_COUNT", str(DEFAULT_RUNS_KEEP_COUNT))

    try:
        keep_count = int(raw)
    except (TypeError, ValueError):
        keep_count = DEFAULT_RUNS_KEEP_COUNT

    return max(1, keep_count)


def _cleanup_old_runs(base_dir: Path, keep_count: int) -> None:
    """runs 디렉터리에서 오래된 실행 artifact를 삭제한다."""
    if not base_dir.exists():
        return

    run_dirs = [item for item in base_dir.iterdir() if item.is_dir()]
    if len(run_dirs) <= keep_count:
        return

    run_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for stale_dir in run_dirs[keep_count:]:
        shutil.rmtree(stale_dir, ignore_errors=True)


def _get_stdout_max_lines() -> int:
    """stdout 반환 라인 수 제한을 반환한다.

    - `ANSIBLE_MCP_STDOUT_MAX_LINES`가 0 이하이면 전체 라인을 반환한다.
    - 미설정/오류 시 기본값(DEFAULT_STDOUT_MAX_LINES)을 사용한다.
    """
    raw = os.getenv("ANSIBLE_MCP_STDOUT_MAX_LINES", str(DEFAULT_STDOUT_MAX_LINES))
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = DEFAULT_STDOUT_MAX_LINES
    return value


def _read_stdout_from_run_dir(run_dir: Path, max_lines: int) -> tuple[str, int, bool]:
    """run artifact에서 stdout을 읽어 반환한다."""
    stdout_files = sorted(
        run_dir.glob("artifacts/*/stdout"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not stdout_files:
        return "", 0, False

    lines = stdout_files[0].read_text(encoding="utf-8", errors="replace").splitlines()
    line_count = len(lines)

    if max_lines <= 0 or line_count <= max_lines:
        return "\n".join(lines), line_count, False

    tail = lines[-max_lines:]
    return "\n".join(tail), line_count, True


def _collect_host_summary(stats: dict[str, Any]) -> dict[str, HostSummary]:
    """ansible-runner stats를 호스트별 ok/changed/failed/unreachable로 정규화한다.

    ansible-runner의 stats 키 매핑:
    - ok -> ok
    - changed -> changed
    - failures -> failed
    - dark -> unreachable
    """
    ok = stats.get("ok", {}) or {}
    changed = stats.get("changed", {}) or {}
    failed = stats.get("failures", {}) or {}
    unreachable = stats.get("dark", {}) or {}
    processed = stats.get("processed", {}) or {}

    hosts = set(processed.keys()) | set(ok.keys()) | set(changed.keys()) | set(failed.keys()) | set(unreachable.keys())

    out: dict[str, HostSummary] = {}
    for host in sorted(hosts):
        out[host] = HostSummary(
            ok=int(ok.get(host, 0)),
            changed=int(changed.get(host, 0)),
            failed=int(failed.get(host, 0)),
            unreachable=int(unreachable.get(host, 0)),
        )
    return out


def execute_playbook(
    *,
    playbook_path: str,
    inventory_path: str,
    check_mode: bool,
    extra_vars: dict[str, Any] | None = None,
    limit: str | None = None,
    tags: str | None = None,
    skip_tags: str | None = None,
    runs_root: str | None = None,
) -> RunResult:
    """playbook을 실행하고 표준 응답 스키마로 반환한다.

    Args:
        playbook_path: 실행 대상 playbook 경로(레지스트리에서 resolve된 값).
        inventory_path: 실행 대상 inventory 경로(레지스트리에서 resolve된 값).
        check_mode: True면 `--check`, False면 실제 적용.
        extra_vars: Ansible extra vars.
        limit: `--limit` 대상 호스트 표현식.
        tags: 실행할 태그.
        skip_tags: 제외할 태그.
        runs_root: artifact 루트(없으면 환경변수/기본값 사용).

    Returns:
        RunResult: run_id, host별 집계, 실패 목록 포함 결과.
    """
    run_id = str(uuid.uuid4())

    base_dir = Path(runs_root or os.getenv("ANSIBLE_MCP_RUNS_DIR", DEFAULT_RUNS_ROOT))
    run_dir = base_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # runs artifact 용량이 계속 누적되지 않도록 보관 개수 기반으로 정리한다.
    _cleanup_old_runs(base_dir, _get_runs_keep_count())

    failures: list[FailureItem] = []

    def _event_handler(event: dict[str, Any]) -> bool:
        """runner 이벤트를 받아 실패/접속불가 이벤트만 failures 배열로 축적한다."""
        event_name = event.get("event", "")
        if event_name not in {"runner_on_failed", "runner_on_unreachable"}:
            return True

        data = event.get("event_data", {}) or {}
        failures.append(
            FailureItem(
                host=str(data.get("host", "unknown")),
                task=str(data.get("task", "")),
                message=str(data.get("res", data.get("stdout", ""))),
                event=event_name,
            )
        )
        return True

    cmdline = "--check" if check_mode else ""

    # private_data_dir를 run 전용 디렉터리로 고정해 실행별 artifact를 분리 저장한다.
    result = ansible_runner.run(
        private_data_dir=str(run_dir),
        playbook=playbook_path,
        inventory=inventory_path,
        extravars=extra_vars or {},
        limit=limit,
        tags=tags,
        skip_tags=skip_tags,
        cmdline=cmdline,
        event_handler=_event_handler,
        quiet=True,
    )

    stats = result.stats if isinstance(result.stats, dict) else {}
    host_summary = _collect_host_summary(stats)

    stdout, stdout_line_count, stdout_truncated = _read_stdout_from_run_dir(
        run_dir=run_dir,
        max_lines=_get_stdout_max_lines(),
    )

    return RunResult(
        run_id=run_id,
        status=str(result.status),
        rc=int(result.rc if result.rc is not None else 1),
        host_summary=host_summary,
        failures=failures,
        artifact_dir=str(run_dir),
        stdout=stdout,
        stdout_line_count=stdout_line_count,
        stdout_truncated=stdout_truncated,
    )
