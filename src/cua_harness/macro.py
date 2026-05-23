"""Record/replay macro mode for cua-harness actions."""

import json
import time
from pathlib import Path
from typing import Any

_recording: bool = False
_trajectory: list[dict] = []
_start_time: float = 0.0


def start_recording() -> None:
    global _recording, _trajectory, _start_time
    _trajectory = []
    _start_time = time.monotonic()
    _recording = True


def stop_recording(output_path: str | None = None) -> list[dict]:
    global _recording
    _recording = False
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(json.dumps(_trajectory, indent=2))
    return _trajectory


def is_recording() -> bool:
    return _recording


def record_call(tool: str, kwargs: dict, result: Any) -> None:
    if not _recording:
        return
    _trajectory.append({
        "t": round(time.monotonic() - _start_time, 3),
        "tool": tool,
        "args": kwargs,
        "result": result,
    })


def replay(path: str, speed: float = 1.0) -> list[dict]:
    from cua_harness.helpers import _cua

    trajectory = json.loads(Path(path).read_text())
    results = []
    prev_t = 0.0

    for step in trajectory:
        delay = (step["t"] - prev_t) / speed
        if delay > 0:
            time.sleep(delay)
        prev_t = step["t"]

        tool = step["tool"]
        args = step.get("args", {})
        result = _cua(tool, **args)
        results.append(result)

    return results
