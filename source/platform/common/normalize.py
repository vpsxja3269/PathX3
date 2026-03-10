from __future__ import annotations

import os


def normalize_windows_path(path: str) -> str:
    if not path:
        return ""

    expanded = os.path.expandvars(path.strip().strip('"'))
    return os.path.normcase(os.path.normpath(expanded))
