from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Sequence


@dataclass(slots=True)
class CommandResult:
    command: list[str]
    return_code: int
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    error_message: str = ""


def run_process(
    command: Sequence[str], timeout: float = 5.0, cwd: str | None = None
) -> CommandResult:
    normalized_command = [str(part) for part in command]

    try:
        completed = subprocess.run(
            normalized_command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            cwd=cwd,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return CommandResult(
            command=normalized_command,
            return_code=-1,
            timed_out=True,
            error_message="Process timed out.",
        )
    except OSError as exc:
        return CommandResult(
            command=normalized_command,
            return_code=-1,
            error_message=str(exc),
        )

    return CommandResult(
        command=normalized_command,
        return_code=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )
