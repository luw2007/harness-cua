"""Python wrappers around cua-driver CLI."""

import json
import subprocess
import shutil
import tempfile
import time
from pathlib import Path


def _cua(tool: str, *, screenshot_out: str | None = None, **kwargs) -> dict:
    cmd = ["cua-driver", "call", tool]
    if kwargs:
        cmd.append(json.dumps(kwargs))
    cmd.append("--compact")
    if screenshot_out:
        cmd.extend(["--screenshot-out-file", screenshot_out])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        return {"success": False, "error": result.stderr.strip() or f"exit code {result.returncode}"}
    stdout = result.stdout.strip()
    if not stdout:
        out: dict = {"success": True}
        if screenshot_out and Path(screenshot_out).exists():
            out["image_path"] = screenshot_out
        return out
    try:
        parsed = json.loads(stdout)
        if screenshot_out and Path(screenshot_out).exists():
            parsed["image_path"] = screenshot_out
        return parsed
    except json.JSONDecodeError:
        out = {"success": True, "raw": stdout}
        if screenshot_out and Path(screenshot_out).exists():
            out["image_path"] = screenshot_out
        return out


def _tmp_png() -> str:
    fd, path = tempfile.mkstemp(suffix=".png", prefix="cua_")
    import os
    os.close(fd)
    return path


def daemon_alive() -> bool:
    if not shutil.which("cua-driver"):
        return False
    result = subprocess.run(
        ["cua-driver", "status"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    return result.returncode == 0


def ensure_daemon() -> None:
    if daemon_alive():
        return
    subprocess.Popen(
        ["cua-driver", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(20):
        time.sleep(0.25)
        if daemon_alive():
            return
    raise RuntimeError("Failed to start cua-driver daemon within 5s")


def check_permissions() -> dict:
    return _cua("check_permissions")


def launch_app(bundle_id: str, urls: list[str] | None = None) -> dict:
    kwargs: dict = {"bundle_id": bundle_id}
    if urls:
        kwargs["urls"] = urls
    return _cua("launch_app", **kwargs)


def list_windows(pid: int) -> dict:
    return _cua("list_windows", pid=pid)


def get_window_state(
    pid: int,
    window_id: int | None = None,
    capture_mode: str = "som",
) -> dict:
    kwargs: dict = {"pid": pid, "capture_mode": capture_mode}
    if window_id is not None:
        kwargs["window_id"] = window_id
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
    return _cua("click", **kwargs)


def double_click(
    pid: int,
    window_id: int | None = None,
    element_index: int | None = None,
) -> dict:
    kwargs: dict = {"pid": pid}
    if window_id is not None:
        kwargs["window_id"] = window_id
    if element_index is not None:
        kwargs["element_index"] = element_index
    return _cua("double_click", **kwargs)


def right_click(
    pid: int,
    window_id: int | None = None,
    element_index: int | None = None,
) -> dict:
    kwargs: dict = {"pid": pid}
    if window_id is not None:
        kwargs["window_id"] = window_id
    if element_index is not None:
        kwargs["element_index"] = element_index
    return _cua("right_click", **kwargs)


def drag(
    pid: int,
    from_x: float,
    from_y: float,
    to_x: float,
    to_y: float,
    window_id: int | None = None,
) -> dict:
    kwargs: dict = {"pid": pid, "from_x": from_x, "from_y": from_y, "to_x": to_x, "to_y": to_y}
    if window_id is not None:
        kwargs["window_id"] = window_id
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


def screenshot(pid: int, window_id: int | None = None) -> dict:
    kwargs: dict = {"pid": pid}
    if window_id is not None:
        kwargs["window_id"] = window_id
    out_file = _tmp_png()
    return _cua("screenshot", screenshot_out=out_file, **kwargs)


def move_cursor(x: float, y: float) -> dict:
    return _cua("move_cursor", x=x, y=y)


def get_cursor_position() -> dict:
    return _cua("get_cursor_position")


def get_screen_size() -> dict:
    return _cua("get_screen_size")


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


def app_info() -> dict:
    return _cua("list_apps")
