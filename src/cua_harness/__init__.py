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

from cua_harness.client import (  # noqa: E402
    CuaClient,
    daemon_alive,
    ensure_daemon,
    get_client,
    kill_daemon,
)
from cua_harness.diff import StateCapture, ax_diff  # noqa: E402
from cua_harness.helpers import (  # noqa: E402
    app_info,
    check_permissions,
    click,
    double_click,
    drag,
    get_agent_cursor_state,
    get_config,
    get_cursor_position,
    get_recording_state,
    get_screen_size,
    get_window_state,
    hotkey,
    launch_app,
    list_apps,
    list_windows,
    load_app_skills,
    move_cursor,
    page,
    press_key,
    replay_macro,
    replay_trajectory,
    right_click,
    save_app_skill,
    screenshot,
    scroll,
    set_agent_cursor_enabled,
    set_config,
    set_recording,
    set_value,
    start_macro,
    stop_macro,
    type_text,
    zoom,
)
from cua_harness.profiler import Profiler  # noqa: E402
from cua_harness.session import (  # noqa: E402
    Session,
    get_profiler,
    get_session,
    is_dry_run,
    profile,
    set_default_session,
    set_dry_run,
)
from cua_harness.wait import wait_for  # noqa: E402

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
