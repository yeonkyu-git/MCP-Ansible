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

## 5. 빠른 시작
1. `.env` 준비
```bash
cp .env.example .env
```

2. 값 수정 (`.env`)
- `ANSIBLE_MCP_PLAYBOOK_ROOT`
- `ANSIBLE_MCP_INVENTORY_ROOT`
- `ANSIBLE_MCP_LOG_DIR` 또는 `ANSIBLE_MCP_LOG_FILE`/`ANSIBLE_MCP_AUDIT_LOG_FILE`

3. 서버 실행
```bash
./.venv/bin/python -m mcp_ansible.main
```

커스텀 env 파일 사용:
```bash
ANSIBLE_MCP_ENV_FILE=/etc/ansible-mcp/.env ./.venv/bin/python -m mcp_ansible.main
```

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
- `extra_vars`는 playbook `inputs` 스키마 기준으로 런타임 검증(필수값/타입/enum)됩니다.
- 정책 파일의 `path`는 환경변수 치환 지원
  - 예: `${ANSIBLE_MCP_PLAYBOOK_ROOT}/sudoers_manage.yml`

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

## 11. 오프라인 설치
1. 인터넷 환경에서 wheelhouse 생성
```bash
bash ./scripts/build_wheelhouse.sh
```

2. 폐쇄망 서버로 `mcp_ansible/`, `wheelhouse/` 복사

3. 폐쇄망 서버에서 설치
```bash
bash ./scripts/install_offline.sh
```
