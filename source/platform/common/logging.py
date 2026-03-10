from __future__ import annotations

from datetime import datetime
from pathlib import Path

from source.platform.common.runtime_paths import ensure_runtime_directories


def log_action(message: str) -> None:
    paths = ensure_runtime_directories()
    log_file = Path(paths["logs"]) / "application.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}] {message}\n")
