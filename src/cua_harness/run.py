"""Entry point: read stdin heredoc, ensure daemon, exec code."""

import sys
import importlib.util
from pathlib import Path

from cua_harness import __version__, USAGE
from cua_harness.helpers import (
    ensure_daemon,
    daemon_alive,
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
    app_info,
)


def _load_agent_helpers(ns: dict) -> None:
    workspace = Path.cwd() / "agent-workspace"
    helper_file = workspace / "agent_helpers.py"
    if not helper_file.exists():
        return
    spec = importlib.util.spec_from_file_location("agent_helpers", helper_file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for name in dir(mod):
        if not name.startswith("_"):
            ns[name] = getattr(mod, name)


def _doctor() -> None:
    print(f"cua-harness {__version__}")
    print()
    import subprocess
    try:
        result = subprocess.run(
            ["cua-driver", "doctor"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        print(result.stdout.strip() if result.stdout else result.stderr.strip())
    except subprocess.TimeoutExpired:
        print("cua-driver doctor timed out — daemon likely not running.")
        print("Start daemon with: cua-driver serve")
    except FileNotFoundError:
        print("cua-driver not found. Install: brew install anthropics/tap/cua-driver")


def main() -> None:
    args = sys.argv[1:]

    if "--version" in args:
        print(f"cua-harness {__version__}")
        return

    if "--doctor" in args:
        _doctor()
        return

    if "--help" in args or "-h" in args:
        print(USAGE)
        return

    if "--reload" in args:
        print("Reload: agent_helpers.py will be re-imported on next exec.")
        return

    if sys.stdin.isatty():
        print(USAGE, file=sys.stderr)
        sys.exit(1)

    code = sys.stdin.read()
    if not code.strip():
        return

    ensure_daemon()

    ns = {
        "__builtins__": __builtins__,
        "ensure_daemon": ensure_daemon,
        "daemon_alive": daemon_alive,
        "check_permissions": check_permissions,
        "launch_app": launch_app,
        "list_windows": list_windows,
        "get_window_state": get_window_state,
        "click": click,
        "double_click": double_click,
        "right_click": right_click,
        "drag": drag,
        "type_text": type_text,
        "set_value": set_value,
        "press_key": press_key,
        "hotkey": hotkey,
        "scroll": scroll,
        "screenshot": screenshot,
        "move_cursor": move_cursor,
        "get_cursor_position": get_cursor_position,
        "get_screen_size": get_screen_size,
        "zoom": zoom,
        "page": page,
        "app_info": app_info,
    }

    _load_agent_helpers(ns)
    exec(compile(code, "<stdin>", "exec"), ns)


if __name__ == "__main__":
    main()
