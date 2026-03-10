# mcp_ansible
Ansible를 MCP Tool Server(HTTP `streamable-http`)로 제공하는 프로젝트입니다.

## 1. 한눈에 보기
| 항목 | 내용 |
|---|---|
| 목적 | AI가 `playbook_id`/`inventory_id` 기반으로만 안전하게 Ansible 실행 |
| 실행 방식 | 조회형은 `run_playbook_apply`, 변경형은 `run_playbook_check` 검토 후 `run_playbook_apply` |
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
ANSIBLE_CONFIG=/engn/ansible/ansible.cfg

ANSIBLE_MCP_RUNS_DIR=/var/lib/ansible-mcp/runs
ANSIBLE_MCP_STDOUT_MAX_LINES=300
ANSIBLE_MCP_LOG_LEVEL=INFO
ANSIBLE_MCP_LOG_DIR=/var/log/ansible-mcp
ANSIBLE_MCP_LOG_MAX_BYTES=10485760
ANSIBLE_MCP_LOG_BACKUP_COUNT=5
```

커스텀 env 경로를 사용할 경우:
```bash
ANSIBLE_MCP_ENV_FILE=/etc/ansible-mcp/.env ./mcp_ansible/.venv/bin/python -m mcp_ansible.main
```

### 5.6 서버 기동/중지/상태확인
기동:
```bash
cd /engn/mcp/mcp_ansible
bash ./scripts/start.sh
```

중지:
```bash
cd /engn/mcp/mcp_ansible
bash ./scripts/stop.sh
```

상태확인:
```bash
cd /engn/mcp/mcp_ansible
bash ./scripts/status.sh
```

### 5.7 동작 확인 순서
1. `list_registered_playbooks`
2. `get_playbook_schema`
3. `list_registered_inventories`
4. `list_inventory_hosts` (실제 제어 대상 서버 목록 확인)
5. 조회형 진단 playbook은 `run_playbook_apply`
6. 변경형 playbook은 `run_playbook_check` 후 필요 시 `run_playbook_apply`

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
| `list_inventory_hosts` | inventory 파일 기준 실제 호스트/그룹 목록 |
| `run_playbook_check` | check 모드 실행(변경형 playbook 사전 검토용) |
| `run_playbook_apply` | apply 모드 실행(조회형 playbook 실제 실행 포함) |

## 8. 운영자 질의-Playbook 매핑
| 질문 유형(예시) | 권장 Playbook ID | 실행 시 핵심 입력 예시 |
|---|---|---|
| 서버 접속/SSH 연결 확인 | `ping_all` | `limit: web01` |
| 서버 기본 정보 확인(CPU/Mem/FS/User/Group) | `gather_facts_only` | `limit: all` |
| 계정 생성/삭제/셸 변경 | `user_account_manage` | `user_name: opsuser`, `user_state: present` |
| sudo 권한 추가/제거/조회 | `sudoers_manage` | `sudo_action: audit` 또는 `sudo_action: present`, `sudo_user: opsuser` |
| 패키지 전체 업데이트/특정 패키지 설치/제거 | `package_manage` | `package_action: install`, `package_names: ["nginx"]` |
| 서비스 시작/중지/재시작/활성화 | `systemd_service_manage` | `service_name: nginx`, `service_state: restarted`, `service_enabled: true` |
| 지정 디렉터리 파일 목록 확인 | `file_list_files` | `target_dir: /var/log` |
| 지정 파일 마지막 N줄 확인 | `file_tail_file` | `target_file: /var/log/messages`, `tail_lines: 100` |
| 지정 파일에서 ERROR/키워드 검색 | `file_grep_pattern` | `target_file: /var/log/messages`, `search_pattern: ERROR` |
| systemd 저널에서 서비스 에러 확인 | `journal_service_errors` | `service_name: nginx`, `journal_lines: 100` |
| CPU 많이 쓰는 프로세스 확인 | `process_top_cpu` | `top_n: 20` |
| 메모리 많이 쓰는 프로세스 확인 | `process_top_memory` | `top_n: 20` |
| 서비스 상세 상태 및 최근 로그 확인 | `service_status_detail` | `service_name: nginx`, `journal_lines: 50` |
| 최근 시스템 에러 로그 확인 | `journal_recent_errors` | `since: -30m`, `journal_lines: 100` |
| 최근 커널 메시지 확인 | `kernel_recent_messages` | `message_lines: 100` |
| 디렉터리 사용량 상위 항목 확인 | `directory_usage_snapshot` | `target_dir: /var`, `max_depth: 2`, `top_n: 20` |
| 특정 PID의 thread별 CPU 확인 | `process_threads_cpu` | `pid: 1234`, `top_n: 20` |
| 특정 PID의 실행 상세 정보 확인 | `process_runtime_detail` | `pid: 1234` |
| 현재 TCP/UDP 연결 상태 확인 | `socket_connection_snapshot` | `top_n: 100` |
| 디스크 I/O 상태 확인 | `disk_io_snapshot` | `sample_interval: 1`, `sample_count: 3` |
| 최근 변경 파일 목록 확인 | `file_recent_changes` | `target_dir: /var/log`, `top_n: 20` |
| 특정 포트 리스너 확인 | `port_listener_detail` | `target_port: 8080` |
| 원격 IP별 상위 연결 수 확인 | `connection_top_remote_ips` | `top_n: 20` |
| 네트워크 인터페이스 상태 확인 | `network_interface_detail` | `interface_name: eth0` |


### 8.1 실행 모드 권장
- 조회형 playbook은 `command`/`shell` 기반 task가 많아 Ansible check mode에서 skip될 수 있습니다.
- 따라서 아래 playbook은 **read-only**이지만 실제 조회를 위해 `run_playbook_apply` 사용을 권장합니다.
  - `ping_all`, `gather_facts_only`
  - `file_list_files`, `file_tail_file`, `file_grep_pattern`, `file_recent_changes`
  - `process_top_cpu`, `process_top_memory`, `process_threads_cpu`, `process_runtime_detail`
  - `service_status_detail`, `journal_service_errors`, `journal_recent_errors`, `kernel_recent_messages`
  - `directory_usage_snapshot`, `disk_io_snapshot`
  - `socket_connection_snapshot`, `port_listener_detail`, `connection_top_remote_ips`, `network_interface_detail`
- 계정/패키지/서비스 상태를 바꾸는 변경형 playbook은 `run_playbook_check`로 먼저 검토한 뒤 `run_playbook_apply`를 사용합니다.
## 9. 입력/출력 규칙
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
- `stdout` (기본: tail N줄)
- `stdout_line_count`
- `stdout_truncated`

## 10. 주요 환경변수
| 변수 | 설명 |
|---|---|
| `ANSIBLE_MCP_HOST`, `ANSIBLE_MCP_PORT`, `ANSIBLE_MCP_HTTP_PATH` | 서버 바인딩 |
| `ANSIBLE_MCP_ENV_FILE` | 커스텀 `.env` 경로 |
| `ANSIBLE_MCP_PLAYBOOK_ROOT` | playbook 루트 경로 |
| `ANSIBLE_MCP_INVENTORY_ROOT` | inventory 루트 경로 |
| `ANSIBLE_CONFIG` | ansible.cfg 절대 경로(권장 고정) |
| `ANSIBLE_MCP_RUNS_DIR` | runs artifact 저장 경로 |
| `ANSIBLE_MCP_STDOUT_MAX_LINES` | Tool 응답에 포함할 stdout 최대 줄 수(0 이하: 전체) |
| `ANSIBLE_MCP_RUNS_BACKUP_COUNT` | runs 보관 개수(미설정 시 `LOG_BACKUP_COUNT` 사용) |
| `ANSIBLE_MCP_LOG_LEVEL` | 로그 레벨 |
| `ANSIBLE_MCP_LOG_DIR` | 기본 로그 디렉터리(`app.log`, `audit.log`) |
| `ANSIBLE_MCP_LOG_FILE` | 앱 로그 파일 경로 |
| `ANSIBLE_MCP_AUDIT_LOG_FILE` | 감사 로그 파일 경로 |
| `ANSIBLE_MCP_LOG_MAX_BYTES` | 로그 로테이션 크기 |
| `ANSIBLE_MCP_LOG_BACKUP_COUNT` | 로그 백업 개수 |

## 11. 운영 권고
- `policy/*.yaml`은 관리자만 수정
- apply 전 check 결과 반드시 검토
- log/runs 디렉터리 권한 최소화
- 비밀정보는 Vault/외부 Secret Manager 사용

## 12. 백그라운드 실행 (Linux)
`nohup` 기반 백그라운드 실행 스크립트를 제공합니다.

```bash
bash ./scripts/start.sh
```

주요 환경변수:
- `APP_DIR` (기본: 스크립트 기준 프로젝트 루트)
- `PYTHON_BIN` (기본: `$APP_DIR/.venv/bin/python`)
- `LOG_DIR` (기본: `/var/log/ansible-mcp`)
- `PID_FILE` (기본: `$APP_DIR/ansible-mcp.pid`)

중지:
```bash
bash ./scripts/stop.sh
```

상태 확인:
```bash
bash ./scripts/status.sh
```

## 13. 배포 트러블슈팅
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



## 14. Recent Implementation Summary
- Refactored tool modules into `catalog_tools` and `run_tools` for maintainability.
- Adopted 2-step catalog flow: summary (`list_registered_playbooks`) then schema detail (`get_playbook_schema`).
- Added inventory host discovery tool: `list_inventory_hosts(inventory_id)`.
- Added runtime `extra_vars` validation (required/type/enum/unknown key).
- Improved logging with structured audit events (JSON line).
- Extended `.env`-based path/config injection and prioritized project-root `.env` loading.
- Included stdout in run responses: `stdout`, `stdout_line_count`, `stdout_truncated`.
- Added `ANSIBLE_MCP_STDOUT_MAX_LINES` to control response stdout volume.
- Added run artifact retention cleanup (keep-count based).
- Standardized service scripts as `start.sh`, `stop.sh`, `status.sh`.

## 15. 로그 파일 정리
| 로그 파일 경로 | 생성 주체 | 내용 |
| --- | --- | --- |
| `${ANSIBLE_MCP_LOG_FILE}` 또는 `${ANSIBLE_MCP_LOG_DIR}/app.log` | `application/logging_config.py` (`mcp-ansible`) | 애플리케이션 일반 로그(오류/예외/운영 로그) |
| `${ANSIBLE_MCP_AUDIT_LOG_FILE}` 또는 `${ANSIBLE_MCP_LOG_DIR}/audit.log` | `api/tools/context.py`의 `audit_log()` | Tool 요청/결과/오류 감사 이벤트(JSON line) |
| `${LOG_DIR}/server.out.log`, `${LOG_DIR}/server.err.log` (기본 `/var/log/ansible-mcp`) | `scripts/start.sh` (`nohup` 리다이렉션) | 프로세스 표준출력/표준에러(Uvicorn 기동 메시지, 런타임 stderr) |

실행 산출물(artifact):

| 경로 | 내용 |
| --- | --- |
| `${ANSIBLE_MCP_RUNS_DIR}/{run_id}/...` (기본 `/var/lib/ansible-mcp/runs`) | `stdout`, `job_events`, `command`, `status` 등 ansible-runner 실행 상세 결과 |






