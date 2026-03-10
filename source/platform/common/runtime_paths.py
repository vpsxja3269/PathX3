from __future__ import annotations

import os
import sys
from pathlib import Path


APP_NAME = "PathX3"


def get_source_root() -> Path:
    if getattr(sys, "frozen", False):
        bundle_root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        bundled_source = bundle_root / "source"
        return bundled_source if bundled_source.exists() else bundle_root

    return Path(__file__).resolve().parents[2]


def get_runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        local_app_data = Path(os.getenv("LOCALAPPDATA", str(Path.home())))
        return local_app_data / APP_NAME

    return get_source_root() / "data"


def get_resource_paths() -> dict[str, str]:
    source_root = get_source_root()
    runtime_root = get_runtime_root()

    return {
        "source_root": str(source_root),
        "data_root": str(runtime_root),
        "tool_config": str(source_root / "data" / "tool_config"),
        "logs": str(runtime_root / "logs"),
        "reports": str(runtime_root / "reports"),
        "snapshots": str(runtime_root / "snapshots"),
    }


def ensure_runtime_directories() -> dict[str, str]:
    paths = get_resource_paths()
    for key in ("data_root", "logs", "reports", "snapshots"):
        Path(paths[key]).mkdir(parents=True, exist_ok=True)
    return paths
