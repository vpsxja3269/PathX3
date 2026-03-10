from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from source.core.models import ToolSpec
from source.platform.common.runtime_paths import get_resource_paths


class ToolRegistry:
    def __init__(self, config_path: str | Path | None = None) -> None:
        default_path = Path(get_resource_paths()["tool_config"]) / "base.json"
        self.config_path = Path(config_path) if config_path else default_path

    def load(self) -> list[ToolSpec]:
        raw_items = json.loads(self.config_path.read_text(encoding="utf-8"))
        if not isinstance(raw_items, list):
            raise ValueError("Tool configuration root must be a list.")

        return [self._build_spec(raw_item) for raw_item in raw_items]

    def _build_spec(self, raw_item: dict[str, Any]) -> ToolSpec:
        return ToolSpec(
            id=str(raw_item["id"]),
            display_name=str(raw_item["display_name"]),
            description=str(raw_item.get("description", "")),
            executables=self._to_list(raw_item.get("executables")),
            version_args=self._to_list(raw_item.get("version_args", ["--version"])),
            candidate_paths=self._to_list(raw_item.get("candidate_paths")),
            path_hints=self._to_list(raw_item.get("path_hints")),
            notes=self._to_list(raw_item.get("notes")),
        )

    @staticmethod
    def _to_list(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        return [str(value)]
