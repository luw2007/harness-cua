"""Declarative tool wrappers over cua-driver socket IPC."""

import atexit
import tempfile
import time
from pathlib import Path

from cua_harness.client import get_client

_tmp_files: list[str] = []


def _cleanup_tmp_files() -> None:
    import os
    for f in _tmp_files:
        try:
            os.unlink(f)
        except OSError:
            pass


atexit.register(_cleanup_tmp_files)


def _tmp_png() -> str:
    f = tempfile.NamedTemporaryFile(suffix=".png", prefix="cua_", delete=False)
    f.close()
    _tmp_files.append(f.name)
    return f.name


def _cua(tool: str, *, screenshot_out: str | None = None, **kwargs) -> dict:
    from cua_harness.dryrun import should_skip, log_skipped
    from cua_harness.macro import record_call
    from cua_harness.profiler import get_profiler

    if should_skip(tool):
        return log_skipped(tool, kwargs)

    if screenshot_out:
        kwargs["screenshot_out_file"] = screenshot_out

    t0 = time.monotonic()
    result = get_client().call(tool, kwargs if kwargs else None)
    elapsed_ms = (time.monotonic() - t0) * 1000

    get_profiler().record(tool, elapsed_ms)
    record_call(tool, kwargs, result)

    if screenshot_out and Path(screenshot_out).exists():
        result["image_path"] = screenshot_out
    return result


# --- Declarative tool definitions ---
# Each tuple: (func_name, tool_name, required_params, optional_params, needs_image)
# optional_params items: (param_name, default_value) or just param_name (default None)

_TOOL_DEFS: list[tuple] = [
    ("check_permissions", "check_permissions", [], [], False),
    ("list_apps", "list_apps", [], [], False),
    ("get_cursor_position", "get_cursor_position", [], [], False),
    ("get_config", "get_config", [], [], False),
    ("get_recording_state", "get_recording_state", [], [], False),
    ("get_agent_cursor_state", "get_agent_cursor_state", [], [], False),
]


def _make_simple_tool(tool_name: str):
    def tool_fn(**kwargs) -> dict:
        return _cua(tool_name, **kwargs)
    tool_fn.__name__ = tool_name
    return tool_fn


# Generate simple no-arg tools
for _name, _tool, _, _, _ in _TOOL_DEFS:
    globals()[_name] = _make_simple_tool(_tool)


# --- Complex tools with image capture or special signatures ---

def get_screen_size(display_id: int | None = None) -> dict:
    kwargs: dict = {}
    if display_id is not None:
        kwargs["display_id"] = display_id
    return _cua("get_screen_size", **kwargs)


def launch_app(
    bundle_id: str | None = None,
    name: str | None = None,
    urls: list[str] | None = None,
    electron_debugging_port: int | None = None,
) -> dict:
    if not bundle_id and not name:
        raise ValueError("launch_app requires bundle_id or name")
    kwargs: dict = {}
    if bundle_id:
        kwargs["bundle_id"] = bundle_id
    if name:
        kwargs["name"] = name
    if urls:
        kwargs["urls"] = urls
    if electron_debugging_port is not None:
        kwargs["electron_debugging_port"] = electron_debugging_port
    return _cua("launch_app", **kwargs)


def list_windows(pid: int) -> dict:
    return _cua("list_windows", pid=pid)


def get_window_state(
    pid: int,
    window_id: int | None = None,
    capture_mode: str = "som",
    query: str | None = None,
) -> dict:
    kwargs: dict = {"pid": pid, "capture_mode": capture_mode}
    if window_id is not None:
        kwargs["window_id"] = window_id
    if query is not None:
        kwargs["query"] = query
    needs_image = capture_mode in ("vision", "screenshot")
    out_file = _tmp_png() if needs_image else None
    return _cua("get_window_state", screenshot_out=out_file, **kwargs)


def click(
    pid: int,
    window_id: int | None = None,
    element_index: int | None = None,
    x: float | None = None,
    y: float | None = None,
    count: int = 1,
    action: str | None = None,
    modifier: list[str] | None = None,
    from_zoom: bool | None = None,
) -> dict:
    kwargs: dict = {"pid": pid, "count": count}
    if window_id is not None:
        kwargs["window_id"] = window_id
    if element_index is not None:
        kwargs["element_index"] = element_index
    if x is not None:
        kwargs["x"] = x
    if y is not None:
        kwargs["y"] = y
    if action is not None:
        kwargs["action"] = action
    if modifier is not None:
        kwargs["modifier"] = modifier
    if from_zoom is not None:
        kwargs["from_zoom"] = from_zoom
    return _cua("click", **kwargs)


def double_click(
    pid: int,
    window_id: int | None = None,
    element_index: int | None = None,
    x: float | None = None,
    y: float | None = None,
    modifier: list[str] | None = None,
    from_zoom: bool | None = None,
) -> dict:
    kwargs: dict = {"pid": pid}
    if window_id is not None:
        kwargs["window_id"] = window_id
    if element_index is not None:
        kwargs["element_index"] = element_index
    if x is not None:
        kwargs["x"] = x
    if y is not None:
        kwargs["y"] = y
    if modifier is not None:
        kwargs["modifier"] = modifier
    if from_zoom is not None:
        kwargs["from_zoom"] = from_zoom
    return _cua("double_click", **kwargs)


def right_click(
    pid: int,
    window_id: int | None = None,
    element_index: int | None = None,
    x: float | None = None,
    y: float | None = None,
    modifier: list[str] | None = None,
    from_zoom: bool | None = None,
) -> dict:
    kwargs: dict = {"pid": pid}
    if window_id is not None:
        kwargs["window_id"] = window_id
    if element_index is not None:
        kwargs["element_index"] = element_index
    if x is not None:
        kwargs["x"] = x
    if y is not None:
        kwargs["y"] = y
    if modifier is not None:
        kwargs["modifier"] = modifier
    if from_zoom is not None:
        kwargs["from_zoom"] = from_zoom
    return _cua("right_click", **kwargs)


def drag(
    pid: int,
    from_x: float,
    from_y: float,
    to_x: float,
    to_y: float,
    window_id: int | None = None,
    duration_ms: int | None = None,
) -> dict:
    kwargs: dict = {"pid": pid, "from_x": from_x, "from_y": from_y, "to_x": to_x, "to_y": to_y}
    if window_id is not None:
        kwargs["window_id"] = window_id
    if duration_ms is not None:
        kwargs["duration_ms"] = duration_ms
    return _cua("drag", **kwargs)


def type_text(
    pid: int,
    text: str,
    window_id: int | None = None,
    element_index: int | None = None,
    delay_ms: int | None = None,
) -> dict:
    kwargs: dict = {"pid": pid, "text": text}
    if window_id is not None:
        kwargs["window_id"] = window_id
    if element_index is not None:
        kwargs["element_index"] = element_index
    if delay_ms is not None:
        kwargs["delay_ms"] = delay_ms
    return _cua("type_text", **kwargs)


def set_value(pid: int, window_id: int, element_index: int, value: str) -> dict:
    return _cua("set_value", pid=pid, window_id=window_id, element_index=element_index, value=value)


def press_key(
    pid: int,
    key: str,
    window_id: int | None = None,
    element_index: int | None = None,
    modifiers: list[str] | None = None,
) -> dict:
    kwargs: dict = {"pid": pid, "key": key}
    if window_id is not None:
        kwargs["window_id"] = window_id
    if element_index is not None:
        kwargs["element_index"] = element_index
    if modifiers:
        kwargs["modifiers"] = modifiers
    return _cua("press_key", **kwargs)


def hotkey(pid: int, keys: list[str]) -> dict:
    return _cua("hotkey", pid=pid, keys=keys)


def scroll(
    pid: int,
    direction: str,
    amount: int = 3,
    by: str = "line",
    window_id: int | None = None,
    element_index: int | None = None,
) -> dict:
    kwargs: dict = {"pid": pid, "direction": direction, "amount": amount, "by": by}
    if window_id is not None:
        kwargs["window_id"] = window_id
    if element_index is not None:
        kwargs["element_index"] = element_index
    return _cua("scroll", **kwargs)


def screenshot(pid: int, window_id: int | None = None, format: str = "png") -> dict:
    kwargs: dict = {"pid": pid, "format": format}
    if window_id is not None:
        kwargs["window_id"] = window_id
    out_file = _tmp_png()
    return _cua("screenshot", screenshot_out=out_file, **kwargs)


def move_cursor(x: float, y: float) -> dict:
    return _cua("move_cursor", x=x, y=y)


def zoom(
    pid: int,
    x: float,
    y: float,
    width: float,
    height: float,
    window_id: int | None = None,
) -> dict:
    kwargs: dict = {"pid": pid, "x": x, "y": y, "width": width, "height": height}
    if window_id is not None:
        kwargs["window_id"] = window_id
    out_file = _tmp_png()
    return _cua("zoom", screenshot_out=out_file, **kwargs)


def page(
    pid: int,
    action: str,
    window_id: int | None = None,
    script: str | None = None,
    selector: str | None = None,
) -> dict:
    kwargs: dict = {"pid": pid, "action": action}
    if window_id is not None:
        kwargs["window_id"] = window_id
    if script is not None:
        kwargs["script"] = script
    if selector is not None:
        kwargs["selector"] = selector
    return _cua("page", **kwargs)


# --- New tools not in original harness ---

def set_config(key: str, value) -> dict:
    return _cua("set_config", key=key, value=value)


def set_recording(enabled: bool, output_dir: str | None = None) -> dict:
    kwargs: dict = {"enabled": enabled}
    if output_dir:
        kwargs["output_dir"] = output_dir
    return _cua("set_recording", **kwargs)


def set_agent_cursor_enabled(enabled: bool) -> dict:
    return _cua("set_agent_cursor_enabled", enabled=enabled)


def replay_trajectory(dir: str) -> dict:
    return _cua("replay_trajectory", dir=dir)


# Backward compat alias
app_info = list_apps  # type: ignore[name-defined]  # noqa: F821 — generated above
