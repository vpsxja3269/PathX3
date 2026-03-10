from __future__ import annotations

import os
from typing import Sequence

from source.platform.common.subprocessx import CommandResult, run_process


class ToolValidator:
    def locate_on_path(self, executable_name: str, timeout: float = 3.0) -> list[str]:
        command = ["where", executable_name] if os.name == "nt" else ["which", executable_name]
        result = run_process(command, timeout=timeout)
        if result.return_code != 0 or result.timed_out:
            return []

        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def read_version(
        self, executable_path: str, version_args: Sequence[str] | None = None
    ) -> CommandResult:
        args = list(version_args or ["--version"])
        return run_process([executable_path, *args], timeout=5.0)
