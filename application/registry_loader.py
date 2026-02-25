from __future__ import annotations

"""레지스트리 YAML 로더.

보안 목적상 사용자 입력으로 파일 경로를 직접 받지 않고,
미리 등록된 ID만 허용하기 위한 allow-list 레이어다.
"""

import os
from pathlib import Path
from typing import Any

import yaml


class RegistryError(ValueError):
    """레지스트리 형식/조회 오류를 나타내는 예외."""


class RegistryLoader:
    """playbook/inventory 레지스트리를 읽고 ID를 경로로 해석한다."""

    def __init__(self, playbook_registry_path: Path, inventory_registry_path: Path) -> None:
        """레지스트리 파일을 로드한다.

        Args:
            playbook_registry_path: `playbooks` 목록이 들어있는 YAML 경로.
            inventory_registry_path: `inventories` 목록이 들어있는 YAML 경로.
        """
        self.playbook_registry_path = playbook_registry_path
        self.inventory_registry_path = inventory_registry_path

        self._playbooks = self._load_playbook_registry(self.playbook_registry_path)
        self._inventories = self._load_inventory_registry(self.inventory_registry_path)

    @staticmethod
    def _load_yaml_list(path: Path, key: str) -> list[dict[str, Any]]:
        if not path.exists():
            raise RegistryError(f"registry file not found: {path}")

        payload: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        entries = payload.get(key)
        if not isinstance(entries, list):
            raise RegistryError(f"registry key '{key}' must be a list in {path}")

        out: list[dict[str, Any]] = []
        for item in entries:
            if not isinstance(item, dict):
                raise RegistryError(f"invalid registry entry in {path}: {item}")
            out.append(item)
        return out

    @staticmethod
    def _validate_inputs(inputs: Any, path: Path, item_id: str) -> list[dict[str, Any]]:
        if inputs is None:
            return []
        if not isinstance(inputs, list):
            raise RegistryError(f"playbook '{item_id}' inputs must be a list in {path}")

        normalized: list[dict[str, Any]] = []
        for entry in inputs:
            if not isinstance(entry, dict):
                raise RegistryError(f"playbook '{item_id}' has invalid input schema in {path}")

            name = entry.get("name")
            var_type = entry.get("type")
            required = entry.get("required", False)
            description = entry.get("description", "")
            default = entry.get("default")
            enum = entry.get("enum")

            if not isinstance(name, str) or not name:
                raise RegistryError(f"playbook '{item_id}' input name must be non-empty string in {path}")
            if not isinstance(var_type, str) or not var_type:
                raise RegistryError(f"playbook '{item_id}' input type must be non-empty string in {path}")
            if not isinstance(required, bool):
                raise RegistryError(f"playbook '{item_id}' input required must be bool in {path}")
            if not isinstance(description, str):
                raise RegistryError(f"playbook '{item_id}' input description must be string in {path}")
            if enum is not None and not isinstance(enum, list):
                raise RegistryError(f"playbook '{item_id}' input enum must be list in {path}")

            item: dict[str, Any] = {
                "name": name,
                "type": var_type,
                "required": required,
                "description": description,
            }
            if default is not None:
                item["default"] = default
            if enum is not None:
                item["enum"] = enum

            normalized.append(item)

        return normalized

    def _load_playbook_registry(self, path: Path) -> dict[str, dict[str, Any]]:
        """YAML 레지스트리를 읽어 `{id: metadata}` 사전으로 변환한다.

        metadata 형식:
            {
              "id": str,
              "path": str,
              "description": str,
              "inputs": list[dict]
            }
        """
        entries = self._load_yaml_list(path, "playbooks")

        out: dict[str, dict[str, Any]] = {}
        for item in entries:
            item_id = item.get("id")
            item_path = item.get("path")
            description = item.get("description", "")

            if not isinstance(item_id, str) or not isinstance(item_path, str):
                raise RegistryError(f"registry entries must have string id/path in {path}")
            if not isinstance(description, str):
                raise RegistryError(f"playbook '{item_id}' description must be string in {path}")

            inputs = self._validate_inputs(item.get("inputs"), path, item_id)

            # 동일 ID가 중복되면 마지막 값으로 덮어쓴다. 운영에서는 중복 금지를 권장한다.
            out[item_id] = {
                "id": item_id,
                "path": item_path,
                "description": description,
                "inputs": inputs,
            }

        return out

    def _load_inventory_registry(self, path: Path) -> dict[str, str]:
        """YAML 레지스트리를 읽어 `{id: path}` 사전으로 변환한다."""
        entries = self._load_yaml_list(path, "inventories")

        out: dict[str, str] = {}
        for item in entries:
            item_id = item.get("id")
            item_path = item.get("path")
            if not isinstance(item_id, str) or not isinstance(item_path, str):
                raise RegistryError(f"registry entries must have string id/path in {path}")
            out[item_id] = item_path

        return out

    @staticmethod
    def _expand_registry_path(raw_path: str) -> str:
        """레지스트리 경로 문자열의 환경변수를 확장한다.

        지원 예:
        - `$VAR`, `${VAR}` (POSIX 스타일)
        - `%VAR%` (Windows 스타일)
        """
        expanded = os.path.expandvars(raw_path)
        expanded = os.path.expanduser(expanded)
        return expanded

    def resolve_playbook(self, playbook_id: str) -> str:
        """playbook ID를 실제 파일 경로로 변환한다."""
        playbook = self._playbooks.get(playbook_id)
        if playbook is None:
            raise RegistryError(f"unknown playbook_id: {playbook_id}")
        return self._expand_registry_path(str(playbook["path"]))

    def resolve_inventory(self, inventory_id: str) -> str:
        """inventory ID를 실제 파일 경로로 변환한다."""
        if inventory_id not in self._inventories:
            raise RegistryError(f"unknown inventory_id: {inventory_id}")
        return self._expand_registry_path(self._inventories[inventory_id])

    def get_playbook(self, playbook_id: str) -> dict[str, Any]:
        """등록된 playbook 메타데이터를 반환한다."""
        playbook = self._playbooks.get(playbook_id)
        if playbook is None:
            raise RegistryError(f"unknown playbook_id: {playbook_id}")
        return dict(playbook)

    def list_playbooks(self) -> dict[str, dict[str, Any]]:
        """등록된 playbook 목록(ID -> metadata)을 반환한다."""
        return {item_id: dict(meta) for item_id, meta in self._playbooks.items()}

    def list_playbook_summaries(self) -> dict[str, dict[str, str]]:
        """등록된 playbook 요약 목록(ID -> {description})을 반환한다."""
        summaries: dict[str, dict[str, str]] = {}
        for item_id, meta in self._playbooks.items():
            summaries[item_id] = {"description": str(meta.get("description", ""))}
        return summaries

    def list_inventories(self) -> dict[str, str]:
        """등록된 inventory 목록(ID -> path)을 반환한다."""
        return dict(self._inventories)
