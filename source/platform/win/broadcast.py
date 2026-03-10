from __future__ import annotations

import os
import ctypes
from ctypes import wintypes


HWND_BROADCAST = 0xFFFF
WM_SETTINGCHANGE = 0x001A
SMTO_ABORTIFHUNG = 0x0002


def broadcast_environment_change(timeout_ms: int = 3000) -> bool:
    if os.name != "nt":
        return False

    user32 = ctypes.windll.user32
    result = wintypes.DWORD()
    response = user32.SendMessageTimeoutW(
        HWND_BROADCAST,
        WM_SETTINGCHANGE,
        0,
        "Environment",
        SMTO_ABORTIFHUNG,
        timeout_ms,
        ctypes.byref(result),
    )
    return bool(response)
