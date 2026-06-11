"""Session: single object holding client + profiler + recorder + dry_run."""

import json
import sys
import time
from contextlib import contextmanager
from pathlib import Path

from cua_harness.client import SOCKET_PATH, CuaClient
from cua_harness.profiler import Profiler, ToolStats  # noqa: F401

MUTATION_TOOLS = frozenset({
    "click", "double_click", "right_click", "drag",
    "type_text", "set_value", "press_key", "hotkey",
    "scroll", "move_cursor", "launch_app", "page",
    "set_config", "set_recording", "set_agent_cursor_enabled",
})


class Session:
    def __init__(self, socket_path: Path | str = SOCKET_PATH, dry_run: bool = False):
        self.client = CuaClient(socket_path)
        self.profiler = Profiler()
        self.dry_run = dry_run
        self._recording: bool = False
        self._trajectory: list[dict] = []
        self._rec_start: float = 0.0

    def call(self, tool: str, *, screenshot_out: str | None = None, **kwargs) -> dict:
        if self.dry_run and tool in MUTATION_TOOLS:
            print(f"[dry-run] SKIP {tool}({kwargs})", file=sys.stderr)
            return {"success": True, "dry_run": True, "tool": tool, "args": kwargs}

        if screenshot_out:
            kwargs["screenshot_out_file"] = screenshot_out

        t0 = time.monotonic()
        result = self.client.call(tool, kwargs if kwargs else None)
        elapsed_ms = (time.monotonic() - t0) * 1000

        self.profiler.record(tool, elapsed_ms)

        if self._recording:
            self._trajectory.append({
                "t": round(time.monotonic() - self._rec_start, 3),
                "timestamp": time.time(),
                "tool": tool,
                "args": kwargs,
                "result": result,
                "elapsed_ms": round(elapsed_ms, 1),
            })

        if screenshot_out and Path(screenshot_out).exists():
            result["image_path"] = screenshot_out
        return result

    def start_recording(self) -> None:
        self._trajectory = []
        self._rec_start = time.monotonic()
        self._recording = True

    def stop_recording(self, output_path: str | None = None) -> list[dict]:
        self._recording = False
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_text(json.dumps(self._trajectory, indent=2))
        return self._trajectory

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def trajectory(self) -> list[dict]:
        return self._trajectory

    def replay(self, path: str, speed: float = 1.0) -> list[dict]:
        trajectory = json.loads(Path(path).read_text())
        results = []
        prev_t = 0.0
        for step in trajectory:
            delay = (step["t"] - prev_t) / speed
            if delay > 0:
                time.sleep(delay)
            prev_t = step["t"]
            result = self.call(step["tool"], **step.get("args", {}))
            results.append(result)
        return results

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "Session":
        return self

    def __exit__(self, *_) -> None:
        self.close()


_default: Session | None = None


def get_session() -> Session:
    global _default
    if _default is None:
        _default = Session()
    return _default


def set_default_session(session: Session) -> None:
    global _default
    _default = session


def set_dry_run(enabled: bool) -> None:
    get_session().dry_run = enabled


def is_dry_run() -> bool:
    return get_session().dry_run


def get_profiler() -> Profiler:
    return get_session().profiler


@contextmanager
def profile():
    p = get_session().profiler
    p.start()
    try:
        yield p
    finally:
        p.stop()
        p.print_report()
