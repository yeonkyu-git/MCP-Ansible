from __future__ import annotations

"""환경변수 로더.

- `.env` 파일에서 환경변수를 로드한다.
- python-dotenv가 있으면 사용하고, 없으면 간단 파서로 fallback 한다.
"""

import os
from pathlib import Path


def _fallback_load_dotenv(env_path: Path, override: bool) -> bool:
    if not env_path.exists():
        return False

    loaded = False
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            continue

        if override or key not in os.environ:
            os.environ[key] = value
            loaded = True

    return loaded


def load_env_file(*, env_path: str | None = None, override: bool = False) -> bool:
    """`.env` 파일을 로드한다.

    Args:
        env_path: 지정하면 해당 경로, 미지정이면 현재 작업 디렉터리의 `.env`.
        override: True면 기존 환경변수 값을 덮어쓴다.

    Returns:
        bool: 하나라도 로드되면 True.
    """
    if env_path:
        targets = [Path(env_path)]
    else:
        package_root = Path(__file__).resolve().parent.parent
        targets = [package_root / ".env", Path.cwd() / ".env"]

    for target in targets:
        try:
            from dotenv import load_dotenv  # type: ignore

            if bool(load_dotenv(dotenv_path=target, override=override)):
                return True
        except Exception:
            if _fallback_load_dotenv(target, override):
                return True

    return False
