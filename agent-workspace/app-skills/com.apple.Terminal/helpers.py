# reason: learned Terminal tab management, command execution, and explicit window_id state capture

import time
from cua_harness import get_window_state, hotkey, launch_app, list_windows, press_key, type_text


def _structured(result):
    """Return cua-driver structuredContent, falling back to the raw result."""
    return result.get("payload", {}).get("structuredContent", result)


def _first_window_id(result):
    sc = _structured(result)
    windows = sc.get("windows") or []
    if not windows:
        raise RuntimeError("Terminal has no enumerable windows")
    return windows[0]["window_id"]


def current_window_id(pid):
    """Terminal get_window_state requires an explicit window_id on this driver."""
    return _first_window_id(list_windows(pid))


def terminal_state(pid, capture_mode="som"):
    return get_window_state(pid, window_id=current_window_id(pid), capture_mode=capture_mode)


def new_tab(pid):
    hotkey(pid, ["command", "t"])
    time.sleep(0.5)


def run_command(pid, cmd):
    type_text(pid, cmd)
    press_key(pid, "Return")
    time.sleep(0.5)


def clear_screen(pid):
    hotkey(pid, ["command", "k"])
    time.sleep(0.2)


def launch_terminal():
    result = launch_app(bundle_id="com.apple.Terminal")
    sc = _structured(result)
    return sc["pid"]
