from __future__ import annotations

import os

from source.core.models import FixAction, FixActionType, PathPosition
from source.platform.common.normalize import normalize_windows_path
from source.platform.win.env import WindowsPathSnapshot, read_windows_path_snapshot

try:  # pragma: no cover - depends on platform
    import winreg
except ImportError:  # pragma: no cover - non-Windows fallback
    winreg = None


USER_ENVIRONMENT_KEY = r"Environment"


class UserPathManager:
    def read_snapshot(self) -> WindowsPathSnapshot:
        return read_windows_path_snapshot()

    def write_user_entries(
        self,
        entries: list[str],
        system_entries: list[str] | None = None,
    ) -> None:
        if os.name != "nt" or winreg is None:
            raise RuntimeError("사용자 PATH 수정은 Windows에서만 지원됩니다.")

        normalized_entries = deduplicate_entries(entries)
        path_value = serialize_path_entries(normalized_entries)

        with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, USER_ENVIRONMENT_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, path_value)

        effective_system_entries = (
            system_entries if system_entries is not None else self.read_snapshot().system_entries
        )
        os.environ["PATH"] = serialize_path_entries(
            deduplicate_entries([*normalized_entries, *effective_system_entries])
        )


def apply_actions(entries: list[str], actions: list[FixAction]) -> tuple[list[str], list[str], bool]:
    working_entries = list(entries)
    messages: list[str] = []
    any_changed = False

    for action in actions:
        working_entries, changed = apply_action(working_entries, action)
        messages.append(describe_action(action, changed))
        any_changed = any_changed or changed

    return deduplicate_entries(working_entries), messages, any_changed


def apply_action(entries: list[str], action: FixAction) -> tuple[list[str], bool]:
    normalized_target = normalize_windows_path(action.directory)
    filtered_entries = [
        entry for entry in entries if normalize_windows_path(entry) != normalized_target
    ]
    changed = len(filtered_entries) != len(entries)

    if action.action_type == FixActionType.PATH_REMOVE:
        return filtered_entries, changed

    if action.action_type == FixActionType.PATH_ADD:
        if changed:
            return list(entries), False

        if action.position == PathPosition.FRONT:
            return [action.directory, *filtered_entries], True
        return [*filtered_entries, action.directory], True

    if action.action_type == FixActionType.PATH_MOVE:
        if action.position == PathPosition.FRONT:
            moved_entries = [action.directory, *filtered_entries]
            return moved_entries, moved_entries != entries

        moved_entries = [*filtered_entries, action.directory]
        return moved_entries, moved_entries != entries

    raise ValueError(f"Unsupported action type: {action.action_type}")


def serialize_path_entries(entries: list[str]) -> str:
    return os.pathsep.join(entries)


def deduplicate_entries(entries: list[str]) -> list[str]:
    unique_entries: list[str] = []
    seen: set[str] = set()

    for entry in entries:
        normalized = normalize_windows_path(entry)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique_entries.append(entry)

    return unique_entries


def describe_action(action: FixAction, changed: bool) -> str:
    if action.action_type == FixActionType.PATH_ADD:
        verb = "추가함" if changed else "추가 생략"
        position = "앞쪽" if action.position == PathPosition.FRONT else "뒤쪽"
        return f"사용자 PATH {position}에 {verb}: {action.directory}"

    if action.action_type == FixActionType.PATH_REMOVE:
        verb = "제거함" if changed else "제거 생략"
        return f"사용자 PATH에서 {verb}: {action.directory}"

    if action.action_type == FixActionType.PATH_MOVE:
        verb = "이동함" if changed else "이동 생략"
        position = "앞쪽" if action.position == PathPosition.FRONT else "뒤쪽"
        return f"사용자 PATH {position}으로 {verb}: {action.directory}"

    return f"지원하지 않는 작업입니다: {action.action_type}"
