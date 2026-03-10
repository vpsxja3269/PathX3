from __future__ import annotations

from pathlib import Path
from typing import Iterable

from source.platform.common.normalize import normalize_windows_path


def unique_existing_paths(paths: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    resolved_paths: list[str] = []

    for raw_path in paths:
        if not raw_path:
            continue

        path = Path(raw_path)
        if not path.exists():
            continue

        normalized = normalize_windows_path(str(path))
        if normalized in seen:
            continue

        seen.add(normalized)
        resolved_paths.append(str(path.resolve()))

    return resolved_paths
