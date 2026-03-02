# mcp_ansible
Ansible를 MCP Tool Server(HTTP `streamable-http`)로 제공하는 프로젝트입니다.

## 1. 한눈에 보기
| 항목 | 내용 |
|---|---|
| 목적 | AI가 `playbook_id`/`inventory_id` 기반으로만 안전하게 Ansible 실행 |
| 실행 방식 | `run_playbook_check` -> 검토 -> `run_playbook_apply` |
| 정책 파일 | `policy/registry_playbooks.yaml`, `policy/registry_inventories.yaml` |
| 엔트리포인트 | `python -m mcp_ansible.main` |

## 2. 핵심 원칙
- 임의 파일 경로 직접 입력 금지
- allow-list(ID) 기반 실행
- 감사 로그(JSON line) 기록
- runs artifact 자동 정리(보관 개수 기준)

## 3. 프로젝트 구조
```text
mcp_ansible/
├─ main.py
├─ api/
│  ├─ mcp_router.py
│  └─ tools/
│     ├─ register.py
│     ├─ catalog_tools.py
│     ├─ run_tools.py
│     └─ context.py
├─ application/
│  ├─ env_loader.py
│  ├─ logging_config.py
│  ├─ registry_loader.py
│  └─ runner_wrapper.py
├─ domain/
│  └─ schemas.py
└─ policy/
   ├─ registry_playbooks.yaml
   ├─ registry_inventories.yaml
   └─ Playbook/
```

## 4. 설치
```bash
pip install -e .
```

또는

```bash
uv sync
```

## 5. 폐쇄망 서버 배포 (권장 절차)
### 5.1 준비 조건
- 폐쇄망 서버 Linux 환경 (예: Rocky 9)
- Python 3.11 사용 가능
- Ansible 실행 환경 준비
  - 방법 A: 서버에 `ansible-core`가 이미 설치됨
  - 방법 B: 오프라인 설치 시 `requirements-offline-with-ansible214.txt` 사용

### 5.2 인터넷 가능한 환경에서 패키지 준비
Linux/macOS:
```bash
cd mcp_ansible
bash ./scripts/build_wheelhouse.sh
```

`ansible-core`까지 포함하려면:
```bash
cd mcp_ansible
REQUIREMENTS=requirements-offline-with-ansible214.txt bash ./scripts/build_wheelhouse.sh
```

Windows PowerShell:
```powershell
cd mcp_ansible
powershell -ExecutionPolicy Bypass -File .\scripts\build_wheelhouse.ps1
```

`ansible-core`까지 포함하려면:
```powershell
cd mcp_ansible
powershell -ExecutionPolicy Bypass -File .\scripts\build_wheelhouse.ps1 -Requirements requirements-offline-with-ansible214.txt
```

### 5.3 폐쇄망 서버로 복사
아래를 복사합니다.
- `mcp_ansible/`
- `wheelhouse/`

### 5.4 폐쇄망 서버에서 오프라인 설치
Linux:
```bash
cd /engn/mcp/mcp_ansible
bash ./scripts/install_offline.sh
```

`ansible-core` 포함 설치:
```bash
cd /engn/mcp/mcp_ansible
REQUIREMENTS=requirements-offline-with-ansible214.txt bash ./scripts/install_offline.sh
```

Windows PowerShell:
```powershell
cd D:\MCPTools\mcp_ansible
powershell -ExecutionPolicy Bypass -File .\scripts\install_offline.ps1
```

`ansible-core`까지 포함하려면:
```powershell
cd D:\MCPTools\mcp_ansible
powershell -ExecutionPolicy Bypass -File .\scripts\install_offline.ps1 -Requirements requirements-offline-with-ansible214.txt
```

### 5.5 `.env` 설정 (중요)
`policy/*.yaml`의 경로는 환경변수 치환을 사용하므로, 실제 배치 경로에 맞게 설정합니다.

예시:
```env
ANSIBLE_MCP_HOST=0.0.0.0
ANSIBLE_MCP_PORT=5000
ANSIBLE_MCP_HTTP_PATH=/mcp

ANSIBLE_MCP_PLAYBOOK_ROOT=/engn/ansible/playbook
ANSIBLE_MCP_INVENTORY_ROOT=/engn/ansible

ANSIBLE_MCP_RUNS_DIR=/var/lib/ansible-mcp/runs
ANSIBLE_MCP_LOG_LEVEL=INFO
ANSIBLE_MCP_LOG_DIR=/var/log/ansible-mcp
ANSIBLE_MCP_LOG_MAX_BYTES=10485760
ANSIBLE_MCP_LOG_BACKUP_COUNT=5
```

커스텀 env 경로를 사용할 경우:
```bash
ANSIBLE_MCP_ENV_FILE=/etc/ansible-mcp/.env ./mcp_ansible/.venv/bin/python -m mcp_ansible.main
```

### 5.6 서버 실행
```bash
cd /engn/mcp
./mcp_ansible/.venv/bin/python -m mcp_ansible.main
```

### 5.7 동작 확인 순서
1. `list_registered_playbooks`
2. `get_playbook_schema`
3. `list_registered_inventories`
4. `run_playbook_check`
5. 필요 시 `run_playbook_apply`

## 6. MCP 등록 예시
```toml
[mcp_servers.ansible_http]
transport = "streamable_http"
url = "http://<ANSIBLE_SERVER_IP>:5000/mcp"
```

## 7. 제공 Tool
| Tool | 설명 |
|---|---|
| `list_registered_playbooks` | playbook 요약 목록(ID, description) |
| `get_playbook_schema` | 특정 playbook 상세(`path`, `inputs`) |
| `list_registered_inventories` | inventory 목록 |
| `run_playbook_check` | check 모드 실행 |
| `run_playbook_apply` | apply 모드 실행 |

## 8. 입력/출력 규칙
### 입력
- 실행은 `playbook_id`, `inventory_id` 기준
- `extra_vars`는 JSON object
- `extra_vars`는 playbook `inputs` 스키마 기준으로 런타임 검증(필수값/타입/enum)
- 정책 파일의 `path`는 환경변수 치환 지원

### 출력
- `run_id`
- `status`
- `rc`
- `host_summary`
- `failures`
- `artifact_dir`

## 9. 주요 환경변수
| 변수 | 설명 |
|---|---|
| `ANSIBLE_MCP_HOST`, `ANSIBLE_MCP_PORT`, `ANSIBLE_MCP_HTTP_PATH` | 서버 바인딩 |
| `ANSIBLE_MCP_ENV_FILE` | 커스텀 `.env` 경로 |
| `ANSIBLE_MCP_PLAYBOOK_ROOT` | playbook 루트 경로 |
| `ANSIBLE_MCP_INVENTORY_ROOT` | inventory 루트 경로 |
| `ANSIBLE_MCP_RUNS_DIR` | runs artifact 저장 경로 |
| `ANSIBLE_MCP_RUNS_BACKUP_COUNT` | runs 보관 개수(미설정 시 `LOG_BACKUP_COUNT` 사용) |
| `ANSIBLE_MCP_LOG_LEVEL` | 로그 레벨 |
| `ANSIBLE_MCP_LOG_DIR` | 기본 로그 디렉터리(`app.log`, `audit.log`) |
| `ANSIBLE_MCP_LOG_FILE` | 앱 로그 파일 경로 |
| `ANSIBLE_MCP_AUDIT_LOG_FILE` | 감사 로그 파일 경로 |
| `ANSIBLE_MCP_LOG_MAX_BYTES` | 로그 로테이션 크기 |
| `ANSIBLE_MCP_LOG_BACKUP_COUNT` | 로그 백업 개수 |

## 10. 운영 권고
- `policy/*.yaml`은 관리자만 수정
- apply 전 check 결과 반드시 검토
- log/runs 디렉터리 권한 최소화
- 비밀정보는 Vault/외부 Secret Manager 사용

## 11. 백그라운드 실행 (Linux)
`nohup` 기반 백그라운드 실행 스크립트를 제공합니다.

```bash
bash ./scripts/start
```

주요 환경변수:
- `APP_DIR` (기본: 스크립트 기준 프로젝트 루트)
- `PYTHON_BIN` (기본: `$APP_DIR/.venv/bin/python`)
- `LOG_DIR` (기본: `/var/log/ansible-mcp`)
- `PID_FILE` (기본: `$APP_DIR/ansible-mcp.pid`)

중지:
```bash
bash ./scripts/stop
```

상태 확인:
```bash
bash ./scripts/status
```

## 12. 배포 트러블슈팅
### 12.1 PowerShell 스크립트 실행 차단
증상:
- `running scripts is disabled on this system`

해결:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_wheelhouse.ps1
```

### 12.2 Windows에서 Linux wheel 강제 다운로드 시 `pywin32` 오류
증상:
- `No matching distribution found for pywin32>=310; sys_platform == "win32"`

원인:
- Windows 조건부 의존성이 함께 평가되어 Linux 대상 wheel 다운로드와 충돌

해결:
- Windows 직접 생성 대신 WSL/Linux에서 wheelhouse 생성

### 12.3 WSL에서 `python3.11: command not found`
증상:
- `./scripts/build_wheelhouse.sh: line 15: python3.11: command not found`

해결:
```bash
PYTHON_EXE=python bash ./scripts/build_wheelhouse.sh
```

ansible-core 포함:
```bash
PYTHON_EXE=python REQUIREMENTS=requirements-offline-with-ansible214.txt bash ./scripts/build_wheelhouse.sh
```

### 12.4 오프라인 설치 시 `PyYAML>=6.0.2` 미탐지
증상:
- `No matching distribution found for PyYAML>=6.0.2`

원인:
- wheelhouse ABI 불일치 (예: `cp312` wheel을 Python 3.11 서버에 설치)

확인:
```bash
ls wheelhouse | grep -i pyyaml
```
- 파일명에 `cp311` 포함 필요

해결:
- `cp311` 기준으로 wheelhouse 재생성 후 재복사

### 12.5 서버 Python 다중 버전 이슈
예:
- `python3 --version` -> 3.9.x
- `python --version` -> 3.11.x

해결:
```bash
PYTHON_EXE=python REQUIREMENTS=requirements-offline-with-ansible214.txt bash ./scripts/install_offline.sh
```
