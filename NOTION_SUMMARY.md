# Ansible을 통한 서버 관리 AI Agent 구성 - 진행 요약

## 1) 프로젝트 한 줄 요약
AI가 임의 명령을 직접 실행하지 않고, 등록된 Playbook/Inventory allow-list 기반으로 Ansible 작업을 안전하게 수행하는 MCP 서버를 구축했다.

## 2) 구현 완료 항목 (3단 표)
| 구분 | 완료 내용 | 기대 효과 |
|---|---|---|
| 아키텍처 | 디렉터리 구조를 `api/application/domain/policy`로 정리 | 코드 역할이 명확해지고 유지보수성 향상 |
| Tool 구성 | Tool 로직을 `catalog_tools`/`run_tools`로 분리 | 기능 확장 시 영향 범위 축소 |
| 조회 플로우 | `list_registered_playbooks`(요약) + `get_playbook_schema`(상세) | 토큰 절감, 탐색 효율 개선 |
| 정책 레이어 | Playbook/Inventory 레지스트리 allow-list 적용 | 임의 경로/임의 실행 위험 감소 |
| 실행 검증 | `extra_vars` 런타임 검증(필수/타입/enum/unknown key) | 오입력/오작동 사전 차단 |
| Inventory 가시성 | `list_inventory_hosts(inventory_id)` 추가 | 실제 제어 대상 서버 목록 즉시 확인 |
| 실행 결과 | `stdout`, `stdout_line_count`, `stdout_truncated` 응답 포함 | 사용자 입장에서 실행 결과 신뢰도 향상 |
| 로깅/감사 | app/audit 로그 분리 및 JSON line 감사 이벤트 기록 | 추적성/감사 대응 강화 |
| 환경설정 | `.env` 로드 + 경로 변수 치환 + `ANSIBLE_CONFIG` 고정 지원 | 환경별 배포 유연성 증가 |
| 운영 자동화 | `start.sh / stop.sh / status.sh` 운영 스크립트 구성 | 기동/중지/상태 관리 표준화 |
| 자원 관리 | run artifact 보관 개수 기반 자동 정리 | 디스크 누적 리스크 완화 |
| 배포 체계 | 폐쇄망 오프라인 설치 절차(wheelhouse, 트러블슈팅) 정리 | 배포 재현성 및 장애 대응력 향상 |

## 3) 현재 제공 Tool
- `list_registered_playbooks`
- `get_playbook_schema`
- `list_registered_inventories`
- `list_inventory_hosts`
- `run_playbook_check`
- `run_playbook_apply`

## 4) 현재 운영 포인트
- 실행 전: `get_playbook_schema`로 입력 스키마 확인
- 실행 시: `run_playbook_check` 우선, 필요 시 `run_playbook_apply`
- 결과 확인: 응답의 `stdout`/`host_summary`/`failures` 확인
- 경로 이슈 방지: `.env`에 `ANSIBLE_MCP_PLAYBOOK_ROOT`, `ANSIBLE_MCP_INVENTORY_ROOT`, `ANSIBLE_CONFIG` 고정

## 5) 다음 개선 후보
- 결과 본문 페이징/전체조회 전용 Tool 추가
- Inventory 파서 YAML 포맷 지원 확장
- 운영 대시보드(성공률/실패 유형/실행량) 지표화
