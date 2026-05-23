"""Dry-run mode: log mutations without executing them."""

import sys

_dry_run: bool = False

MUTATION_TOOLS = frozenset({
    "click", "double_click", "right_click", "drag",
    "type_text", "set_value", "press_key", "hotkey",
    "scroll", "move_cursor", "launch_app", "page",
    "set_config", "set_recording", "set_agent_cursor_enabled",
})

READ_ONLY_TOOLS = frozenset({
    "get_window_state", "screenshot", "zoom", "list_windows",
    "check_permissions", "list_apps", "get_cursor_position",
    "get_screen_size", "get_config", "get_recording_state",
    "get_agent_cursor_state", "replay_trajectory",
})


def set_dry_run(enabled: bool) -> None:
    global _dry_run
    _dry_run = enabled


def is_dry_run() -> bool:
    return _dry_run


def should_skip(tool: str) -> bool:
    if not _dry_run:
        return False
    return tool in MUTATION_TOOLS


def log_skipped(tool: str, kwargs: dict) -> dict:
    print(f"[dry-run] SKIP {tool}({kwargs})", file=sys.stderr)
    return {"success": True, "dry_run": True, "tool": tool, "args": kwargs}
