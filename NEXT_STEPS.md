# NEXT STEPS
기준일: 2026-02-25

## 현재 상태 요약
| 항목 | 상태 |
|---|---|
| MCP HTTP 서버 구조 | 완료 |
| Tool 모듈 분리(`api/tools`) | 완료 |
| allow-list 정책(`policy/*.yaml`) | 완료 |
| `.env` 기반 설정 로딩 | 완료 |
| 감사 로그 + runs 정리 | 완료 |

## 우선순위 작업
### P1. `extra_vars` 런타임 검증
- 위치: `api/tools/run_tools.py`
- 목표:
  - playbook `inputs` 기준 필수값/타입/enum 검증
  - 스키마 외 키 처리 정책 확정(허용/차단)
- 완료 기준:
  - 잘못된 입력 시 ansible 실행 전 명확한 에러 반환

### P1. 스모크 스크립트 정합성
- 위치: `scripts/smoke_mcp_local.sh`
- 이슈:
  - 기본 `INVENTORY_ID=prod_linux`
  - 실제 정책 기본 ID는 `linux`
- 완료 기준:
  - 기본값 통일 또는 문서에 명시적 override 안내

### P2. 배포 경로 표준화
- 대상:
  - `policy/registry_playbooks.yaml`
  - 실제 서버 배치 경로
- 목표:
  - `${ANSIBLE_MCP_PLAYBOOK_ROOT}` 기준 실제 파일 경로와 100% 일치
- 완료 기준:
  - check 실행 시 경로 관련 오류 없음

### P2. 테스트 추가
- 권장 범위:
  - `application/registry_loader.py`
  - `api/tools/run_tools.py`
  - `application/runner_wrapper.py`
- 완료 기준:
  - 핵심 경로(조회 -> schema -> check/apply) 회귀 검증 가능

### P3. 운영 문서 강화
- README 보강 항목:
  - 감사 로그 필드 예시
  - 장애 대응 절차(check/apply 분기)
  - log/runs 용량 관리 정책

## 운영 체크리스트
- [ ] `.env` 값 확인
- [ ] `policy/*.yaml`의 ID/경로 유효성 확인
- [ ] check 결과에서 `failed/unreachable` 확인
- [ ] apply 전 영향도 검토
- [ ] log/runs 디렉터리 용량 모니터링

## 다음 세션 시작 포인트
1. `extra_vars` 런타임 검증 구현
2. `smoke_mcp_local.sh` 기본 inventory 값 수정
