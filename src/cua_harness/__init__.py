"""cua-harness: agent-friendly Python SDK for cua-driver desktop automation."""

__version__ = "0.3.1"

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

from cua_harness.session import (  # noqa: E402
    Session, get_session, set_default_session,
    set_dry_run, is_dry_run, profile, get_profiler,
)
from cua_harness.client import ensure_daemon, daemon_alive, get_client, CuaClient, kill_daemon  # noqa: E402
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
    save_app_skill,
    load_app_skills,
    set_config,
    set_recording,
    set_agent_cursor_enabled,
    get_config,
    get_recording_state,
    get_agent_cursor_state,
    replay_trajectory,
    start_macro,
    stop_macro,
    replay_macro,
)
from cua_harness.wait import wait_for  # noqa: E402
from cua_harness.diff import ax_diff, StateCapture  # noqa: E402
from cua_harness.profiler import Profiler  # noqa: E402

__all__ = [
    "Session",
    "get_session",
    "set_default_session",
    "ensure_daemon",
    "daemon_alive",
    "kill_daemon",
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
    "save_app_skill",
    "load_app_skills",
    "set_config",
    "set_recording",
    "set_agent_cursor_enabled",
    "get_config",
    "get_recording_state",
    "get_agent_cursor_state",
    "replay_trajectory",
    "start_macro",
    "stop_macro",
    "replay_macro",
    "wait_for",
    "ax_diff",
    "StateCapture",
    "profile",
    "get_profiler",
    "Profiler",
    "set_dry_run",
    "is_dry_run",
]
