# NEXT STEPS
기준일: 2026-02-25

## 현재 상태
| 항목 | 상태 |
|---|---|
| MCP 서버 구조(api/application/domain/policy) | 완료 |
| Tool 분리 및 등록 구조(api/tools/register) | 완료 |
| Allow-list 기반 실행 제어 | 완료 |
| `.env` 기반 설정 로딩 | 완료 |
| 감사 로그 + runs 정리 로직 | 완료 |
| `extra_vars` 런타임 검증(필수/타입/enum/허용키) | 완료 |
| `log_grep_pattern` 안전 실행 방식(command/argv) | 완료 |
| `smoke_mcp_local.sh` 제거 | 완료 |

## 다음 우선 작업
### P1. 배포 경로 정합성 검증
- `${ANSIBLE_MCP_PLAYBOOK_ROOT}`, `${ANSIBLE_MCP_INVENTORY_ROOT}`가 실제 서버 경로와 일치하는지 점검
- 정책 파일(`policy/*.yaml`)의 모든 path가 실파일로 존재하는지 사전 체크

### P1. 입력 정책 고도화
- `extra_vars`의 unknown key 차단 정책 유지 여부 확정
- 필요 시 playbook별 예외 정책(선택 허용 키) 설계

### P2. 테스트 보강
- `application/registry_loader.py`: env path 확장/해석 테스트
- `api/tools/run_tools.py`: `extra_vars` 검증 테스트
- `application/runner_wrapper.py`: runs 보관 정리 테스트

### P2. 운영 문서 보강
- 감사 로그 샘플(JSON line) 추가
- 장애 대응 절차(check 실패 시 apply 금지) 상세화
- 로그/runs 용량 관리 가이드 추가
