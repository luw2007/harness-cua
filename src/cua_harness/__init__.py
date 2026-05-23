"""cua-harness: agent-friendly Python SDK for cua-driver desktop automation."""

__version__ = "0.1.0"

USAGE = """\
Usage: cua-harness <<'PY'
  # Python code with pre-imported helpers
  state = get_window_state(pid)
  click(pid, element_index=3)
PY

Or as a library:
  from cua_harness import click, get_window_state, ensure_daemon
  ensure_daemon()
  state = get_window_state(pid)

Subcommands:
  --version   Print version
  --doctor    Check cua-driver availability and permissions
  --reload    Reload agent_helpers.py
"""

from cua_harness.client import ensure_daemon, daemon_alive, get_client, CuaClient  # noqa: E402
from cua_harness.helpers import (  # noqa: E402
    check_permissions,
    launch_app,
    list_windows,
    get_window_state,
    click,
    double_click,
    right_click,
    drag,
    type_text,
    set_value,
    press_key,
    hotkey,
    scroll,
    screenshot,
    move_cursor,
    get_cursor_position,
    get_screen_size,
    zoom,
    page,
    list_apps,
    app_info,
    set_config,
    set_recording,
    set_agent_cursor_enabled,
    get_config,
    get_recording_state,
    get_agent_cursor_state,
    replay_trajectory,
)

__all__ = [
    "ensure_daemon",
    "daemon_alive",
    "get_client",
    "CuaClient",
    "check_permissions",
    "launch_app",
    "list_windows",
    "get_window_state",
    "click",
    "double_click",
    "right_click",
    "drag",
    "type_text",
    "set_value",
    "press_key",
    "hotkey",
    "scroll",
    "screenshot",
    "move_cursor",
    "get_cursor_position",
    "get_screen_size",
    "zoom",
    "page",
    "list_apps",
    "app_info",
    "set_config",
    "set_recording",
    "set_agent_cursor_enabled",
    "get_config",
    "get_recording_state",
    "get_agent_cursor_state",
    "replay_trajectory",
]
