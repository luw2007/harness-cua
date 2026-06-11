"""Tool wrappers over cua-driver, delegating to Session."""

import atexit
import os
import tempfile
from pathlib import Path

from cua_harness.session import get_session

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AGENT_WORKSPACE = Path(os.environ.get("CUA_AGENT_WORKSPACE", REPO_ROOT / "agent-workspace")).expanduser()

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
    if screenshot_out:
        raw = get_session().call(tool, screenshot_out=screenshot_out, **kwargs)
    else:
        raw = get_session().call(tool, **kwargs)
    # Unwrap cua-driver envelope: {kind, payload: {structuredContent: {...}}}
    if isinstance(raw, dict):
        sc = raw.get("payload", {}).get("structuredContent") if isinstance(raw.get("payload"), dict) else None
        if isinstance(sc, dict):
            return sc
    return raw


def check_permissions(**kwargs) -> dict:
    return _cua("check_permissions", **kwargs)


def list_apps(**kwargs) -> dict:
    return _cua("list_apps", **kwargs)


def get_cursor_position(**kwargs) -> dict:
    return _cua("get_cursor_position", **kwargs)


def get_config(**kwargs) -> dict:
    return _cua("get_config", **kwargs)


def get_recording_state(**kwargs) -> dict:
    return _cua("get_recording_state", **kwargs)


def get_agent_cursor_state(**kwargs) -> dict:
    return _cua("get_agent_cursor_state", **kwargs)


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
    return _surface_app_skills(_cua("list_windows", pid=pid))


def _pick_window_id(pid: int) -> int | None:
    result = _cua("list_windows", pid=pid)
    windows = result.get("windows", [])
    visible = [w for w in windows if w.get("is_on_screen") and w.get("on_current_space")]
    if not visible:
        visible = [w for w in windows if w.get("on_current_space")]
    if not visible:
        visible = windows
    return visible[0]["window_id"] if visible else None


def get_window_state(
    pid: int,
    window_id: int | None = None,
    capture_mode: str = "som",
    query: str | None = None,
) -> dict:
    kwargs: dict = {"pid": pid, "capture_mode": capture_mode}
    if window_id is None:
        window_id = _pick_window_id(pid)
    if window_id is not None:
        kwargs["window_id"] = window_id
    if query is not None:
        kwargs["query"] = query
    needs_image = capture_mode in ("vision", "screenshot")
    out_file = _tmp_png() if needs_image else None
    result = _surface_app_skills(_cua("get_window_state", screenshot_out=out_file, **kwargs))
    if window_id is not None and "window_id" not in result:
        result["window_id"] = window_id
    return result


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


# --- Macro convenience (Python-level recording via Session) ---


def start_macro() -> None:
    get_session().start_recording()


def stop_macro(output_path: str | None = None) -> list[dict]:
    return get_session().stop_recording(output_path)


def replay_macro(path: str, speed: float = 1.0) -> list[dict]:
    return get_session().replay(path, speed)


# --- App skills surfacing and persistence ---


def _extract_bundle_id(result: dict) -> str | None:
    if isinstance(result, dict):
        return result.get("bundle_id")
    return None


def _surface_app_skills(result: dict) -> dict:
    bundle_id = _extract_bundle_id(result)
    if not bundle_id:
        return result
    skills_dir = AGENT_WORKSPACE / "app-skills" / bundle_id
    if not skills_dir.is_dir():
        return result
    helpers_file = skills_dir / "helpers.py"
    if helpers_file.exists():
        result["app_skills"] = str(helpers_file)
    return result


def load_app_skills(bundle_id: str, ns: dict) -> bool:
    """Load app-skills/<bundle_id>/helpers.py into the given namespace. Returns True if loaded."""
    import importlib.util
    skills_dir = AGENT_WORKSPACE / "app-skills" / bundle_id
    helpers_file = skills_dir / "helpers.py"
    if not helpers_file.exists():
        return False
    spec = importlib.util.spec_from_file_location(f"app_skills.{bundle_id}", helpers_file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for name in dir(mod):
        if not name.startswith("_"):
            attr = getattr(mod, name)
            if callable(attr):
                ns[name] = _wrap_with_fallback(attr, bundle_id, name)
            else:
                ns[name] = attr
    return True


def _wrap_with_fallback(fn, bundle_id, name):
    import functools

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            import sys
            print(f"[app-skill fallback] {bundle_id}.{name}() failed: {e}", file=sys.stderr)
            print("[app-skill fallback] skill may be outdated — consider re-recording", file=sys.stderr)
            return None
    return wrapper


def save_app_skill(bundle_id: str, code: str, reason: str = "") -> str:
    """Persist a learned app skill as Python code. Keeps one .prev.py backup."""
    header = ""
    if reason:
        # collapse newlines so a multi-line reason cannot inject code
        header = "# reason: " + reason.replace("\n", " ") + "\n"
    final_text = header + code

    try:
        compile(final_text, "<app-skill>", "exec")
    except SyntaxError as e:
        raise ValueError(f"invalid app-skill code: {e}") from e

    skills_dir = AGENT_WORKSPACE / "app-skills" / bundle_id
    skills_dir.mkdir(parents=True, exist_ok=True)
    helpers_file = skills_dir / "helpers.py"

    if helpers_file.exists():
        prev = skills_dir / "helpers.prev.py"
        prev.write_bytes(helpers_file.read_bytes())

    helpers_file.write_text(final_text)

    return str(helpers_file)


# Backward compat alias
app_info = list_apps  # type: ignore[name-defined]  # noqa: F821 — generated above
