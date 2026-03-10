from __future__ import annotations

import os
from dataclasses import dataclass, field

from source.platform.common.normalize import normalize_windows_path

try:  # pragma: no cover - import availability depends on platform
    import winreg
except ImportError:  # pragma: no cover - non-Windows fallback
    winreg = None


@dataclass(slots=True)
class WindowsPathSnapshot:
    user_entries: list[str] = field(default_factory=list)
    system_entries: list[str] = field(default_factory=list)
    process_entries: list[str] = field(default_factory=list)

    @property
    def combined_entries(self) -> list[str]:
        combined = self.user_entries + self.system_entries
        if not combined:
            combined = self.process_entries
        return _unique_entries(combined)


def read_windows_path_snapshot() -> WindowsPathSnapshot:
    process_entries = _split_path_value(os.environ.get("PATH", ""))

    if os.name != "nt" or winreg is None:
        return WindowsPathSnapshot(process_entries=process_entries)

    return WindowsPathSnapshot(
        user_entries=_split_path_value(_read_registry_path(winreg.HKEY_CURRENT_USER, r"Environment")),
        system_entries=_split_path_value(
            _read_registry_path(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
            )
        ),
        process_entries=process_entries,
    )


def _read_registry_path(root: int, sub_key: str) -> str:
    try:
        with winreg.OpenKey(root, sub_key) as registry_key:
            value, _ = winreg.QueryValueEx(registry_key, "Path")
            return str(value)
    except OSError:
        return ""


def _split_path_value(raw_value: str) -> list[str]:
    if not raw_value:
        return []

    entries = [entry.strip() for entry in raw_value.split(os.pathsep)]
    return [entry for entry in entries if entry]


def _unique_entries(entries: list[str]) -> list[str]:
    unique_entries: list[str] = []
    seen: set[str] = set()

    for entry in entries:
        normalized = normalize_windows_path(entry)
        if normalized in seen:
            continue
        seen.add(normalized)
        unique_entries.append(entry)

    return unique_entries
